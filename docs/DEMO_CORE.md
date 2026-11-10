# Guion de la demo · Core v0.5

**20 minutos de demo y 10 de preguntas** (rúbrica §2.4). Se muestra el flujo completo con dos roles, el aspirante y la coordinadora: inscripción con PDFs, link por email, enviar, revisar, observar, corregir, aprobar con número y email, y matricular (plan §14). Al final, el Excel, el período y el vencimiento (hito 3).

Todo corre en una sola máquina con `docker compose up --build`. Nada se muestra desde Swagger: es software andando (plan §1).

Cada bloque lo presenta quien hizo esa parte, porque el profe le puede preguntar a cualquiera por lo suyo (plan §16). El reparto de abajo es una propuesta: se confirma en el ensayo.

| # | Bloque | Min | Presenta | Maneja la máquina |
| --- | --- | --- | --- | --- |
| 0 | Apertura | 1 | Enzo | Enzo |
| 1 | El aspirante se inscribe | 4 | Gero y Fran | Gero |
| 2 | Seguimiento, PDFs y envío | 3 | Fran y Gero | Gero |
| 3 | La coordinadora revisa y observa | 4 | Loli y Luca | Loli |
| 4 | El aspirante corrige | 2 | Gero y Fran | Gero |
| 5 | Aprobar y matricular | 3 | Luca y Loli | Loli |
| 6 | Excel, período y vencimiento | 2 | Loli, Fran y Enzo | Loli y Enzo |
| 7 | Cierre: cómo sabemos que anda | 1 | Enzo | Enzo |

---

## Antes de empezar

**El día anterior:** un ensayo completo con cronómetro y, al terminar, `docker compose down -v` para dejar la base como el seed.

**El día de la demo, después de las 3:00** (a las 3:00 corre la tarea de vencimiento: si la base ya está levantada, vence el legajo que queremos vencer en vivo):

1. En la raíz del repo, con la rama que se entrega: `git switch main && git pull`.
2. Base nueva: `docker compose down -v && docker compose up --build`. Esperar a que `docker compose ps` muestre `db` y `backend` como `healthy`.
3. Los PDFs de la demo, en una carpeta fuera del repo (los arma el back con la misma función que el seed):

   ```bash
   mkdir -p ~/demo-pdfs
   for doc in FORM_INSCRIPCION DNI TITULO_GRADO PARTIDA CUIT_CUIL; do
     docker compose exec -T backend uv run python -c "import sys; from scripts.seed import _pdf_de_prueba; sys.stdout.buffer.write(_pdf_de_prueba('$doc'))" > ~/demo-pdfs/$doc.pdf
   done
   cp ~/demo-pdfs/PARTIDA.pdf ~/demo-pdfs/PARTIDA-legible.pdf
   echo "esto no es un PDF" > ~/demo-pdfs/foto.pdf
   ```

   Los mensajes "Bytecode compiled" que aparecen en la terminal son normales: no van a los archivos. `foto.pdf` es texto con extensión `.pdf`: sirve para mostrar que el back mira el contenido y no el nombre.
4. Pestañas abiertas en este orden: http://localhost:3000/inscripcion, http://localhost:8025 (MailHog) y http://localhost:3000/login. Una terminal abierta en la raíz del repo, para el bloque 6.
5. Zoom del navegador al 125 % y las notificaciones del sistema apagadas.

**Lo que NO hay que hacer antes de la demo:**
- **Correr el comando de vencimiento.** Si se corrió, Julieta Paz ya está VENCIDO: `docker compose down -v && docker compose up --build`.
- **Mandar más de 10 inscripciones en una hora desde la misma máquina.** El límite por IP (E7) responde 429. Si pasó, `docker compose restart backend` pone los contadores en cero.

## Datos de la demo

| Quién | Datos | Para qué |
| --- | --- | --- |
| Coordinadora | `admin@fenix.test` / `Admin1234!` (María González) | Bloques 3, 5 y 6 |
| Aspirante en vivo | Martina Ruiz (abajo, para copiar) | Bloques 1, 2 y 4 |
| Julieta Paz, del seed | COMPLETADO hace 31 días, legajo `26-001-004` | El vencimiento del bloque 6 |
| Roberto García, del seed | OBSERVADO | Plan B del bloque 4 |
| Lucía Martínez, del seed | PENDIENTE, beca del 100 % | Plan B del bloque 3 |

