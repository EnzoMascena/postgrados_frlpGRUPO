# ADR-005: Acceso del aspirante con un link por email, con token aleatorio guardado como hash

**Estado:** Aceptado  
**Fecha:** 03/11/2026  
**Autor:** Francisco Buscaglia (rol: Desarrollador Backend)  
**Revisores:** Gero (PR F4), Enzo (revisión de arquitectura)

---

## Contexto

El aspirante no tiene usuario: completa el formulario una vez y después tiene que volver a su legajo para subir los PDFs, corregir lo que le observen y ver en qué estado está (US-CORE-001 a 004). Eso puede pasar a lo largo de varias semanas. Pedirle que cree una cuenta con contraseña agrega un paso que la mayoría no necesita, pero el acceso a su legajo no puede ser adivinable: tiene DNI, domicilio, teléfono y los PDFs de sus documentos (NFR-S02). El plan (PLAN_CORE §10) fija que entre con un link que recibe por email y que pueda pedir uno nuevo si lo pierde.

---

## Opciones Evaluadas

### Opción A: Token aleatorio por email, guardado como hash y con vencimiento
**Descripción:** al crear el borrador se genera un token aleatorio de 32 bytes y se manda por email el link `{FRONTEND_URL}/seguimiento/{token}`. En la base se guarda solo el SHA-256 del token, con su fecha de vencimiento. Si lo pierde, pide uno nuevo con su email.  
**Ventajas:** el aspirante no recuerda nada; el link no se puede adivinar; si alguien lee la tabla, no puede armar ningún link; cada token vence solo.  
**Desventajas:** quien tenga el email (o el link reenviado) entra al legajo; un link ya mandado no se puede volver a mostrar, porque no está guardado.

### Opción B: Usuario y contraseña para el aspirante
**Descripción:** el formulario crea una cuenta con contraseña y el aspirante inicia sesión como el coordinador.  
**Ventajas:** el mismo esquema que el coordinador (ADR-003); revocable cambiando la contraseña.  
**Desventajas:** suma alta de cuenta, recuperar contraseña (que igual termina en un link por email) y contraseñas que el aspirante olvida entre una visita y otra. Más trabajo y más fricción para algo que se usa pocas veces.

### Opción C: Entrar con el código de seguimiento (o con el id del legajo)
**Descripción:** el link lleva el código de 8 caracteres o el UUID del legajo.  
**Ventajas:** nada que guardar; el código ya existe.  
**Desventajas:** el código es corto (8 caracteres hexadecimales) y se dicta por teléfono: no es un secreto. El id aparece en las URLs del coordinador. Ninguno de los dos se puede revocar.

### Opción D: JWT firmado, sin tabla
**Descripción:** el link lleva un JWT con el id del legajo y su vencimiento, firmado con `JWT_SECRET`.  
**Ventajas:** no hace falta la tabla `tokens_seguimiento`.  
**Desventajas:** no se puede revocar uno solo antes de que venza, el link queda largo y cualquiera puede leer lo que lleva adentro. Cambiar `JWT_SECRET` invalidaría también todos los links de los aspirantes.

---

## Decisión

"Decidimos usar **la opción A: un token aleatorio de 32 bytes por email, guardado como SHA-256 y con vencimiento a los 60 días**, porque el aspirante no tiene que recordar nada y su legajo no queda expuesto aunque se filtre la base."

### Cómo queda

