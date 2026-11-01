# ADR-003: Sesión del coordinador con JWT de acceso, sin refresh token

**Estado:** Aceptado  
**Fecha:** 31/10/2026  
**Autor:** Luca De Paola (rol: Desarrollador Backend)  
**Revisores:** Loli (PR L1), Enzo (revisión de arquitectura)

---

## Contexto

En el Core solo el coordinador entra con usuario y contraseña; el aspirante usa el link de seguimiento (ADR-005). El front (React) y la API (FastAPI) corren separados y se hablan por JSON, así que la API tiene que saber en cada request quién llama y con qué rol (NFR-S01: todo endpoint que no sea público pide credenciales). Tenemos una semana para el Core y el plan deja afuera el refresh token, el logout en el back y el límite de intentos de login (PLAN_CORE §2). Las contraseñas van con bcrypt de costo 12 o más (NFR-S04) y los secretos solo en variables de entorno (NFR-M04).

---

## Opciones Evaluadas

### Opción A: JWT de acceso sin estado, sin refresh token
**Descripción:** al iniciar sesión, la API firma un JWT (HS256 con `JWT_SECRET`) que dura 8 horas. El front lo manda en `Authorization: Bearer …` y la API verifica la firma y el vencimiento. Cuando vence, se vuelve a iniciar sesión.  
**Ventajas:** no hace falta una tabla de sesiones ni limpiarla; es el esquema que vimos en la cátedra (módulo 04, PyJWT y pwdlib); se prueba fácil (un token se arma en el test); 8 horas cubren una jornada de trabajo.  
**Desventajas:** un token no se puede revocar antes de que venza; si alguien lo roba, sirve hasta el `exp`.

### Opción B: Sesiones guardadas en la base (cookie con id de sesión)
**Descripción:** al iniciar sesión se crea una fila en una tabla `sesiones` y el navegador guarda su id en una cookie `HttpOnly`. Cada request busca la sesión.  
**Ventajas:** se revoca borrando la fila (logout real); JavaScript no puede leer la cookie, así que un XSS no se la lleva.  
**Desventajas:** una tabla y una migración más, limpieza de sesiones vencidas, y protección contra CSRF por usar cookies. Con el front en otro origen hay que configurar `SameSite` y CORS con credenciales. Es más trabajo del que entra en la semana.

### Opción C: JWT de acceso corto con refresh token
**Descripción:** un token de acceso de 15 minutos más un refresh token de 7 días para renovarlo (lo que propone ARQUITECTURA §7.1).  
**Ventajas:** si roban el token de acceso, dura poco; el refresh se puede revocar.  
**Desventajas:** el refresh token tiene que guardarse y revocarse en la base (vuelve el estado de la opción B), y el front necesita renovar el token y reintentar el request. El plan lo dejó fuera del Core.

---

## Decisión

"Decidimos usar **la opción A: un JWT de acceso de 8 horas, sin refresh token ni logout en el back**, porque cubre lo que pide el Core con lo mínimo de piezas y es lo que el equipo ya conoce de la cátedra."

### Cómo queda

- **Token:** HS256 firmado con `settings.jwt_secret` (mínimo 32 caracteres, sin valor por defecto en el código), válido `settings.jwt_expira_minutos` (480). Claims: `sub` (id del usuario), `email`, `rol`, `iat` y `exp`. Al decodificar se fija el algoritmo (`algorithms=["HS256"]`, así no se acepta `alg: none`) y se exigen los cinco claims.
- **Login:** `POST /auth/login` devuelve `accessToken`, `tokenType`, `expiraEn` (segundos) y el usuario. Email inexistente, contraseña incorrecta o usuario inactivo dan siempre 401 con "Email o contraseña incorrectos", para no revelar cuál de las tres falló.
- **Contraseñas:** bcrypt de 12 rondas con pwdlib (`BcryptHasher(rounds=12)`).
- **Logout:** lo hace el front, borrando el token.
- **Dónde lo guarda el front:** en `localStorage` si el coordinador tilda "Recordarme" y en `sessionStorage` si no (PLAN_CORE §12, D1 de Loli).
- **Protección de endpoints:** `require_role(*roles)` en `src/autenticacion/presentation/dependencies.py`. Sin token, con un token inválido o vencido, o con un usuario que ya no existe o está inactivo → 401. Con otro rol → 403.

### Decisiones de implementación