**El formulario de Martina:**

| Campo | Valor |
| --- | --- |
| Carrera | Maestría en Tecnología Informática |
| Apellido / Nombre | Ruiz / Martina |
| Nacionalidad | Argentina |
| DNI | 40.123.456 (con puntos: el back lo guarda sin ellos) |
| Teléfono móvil | +54 221 555 1234 |
| Email / alternativo | martina.ruiz@example.com / martina.trabajo@example.com |
| Domicilio / ciudad / provincia / país | Calle 50 Nro. 742 / La Plata / Buenos Aires / Argentina |
| Título de grado | Ingeniería en Sistemas de Información |
| Título de posgrado | (vacío) |
| ¿Cómo nos conociste? | Egresados |
| Motivación | Quiero especializarme en tecnología informática para liderar proyectos de transformación digital en mi trabajo. |
| Beca | No |

Si en el ensayo ya se usó a Martina y no se hizo `down -v`, el DNI da 409: usar a **Tomás Acosta**, DNI 41.234.567, `tomas.acosta@example.com`, con el resto igual.

---

## 0. Apertura · 1 min · Enzo

**Decir:** el sistema gestiona la inscripción a los posgrados de la UTN FRLP, desde que el aspirante completa el formulario hasta que queda matriculado. Son dos roles: el aspirante, que no tiene usuario y entra con un link que le llega por email, y la coordinadora de la Secretaría. Back en FastAPI con Clean Architecture, base PostgreSQL, front en React. Todo lo que van a ver se levantó con un solo `docker compose up --build`.

## 1. El aspirante se inscribe · 4 min · Gero y Fran

**Hacer (pestaña del formulario):**
1. Escribir un DNI corto (`123`): el error aparece al lado del campo antes de enviar (validación en tiempo real).
2. Completar el formulario de Martina y tocar "Guardar y continuar con la documentación".
3. Ver el aviso con el código de seguimiento (8 caracteres).
4. Pasar a MailHog: llegó "Tu preinscripción al Posgrado UTN FRLP", con el código y el botón "Continuar mi preinscripción". Abrir el botón.

**Decir:**
- Gero: el formulario valida lo mismo que el back (mismos mensajes), pero la regla de verdad está en el back: el front solo ayuda.
- Fran: `POST /legajos` crea el legajo en BORRADOR. El link lleva un token de 32 bytes que en la base se guarda solo como hash SHA-256 (ADR-005): si alguien lee la base, no puede entrar a ningún legajo. Vence a los 60 días.

**Tiene que verse:** el email en MailHog y, al abrir el link, "Mi preinscripción" en estado Borrador.

## 2. Seguimiento, PDFs y envío · 3 min · Fran y Gero

**Hacer (página de seguimiento):**
1. Mostrar la lista de documentos: Martina no pidió beca ni tiene título de posgrado, así que le piden 5. "Enviar a revisión" está deshabilitado y dice cuáles faltan.
2. En "DNI", subir `foto.pdf`: lo rechaza porque no es un PDF de verdad.
3. Subir los 5 PDFs de `~/demo-pdfs`, uno en cada documento.
4. "Enviar a revisión" se habilita. Tocarlo y confirmar en el modal.
5. MailHog: llegó "Recibimos tu preinscripción".

**Decir:**
- Fran: el back mira los primeros bytes del archivo, no la extensión, y acepta hasta 5 MB. Los guarda en un volumen que no sirve ninguna ruta, con nombre UUID y su SHA-256 (ADR-002): un PDF solo se baja con el link del aspirante o con sesión de coordinador. Antes de enviar, el back vuelve a controlar que estén todos.
- Gero: la página cambia según el estado: ahora está Pendiente y ya no deja editar.

**Tiene que verse:** el estado Pendiente y el email de confirmación.

## 3. La coordinadora revisa y observa · 4 min · Loli y Luca