- **Generación:** `secrets.token_urlsafe(32)` (32 bytes al azar, unos 43 caracteres que van bien en una URL), en `crear_link_seguimiento(session, legajo_id)` de `src/inscripcion/infrastructure/links.py`.
- **Qué se guarda:** una fila en `tokens_seguimiento` con `legajo_id`, `token_hash` (SHA-256 en hexadecimal, único) y `expira_en`. El token en claro existe solo en el email y en la respuesta de `POST /legajos`.
- **Vencimiento:** `settings.token_seguimiento_dias` (60). Pasado ese plazo, el aspirante pide uno nuevo.
- **Cuándo se crea uno:** al crear el borrador (`POST /legajos`) y en cada `POST /legajos/recuperar-acceso`. Cada email lleva un token nuevo; los anteriores siguen sirviendo hasta que vencen.
- **Uso:** las rutas `/seguimiento/{token}` (F5 y F6) reciben el legajo con la dependencia `legajo_id_desde_token`, que hashea el token y lo busca. Un token que no existe y uno vencido dan el mismo 404 ("El link no es válido o venció. Pedí uno nuevo con tu email").
- **Recuperar acceso:** responde siempre 202 con el mismo mensaje, exista o no el email, y manda el link del legajo más reciente con ese email.

### Decisiones de implementación

1. **SHA-256 sin sal, y no bcrypt.** Una contraseña la elige una persona y se puede adivinar probando, por eso va con bcrypt (lento y con sal). El token tiene 256 bits al azar: no hay forma práctica de adivinarlo, así que un hash rápido alcanza. Además, sin sal el hash es siempre el mismo y se puede buscar directo por `token_hash` con su índice único; con bcrypt habría que recorrer y comparar todos los tokens.
2. **El token vuelve también en la respuesta de `POST /legajos`.** Así el front lleva al aspirante a su seguimiento en el momento, sin esperar el email. Si el SMTP falla, la inscripción no se deshace (`enviar_email` devuelve `False` y lo registra en el log) y el aspirante igual tiene su link.
3. **Los links viejos no se anulan al pedir uno nuevo.** Cada uno vence a los 60 días. Anularlos haría que un link que el aspirante tiene guardado deje de andar solo porque pidió otro desde otro dispositivo.
4. **Los emails se guardan en minúsculas.** Así `Ana@Mail.com` y `ana@mail.com` son el mismo email para la regla de "único en la cohorte" y para recuperar el acceso.
5. **El email de observación no lleva el link.** Como el token se guarda hasheado, después no se puede volver a armar. Ese email lleva `{FRONTEND_URL}/inscripcion?recuperar=1` para pedir uno nuevo (PLAN_CORE §11).

---

## Consecuencias

### Positivas
- El aspirante entra con un clic, sin cuenta ni contraseña.
- Leer la tabla `tokens_seguimiento` no alcanza para entrar a ningún legajo.
- Perder el link no es grave: se pide otro con el email.
- Los tests crean, usan y vencen tokens sin más piezas que la base.

### Negativas (trade-offs aceptados)
- Quien tenga acceso al email del aspirante, o a un link reenviado, entra a su legajo hasta que el link vence.
- Un link ya mandado no se puede volver a mostrar ni reenviar: hay que generar uno nuevo.
- Los tokens vencidos quedan en la tabla. Son filas chicas y no molestan; se pueden borrar más adelante con una tarea.

### Riesgos y Mitigaciones
| Riesgo | Mitigación |
|--------|-----------|
| Adivinar un link | 256 bits al azar con `secrets` (generador criptográfico) |
| Filtración de la base | Solo se guarda el SHA-256: con el hash no se arma el link |
| Link reenviado o email comprometido | Vence a los 60 días; desde el link solo se edita en BORRADOR u OBSERVADO; el coordinador revisa todo antes de aprobar |
| Averiguar quién se inscribió con recuperar acceso | Siempre 202 con el mismo mensaje. La respuesta tarda un poco más cuando manda el email; el límite de 10 pedidos por IP por hora (E7) hace caro probar en masa |
| Muchos pedidos de link para llenar la bandeja de alguien | Límite por IP de E7 (NFR-S06) |

---

## Revisión

Esta decisión será revisada en: la entrega final v1.0.  
Criterio de revisión: si el aspirante pasa a tener una cuenta (por ejemplo, para seguir la cursada después de matricularse), conviene evaluar la opción B y que el link de seguimiento quede solo para el preinscripto.