1. **Hash de relleno cuando el email no existe.** Si el email no está registrado, igual se verifica la contraseña contra un hash bcrypt de 12 rondas de un valor aleatorio descartado (`HASH_DE_RELLENO` en `iniciar_sesion.py`). Con un usuario inactivo también se verifica la contraseña antes de rechazar. Sin esto, el email inexistente respondía en milisegundos y uno registrado en unos 250 ms: aunque el mensaje fuera el mismo, midiendo el tiempo se podía saber quién tiene usuario. El hash no es un secreto: no es la contraseña de nadie.
2. **El email del login es `str` y no `EmailStr`.** `email-validator` rechaza siempre los dominios reservados (RFC 2606), y el seed de la cátedra usa `admin@fenix.test`: con `EmailStr`, el coordinador del seed recibía 422 y no podía entrar. En el login no hace falta validar el formato: un email mal escrito no existe y da el mismo 401. `LoginRequest.email` queda con `min_length=1` y `max_length=255`. Los formularios del aspirante (Fran) siguen con `EmailStr`.
3. **Límite de 72 bytes de bcrypt.** bcrypt solo mira los primeros 72 bytes de la contraseña y, desde bcrypt 5.0, una más larga levanta `ValueError` (el login respondía 500, incluso con un email inexistente, al verificar contra el hash de relleno). Se cuentan bytes en UTF-8, no caracteres ("ñ" ocupa 2 bytes y un emoji 4), así que lo controla `hashing.py`:
   - `verificar_password` devuelve `False` sin llamar a bcrypt: esa clave nunca puede ser la correcta y el login da el 401 de siempre.
   - `hashear_password` levanta `ErrorDeValidacion` (422, campo `password`). No se corta en silencio: dos claves con los mismos primeros 72 bytes servirían igual.
   - Además, `LoginRequest.password` tiene `max_length=128` (caracteres), solo como tope barato contra bodies enormes.
4. **El usuario y su rol se leen de la base en cada request.** `get_current_user` busca al usuario por el `sub` del token y usa el rol de la base, no el del token. Si desactivan a un coordinador o le cambian el rol, su token deja de servir en el próximo request, sin esperar las 8 horas. Es una consulta por clave primaria por request, despreciable para nuestro volumen. Esto achica el principal riesgo de la opción A (no poder revocar): desactivar al usuario corta todos sus tokens.

### Diferencias con ARQUITECTURA §7

ARQUITECTURA §7 es la guía general de la cátedra; para el Core manda PLAN_CORE, que ya se acordó en el equipo:

| ARQUITECTURA §7 | Core (este ADR) | Por qué |
| --- | --- | --- |
| Login devuelve `access_token` (8 h) y `refresh_token` (7 d); existen `/auth/refresh` y `/auth/logout` | Solo el token de acceso de 8 h; sin refresh ni logout en el back | Fuera del alcance del Core (PLAN_CORE §2). 8 horas cubren la jornada del coordinador |
| `require_role` en `src/shared/auth/dependencies.py` | En `src/autenticacion/presentation/dependencies.py` | Screaming Architecture: el login es un módulo de negocio con sus cuatro capas. El nombre y el lugar están fijos en el plan §7 y en la regla B008 del `pyproject.toml` |
| `HTTPBearer()` y `HTTPException` con "Rol requerido: …" | `HTTPBearer(auto_error=False)` y los errores `NoAutenticado` / `SinPermiso` | Con `auto_error=True` FastAPI responde en inglés y con otro formato; así todo sale con el formato uniforme de §11.2. El mensaje del 403 no revela qué roles existen |
| El rol se lee del payload del token | El rol se lee de la base en cada request | Decisión 4 |

---

## Consecuencias

### Positivas
- No hay tabla de sesiones ni tarea para limpiarlas.
- Los tests arman tokens válidos, vencidos o mal firmados sin levantar nada más.
- Todos los errores de autenticación salen con el formato uniforme y en español.
- Desactivar un usuario lo saca del sistema al instante, aun sin logout en el back.

### Negativas (trade-offs aceptados)
- Un token robado sirve hasta 8 horas si el usuario sigue activo.
- El logout solo borra el token del navegador: si alguien lo copió antes, sigue sirviendo hasta el `exp`.
- El token en `localStorage` o `sessionStorage` lo puede leer cualquier JavaScript de la página, así que un XSS se lo llevaría (con una cookie `HttpOnly` no).
- Si cambia `JWT_SECRET`, se invalidan todos los tokens a la vez (todos vuelven a iniciar sesión).

### Riesgos y Mitigaciones
| Riesgo | Mitigación |
|--------|-----------|
| Robo del token por XSS | React escapa lo que muestra y no usamos `dangerouslySetInnerHTML`; vence a las 8 horas; desactivar al usuario corta el token (decisión 4) |
| Adivinar qué emails tienen usuario | Mismo mensaje y mismo tiempo de respuesta en los tres fallos (decisión 1) |
| Fuerza bruta sobre el login | bcrypt de 12 rondas hace lento cada intento. El límite de intentos queda fuera del Core (PLAN_CORE §2); el de E7 es solo para el formulario |
| Token falsificado o con `alg: none` | Firma HS256 con un secreto de 32 caracteres o más, algoritmo fijo al decodificar y claims obligatorios |
| Contraseña de más de 72 bytes rompe bcrypt (500) | Control en bytes en `hashing.py` (decisión 3) |

---

## Revisión

Esta decisión será revisada en: la entrega final v1.0, al sumar los roles Docente y CPR.  
Criterio de revisión: si entran más roles con login o datos más sensibles (tesis, notas), conviene evaluar la opción C (token corto con refresh revocable) o la opción B (cookie `HttpOnly`), y agregar un límite de intentos de login.