**Hacer (pestaña del login):**
1. Entrar con `admin@fenix.test` / `Admin1234!`.
2. En el dashboard, mostrar las tarjetas del resumen (totales por estado y becas).
3. Buscar `ruiz` (parte del apellido) y después `40123456` (DNI exacto): aparece Martina, Pendiente, con 5 de 5 documentos.
4. Filtrar por estado "Pendiente" para mostrar los filtros, y volver a buscarla.
5. "Ver legajo": datos, carreras, documentación e historial. En "Documentación", tocar "Ver" en el DNI: el PDF se abre sin salir del legajo.
6. "Pasar a revisión": queda En revisión.
7. "Observar", con el comentario: `La partida de nacimiento no se lee bien. Subí una copia más clara.` Queda Observado.
8. MailHog: llegó "Tu legajo tiene observaciones", con el comentario.

**Decir:**
- Loli: el dashboard y el detalle piden los datos a la API. Los botones de acciones salen de lo que el back dice que se puede hacer en ese estado: el front no decide nada.
- Luca: el login devuelve un JWT de 8 horas (ADR-003). Cada endpoint del coordinador exige rol COORDINADOR: sin token da 401 y con otro rol, 403. Los cambios de estado pasan por la máquina de estados (ADR-004), que valida la transición, guarda la auditoría y manda el email. La regla vive en `domain/`, sin FastAPI ni SQL, y por eso se prueba sola.

**Tiene que verse:** el legajo Observado, el historial con REVISAR y OBSERVAR, y el email.

## 4. El aspirante corrige · 2 min · Gero y Fran

**Hacer (volver a la pestaña del seguimiento y recargar):**
1. Arriba, en amarillo, la observación de la coordinadora.
2. "Editar mis datos": agregar el teléfono fijo `0221 423 4567` y guardar.
3. En "Partida de nacimiento", subir `PARTIDA-legible.pdf`: reemplaza al anterior.
4. "Reenviar corrección" y confirmar. Vuelve a Pendiente.
5. MailHog: llegó la confirmación, que ahora dice que es una corrección.

**Decir:**
- Gero: el mismo formulario de la inscripción sirve para editar, y solo se puede en Borrador u Observado.
- Fran: el back sabe que es una corrección (CORREGIR y no ENVIAR) porque el legajo estaba Observado. Así queda en el historial y el email cambia.

**Plan B:** si algo de este bloque falla, se puede seguir con Roberto García, del seed, que ya está Observado: "¿Ya empezaste tu preinscripción?" en el formulario, con `roberto.garcia@empresa.com.ar`, y el link nuevo llega a MailHog.

## 5. Aprobar y matricular · 3 min · Luca y Loli

**Hacer (volver a la coordinadora y recargar el legajo de Martina):**
1. "Pasar a revisión" y después "Aprobar", y confirmar. Aparece el número de legajo **26-001-005** y queda Completado.
2. MailHog: llegó "Tu legajo fue aprobado", con el número y los 30 días para matricularse.
3. "Matricular" y confirmar: queda Activo.
4. Mostrar el historial completo: ENVIAR y CORREGIR del aspirante, y el resto de la coordinadora, con fecha y comentario.

**Decir:**
- Luca: el número es `AA-CCC-SSS`: año de la cohorte, número de cohorte y secuencial. Es el 005 porque el seed ya aprobó 4. Para que dos aprobaciones al mismo tiempo no repitan número, el back bloquea la fila de la cohorte (`SELECT … FOR UPDATE`) mientras lo calcula.
- Loli: el historial es la auditoría: cada cambio dice quién lo hizo, desde qué estado y con qué comentario.

**Tiene que verse:** el número 26-001-005, el email de aprobación y el estado Activo. Si en el ensayo se aprobó otro legajo sin `down -v`, el número es otro: decir el que aparezca.

## 6. Excel, período y vencimiento · 2 min · Loli, Fran y Enzo

**Hacer:**
1. Loli: en el dashboard, elegir "Con beca" en el filtro de beca y tocar "Exportar". Se baja `inscriptos-cohorte2026-AAAA-MM-DD.xlsx` con los mismos legajos que la tabla. Abrirlo.
2. Fran: con el interruptor "Período de inscripción", cerrar la inscripción con la próxima apertura `01/03/2027`. En la pestaña del formulario, recargar: avisa que está cerrada y desde cuándo abre. **Volver a abrirla.**
3. Enzo: en la terminal, correr la tarea de vencimiento a mano:

   ```bash
   docker compose exec backend uv run python -m src.legajos.infrastructure.job_vencimiento
   ```

   Imprime `Vencimiento: 1 de 1 legajos COMPLETADO pasaron a VENCIDO (26-001-004)`.
4. En el dashboard, buscar `paz`: Julieta Paz está Vencido, y en su historial VENCER lo hizo el SISTEMA. En MailHog llegó "Venció una reserva de vacante" a la coordinadora.

**Decir:**
- Fran: el período lo controla el back. Aunque alguien tenga el formulario abierto, con la inscripción cerrada `POST /legajos` responde 409.
- Enzo: un aprobado tiene 30 días para matricularse (BR-005). La tarea corre sola todos los días a las 3:00, dentro de la API (ADR-007), y se puede correr a mano como ahora. Julieta se aprobó hace 31 días.

## 7. Cierre: cómo sabemos que anda · 1 min · Enzo

**Decir:**
- Cada PR pasó por revisión y por el CI: ruff, migraciones, pytest con PostgreSQL 16, y lint y build del front. Sin el CI en verde no se puede mergear.
- Son más de 950 tests. Uno recorre por la API este mismo flujo de punta a punta (`test_flujo_completo.py`), y otro prueba los permisos de todos los endpoints (`test_permisos.py`).
- Seguridad: JWT con roles, token del aspirante hasheado y tapado en los logs, PDFs fuera de cualquier carpeta servida y validados por contenido, headers de seguridad, y hasta 10 inscripciones por hora por IP.
- La entrega es el tag `v0.5` en `main`.

---

## Si algo falla

| Pasa esto | Hacer |
| --- | --- |
| El formulario dice "Llegaste al límite de 10 envíos por hora" | `docker compose restart backend` (los contadores están en memoria) y recargar. |
| El DNI de Martina da "ya está inscripto" | Se ensayó sin `down -v`: usar a Tomás Acosta. |
| No llega un email | Recargar MailHog. Si sigue sin llegar: `docker compose logs backend --tail 30`. Para el link, "¿Ya empezaste tu preinscripción?" manda uno nuevo. |
| Julieta Paz ya aparece Vencido | La base estaba levantada a las 3:00 o se corrió el comando. Mostrar igual su historial (VENCER por SISTEMA) y contar cómo funciona. |
| La sesión de la coordinadora venció | Entrar de nuevo: el JWT dura 8 horas. |
| El front no carga o da errores de módulos | `docker compose up -d --build -V frontend`. |
| `docker compose up` dice que el puerto 5432 está ocupado | Hay otro Postgres corriendo: `docker ps` y frenarlo. |
| Se cae todo | `docker compose down -v && docker compose up --build` tarda unos 3 minutos. Mientras, se sigue con la guía con capturas (`docs/GUIA_USO.md`). |

## Preguntas probables

Cada uno tiene que poder explicar estas cuatro (plan §16) y su PR más importante.

| Pregunta | Idea de la respuesta |
| --- | --- |
| ¿Cuál es el flujo completo de un legajo? | BORRADOR → (ENVIAR) PENDIENTE → (REVISAR) EN_REVISION → (APROBAR) COMPLETADO → (MATRICULAR) ACTIVO. Desde EN_REVISION puede ir a OBSERVADO (y volver con CORREGIR) o a RECHAZADO. Un COMPLETADO sin matricular vence a los 30 días. |
| ¿Por qué la lógica va en `domain/` sin FastAPI ni SQL? | Porque la regla de negocio no depende de cómo llega el pedido ni de dónde se guarda: se prueba con tests rápidos sin base, y si mañana cambia el framework o la base, la regla no se toca. |
| ¿Cómo se protege un PDF? | Se valida por contenido y tamaño, se guarda fuera de cualquier carpeta servida con nombre UUID, y solo se baja por un endpoint que pide el link del aspirante (y solo de su legajo) o sesión de coordinador, sin caché. |
| ¿Cómo funciona el JWT? | El login valida la contraseña (bcrypt) y firma un token con el id y el rol, que vence a las 8 horas. El front lo manda en `Authorization: Bearer`, y cada endpoint protegido lo verifica y controla el rol. No hay refresh token: a las 8 horas se vuelve a entrar. |
