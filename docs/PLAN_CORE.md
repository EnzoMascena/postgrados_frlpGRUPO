# Plan Core · Entrega martes 10/11

Oct 28, 2026 · @Enzo

El Nov 10, 2026 entregamos el Módulo Core andando de punta a punta: un aspirante se inscribe y sube sus PDFs desde el front, el coordinador lo revisa, lo observa o lo aprueba, y los emails llegan a MailHog. Hacemos solo los requisitos \[M\] del SRS, con un back nuevo en `backend/` y el front que ya tenemos (el del wireframe) conectado a la API. Este plan reemplaza a los dos planes de back anteriores; la copia que usa el código es `docs/PLAN_CORE.md` en el repo.

## 1. Qué entregamos

- **Fecha:** martes 10/11. El 11 cae miércoles: si la entrega es ese día, queda uno de colchón.
- **Terminado = software andando, no Swagger.** `docker compose up` desde cero levanta base, back, front y MailHog; el flujo aspirante → estudiante anda desde el front; el CI está en verde y existe `git tag v0.5` en `main`.
- **Criterios de corte de la rúbrica (si falla uno, la nota máxima es 4):**
  - `git tag v0.5` existe en el repo.
  - Un aspirante se inscribe completo (formulario + PDFs) sin errores.
  - El coordinador aprueba el legajo y el aspirante recibe el email.
  - Los tests pasan en el CI, no solo en la máquina de alguien.
- **Nota máxima 3 si:** no levanta con `docker compose up`, alguien tiene 0 commits, el CI falla en la entrega o hay contraseñas reales commiteadas.

## 2. Alcance

| Historia | Qué incluye | Back | Front |
| --- | --- | --- | --- |
| US-CORE-001 Formulario | Validación en tiempo real, DNI y email únicos en la cohorte, legajo en Borrador, link de seguimiento por email, recuperar el borrador con el email, hasta 10 envíos por IP por hora | Fran, Enzo (límite por IP) | Gero |
| US-CORE-002 Beca | 30% o 100%, formulario de beca obligatorio, visible para el coordinador | Fran | Gero |
| US-CORE-003 PDFs | Solo PDF real (magic bytes), máximo 5 MB, nombre UUID en disco, SHA-256, nada por URL directa, vista previa | Fran | Gero (subida), Loli (vista previa) |
| US-CORE-004 Documentos obligatorios | Cargado o Pendiente por documento, no deja enviar si falta uno, faltantes en rojo | Fran | Gero |
| US-CORE-005 Estados del legajo | Transiciones por rol, auditoría de cada cambio, número AÑO-COHORTE-SECUENCIAL al aprobar | Luca | Loli |
| US-CORE-006 Emails | Link de seguimiento, confirmación, observación, aprobación, rechazo y vencimiento, en HTML con logo UTN | Enzo (envío), Gero (plantillas), Fran y Luca (cuándo se mandan) | — |
| US-CORE-007 Búsqueda | DNI exacto, apellido parcial (3 letras o más), filtros por estado, cohorte, carrera y beca | Luca | Loli |
| US-CORE-008 Excel | Exporta la búsqueda actual con encabezados en negrita, columnas ajustadas y filtros | Luca | Loli |
| US-CORE-009 Período de inscripción | Abrir y cerrar por cohorte; con período cerrado, el formulario lo avisa | Fran | Loli (interruptor), Gero (aviso) |
| US-CORE-010 Vencimiento | 30 días en Completado sin matricular → Vencido, email al coordinador, tarea diaria | Enzo (tarea y comando), Luca (regla) | — |
| US-TECH-001 CI | Ruff, migraciones, tests con cobertura del 70% o más, lint y build del front | Fran | — |
| US-TECH-002 Docker | `docker compose up` levanta todo, migra y carga el seed | Enzo (base), Fran (servicios), Loli (seed) | — |
| US-TECH-003 Swagger | `/api/docs` con todos los endpoints, ejemplos y errores | Todos | — |
| US-TECH-004 Login (nueva) | JWT del coordinador, rutas protegidas por rol | Luca | Loli |
| US-TECH-005 Router y cliente de API (nueva) | Rutas, sesión, cliente HTTP con el formato de errores | — | Loli |

- **No entra:** refresh token, logout en el back (el front borra el token), límite de intentos de login, cola de emails con reintentos, módulos B, C y D (Legajo académico, Estadísticas y Planilla siguen con datos de prueba), semáforo, roles Docente y CPR.
- **Si nos atrasamos, se recorta en este orden:** 1) límite de 10 inscripciones por IP (NFR-S06), 2) editar los datos del borrador (el aspirante corrige subiendo PDFs), 3) búsqueda parcial por apellido (queda DNI exacto), 4) Excel. Nunca se recortan los criterios de corte de la sección 1.

## 3. Quién hace qué

Enzo, Fran y Luca se reparten el back en partes iguales: seis PRs de código cada uno. Fran y Luca escriben los módulos de negocio. Enzo deja la base, la base de datos y el envío de emails en los primeros días; después hace lo que cruza los módulos (la tarea de vencimiento, el límite por IP y la prueba del flujo completo), y además integra y entrega. Loli y Gero conectan el front y suman una parte chica de back.

| Persona | Rol (README) | Qué hace en el Core | Carga | PRs |
| --- | --- | --- | --- | --- |
| Fran | Desarrollador Backend | CI y Docker, período de inscripción, requisitos de documentos, inscripción del aspirante, PDFs, seguimiento y envío a revisión | Muy alta | 6 |
| Luca | Desarrollador Backend | Login con JWT, máquina de estados y regla de vencimiento, cambios de estado con auditoría y número, búsqueda, detalle, Excel, tests de permisos | Muy alta | 6 |
| Enzo | Líder / Desarrollador principal | Reinicio del repo, base del back, modelo de datos, envío de emails, tarea de vencimiento, límite por IP, prueba del flujo completo, revisión de arquitectura, guion de la demo y release | Muy alta | 10 (6 de código y 4 de docs) |
| Loli | Diseñadora / Frontend | Router, cliente de API y sesión, seed de la base, login, dashboard y detalle del legajo | Alta | 6 |
| Gero | Diseñador UI/UX / Frontend | Plantillas de los emails, formulario de inscripción, página de seguimiento del aspirante, guía de uso | Alta | 5 |

- **Duplas:** Fran y Gero hacen el flujo del aspirante (Fran el back, Gero el front); Luca y Loli, el del coordinador. Cada dupla se revisa los PRs, así quien consume la API la conoce. Lo de Enzo cruza los dos flujos: lo revisan Fran y Luca.
- **Roles que rotan:** además de su parte, cada uno hace de QA un día (prueba todo desde cero en su máquina) y la retro la escriben dos personas distintas (tabla de la sección 6). La rúbrica pide al menos dos roles por persona.

## 4. Cronograma y PRs

Enzo, Fran y Luca tienen PRs abiertos casi todos los días, seis de código cada uno; Enzo además abre y cierra la entrega. Cada PR tiene su rama, el día que se abre, el día que se mergea y quién lo revisa.

Se lee por carril: Enzo, Fran y Luca no dejan días libres del jueves 29 al sábado 7, Enzo además abre y cierra la entrega, y cada pantalla de Loli y Gero se mergea el mismo día que el endpoint que usa o después, nunca antes.

| PR | Rama | Qué incluye | Abre | Merge | Revisa |
| --- | --- | --- | --- | --- | --- |
| E1 | `docs/plan-core` | Este plan en `docs/PLAN_CORE.md` | Mié 28 | Mié 28 | Fran |
| E2 | `feature/US-TECH-002-base-backend` | Esqueleto de `backend/`, `shared/`, compose con base y MailHog, `.env.example`, fixtures de tests | Mié 28 | Jue 29 | Luca |
| E3 | `feature/US-TECH-002-modelo-de-datos` | Alembic, los 8 modelos, migración inicial, fábricas de tests, ADR-006 | Jue 29 | Vie 30 | Fran |
| E4 | `feature/US-CORE-006-envio-emails` | `enviar_email` con logo y bandeja de prueba | Vie 30 | Sáb 31 | Gero |
| E5 | `docs/readme-adr-001` | README (cómo levantar, URLs, usuario de prueba) y ADR-001 | Dom 1 | Lun 2 | Loli |
| E6 | `feature/US-CORE-010-vencimiento-reservas` | Tarea diaria a las 3:00, comando manual y ADR-007, con la regla y el `ServicioEstados` de Luca | Mié 4 | Jue 5 | Luca |
| E7 | `feature/US-CORE-001-limite-inscripciones` | Hasta 10 envíos por IP por hora en el formulario y en recuperar acceso (NFR-S06) | Jue 5 | Vie 6 | Fran |
| E8 | `test/flujo-completo` | Prueba por la API del flujo del hito 3, de la inscripción a la matrícula | Sáb 7 | Dom 8 | Fran |
| E9 | `docs/guion-demo` | Guion de la demo en `docs/DEMO_CORE.md` | Sáb 7 | Sáb 7 | Gero |
| E10 | `docs/changelog-v0.5` + PR `develop` → `main` | CHANGELOG v0.5.0, release y `git tag v0.5` | Lun 9 | Mar 10 | Luca |
| F1 | `feature/US-TECH-001-ci-docker` | CI nuevo, Dockerfiles, compose completo, `start.sh`, `.gitattributes` | Vie 30 | Sáb 31 | Luca |
| F2 | `feature/US-CORE-009-periodo-inscripcion` | `GET /cohortes`, `GET /carreras`, `PATCH /cohortes/{id}/inscripcion` | Sáb 31 | Dom 1 | Loli |
| F3 | `feature/US-CORE-004-requisitos-documentos` | Requisitos y checklist de documentos (dominio puro) | Sáb 31 | Dom 1 | Luca |
| F4 | `feature/US-CORE-001-inscripcion` | `POST /legajos`, beca, link de seguimiento, recuperar acceso, ADR-005 | Lun 2 | Mar 3 | Gero |
| F5 | `feature/US-CORE-003-documentos-pdf` | Subida, validación, almacenamiento y descargas de PDFs, `GET /seguimiento/{token}`, ADR-002 | Mié 4 | Jue 5 | Luca |
| F6 | `feature/US-CORE-001-seguimiento-envio` | `PUT /seguimiento/{token}`, enviar y corregir | Vie 6 | Sáb 7 | Gero |
| L1 | `feature/US-TECH-004-login-jwt` | Login, `/auth/me`, `require_role`, ADR-003 | Vie 30 | Sáb 31 | Loli |
| L2 | `feature/US-CORE-005-maquina-estados` | Estados, transiciones por rol, número de legajo y regla de vencimiento (dominio puro), ADR-004 | Sáb 31 | Dom 1 | Fran |
| L3 | `feature/US-CORE-005-cambio-estado` | `ServicioEstados`, `PATCH /legajos/{id}/estado`, `GET /legajos/{id}` (detalle), auditoría, emails | Lun 2 | Mar 3 | Loli |
| L4 | `feature/US-CORE-007-busqueda-legajos` | `GET /legajos` (búsqueda, filtros, páginas) y `GET /legajos/resumen` | Mié 4 | Jue 5 | Loli |
| L5 | `feature/US-CORE-008-exportar-excel` | `GET /legajos/exportar` | Vie 6 | Sáb 7 | Gero |
| L6 | `test/permisos-endpoints` | 401 sin token y 403 con otro rol en todos los endpoints protegidos | Dom 8 | Dom 8 | Enzo |
| D1 | `feature/US-TECH-005-router-api` | Router, layouts, cliente de API, sesión, tipos compartidos, Modal y Alerta | Vie 30 | Sáb 31 | Gero |
| D2 | `feature/US-TECH-002-seed` | `scripts/seed.py` idempotente | Sáb 31 | Dom 1 | Enzo |
| D3 | `feature/US-TECH-004-login-front` | Login conectado y rutas protegidas | Dom 1 | Dom 1 | Luca |
| D4 | `feature/US-CORE-007-dashboard` | Dashboard conectado: cohorte, período, resumen, tabla, búsqueda y filtros | Mié 4 | Jue 5 | Luca |
| D5 | `feature/US-CORE-005-detalle-legajo` | DetalleLegajo: datos, PDFs con vista previa, historial y acciones | Sáb 7 | Dom 8 | Luca |
| D6 | `feature/US-CORE-008-exportar-front` | Botón Exportar y PDFs de ejemplo en el seed | Sáb 7 | Dom 8 | Fran |
| G1 | `feature/US-CORE-006-plantillas-email` | Base y 6 plantillas HTML, logo, test de render | Vie 30 | Sáb 31 | Enzo |
| G2 | `feature/US-CORE-001-formulario-front` | Formulario conectado, validación en tiempo real, aviso de período cerrado, recuperar acceso | Lun 2 | Mar 3 | Fran |
| G3 | `feature/US-CORE-003-seguimiento-front` | Página de seguimiento y subida de PDFs | Jue 5 | Vie 6 | Fran |
| G4 | `feature/US-CORE-004-enviar-front` | Enviar, corregir, editar datos y vista por estado | Sáb 7 | Dom 8 | Fran |
| G5 | `docs/guia-de-uso` | Guía de uso del aspirante y del coordinador con capturas | Lun 9 | Lun 9 | Loli |
| R1 | `docs/retro-h1` | Retro del hito 1 en `docs/retros/` (Gero) | Dom 1 | Dom 1 | Loli |
| R2 | `docs/retro-final` | Retro final en `docs/retros/` (Luca) | Lun 9 | Lun 9 | Gero |

Cada uno tiene además su lista de tareas día por día. Si alguien arranca un día tarde, se corre su fila pero no el orden; lo que no se mueve son los hitos.

## 5. Hitos

1. **H0 · Mié 28 (noche):** `develop` reiniciada a la entrega del front, este plan en `develop` y todos con el entorno andando.
2. **H1 · Dom 1:** `docker compose up --build` levanta todo, migra y carga el seed; el coordinador entra desde el front; el CI está en verde y es obligatorio en `develop`. QA: Luca. Retro: Gero.
3. **H2 · Vie 6:** el aspirante completa el formulario desde el front, recibe el link en MailHog y sube sus PDFs; el coordinador ve el listado con búsqueda y filtros. QA: Gero.
4. **H3 · Dom 8, 23:59 (code freeze):** flujo completo desde el front: enviar → revisar → observar → corregir → aprobar (número y email) → matricular; abrir y cerrar el período; Excel; vencimiento con el comando manual. QA: Loli.
5. **H4 · Lun 9:** clon limpio en la máquina de Fran, `docker compose up` y la demo completa sin errores. Después del freeze entran solo arreglos. Retro final: Luca.
6. **H5 · Mar 10:** PR de `develop` a `main`, `git tag v0.5` y entrega.

## 6. Cómo trabajamos

Todo entra por PR a `develop` con una revisión, y en cada hito alguien prueba todo desde cero en su máquina.

### Paso 0 · Enzo, miércoles 28

`develop` vuelve a ser igual a `main` (la entrega del front) y se borra la rama del back viejo. El código viejo no se pierde: sigue en el PR #8 de GitHub.

```bash
git fetch origin --prune
git branch backup/back-viejo origin/develop      # copia local, no se pushea

# En GitHub: Settings → Branches → regla de develop → Edit → tildar "Allow force pushes" → Save
git push --force origin origin/main:refs/heads/develop
git push origin --delete feature/US-TECH-003-base-backend
# En GitHub: destildar "Allow force pushes". La regla queda: PR obligatorio + 1 aprobación.

git checkout develop && git reset --hard origin/develop
git log --oneline -1                             # tiene que mostrar 7a83909 (Merge pull request #7)
```

### Para todos, antes de arrancar

- **Que tus commits te cuenten:** `git config --global user.name "Nombre Apellido"` y `git config --global user.email` con un email verificado en tu cuenta de GitHub (github.com/settings/emails). Si el email no está ahí, tus commits no aparecen como tuyos y la rúbrica no los ve.
- **Actualizar `develop` después del paso 0:** `git fetch origin --prune`, `git checkout main`, `git branch -D develop` (si dice que no existe, seguí) y `git checkout develop`.
- **Herramientas:** Git, Node 22, npm, uv (Python 3.12 lo instala uv) y Docker Desktop andando.
- **Ritmo:** cada uno avanza por checkpoints chicos: termina una pieza, la prueba, la entiende y recién ahí la commitea. El push y el PR los hace cada uno desde su máquina.

### Reglas

- Una rama por PR (tabla de la sección 4), siempre desde `develop` actualizada.
- Commits chicos durante el día, con Conventional Commits en español: `feat(inscripcion): valida DNI único en la cohorte`. La rúbrica baja la nota si está todo junto al final.
- El PR usa el template de CONTRIBUTING: título `[US-CORE-001] …`, pasos reales en "Cómo probarlo" y una línea en `CHANGELOG.md` bajo `[Unreleased]`. Si el CHANGELOG choca al rebasear, se quedan las dos líneas.
- Quien revisa baja la rama, la prueba y deja al menos un comentario concreto (una pregunta o una mejora). Nada de "LGTM" vacío. Enzo hace además una revisión de arquitectura en todos los PRs de back.
- Se mergea con "Create a merge commit", no con squash.
- Un bloqueo se carga como issue de GitHub el mismo día y se avisa en el grupo.
- Daily en el grupo: "✅ Hice | 🔜 Haré | 🚧 Bloqueante".
- Nunca se commitean `.env` ni contraseñas reales. Las variables nuevas van a `.env.example` con un comentario.
- Cada uno toca sus carpetas (sección 7). Los únicos archivos compartidos son `backend/main.py` (una línea `include_router` por módulo), `backend/tests/conftest.py` (fixtures comunes), `CHANGELOG.md`, `.env.example` y `frontend/src/App.tsx` (rutas, de Loli). Si tocás uno, avisalo en el PR. La única excepción es E7: Enzo suma la dependencia del límite en las dos rutas públicas de Fran, y Fran lo revisa.

### QA y retros

| Hito | Prueba todo desde cero en su máquina | Escribe la retro en `docs/retros/` |
| --- | --- | --- |
| H1 · Dom 1 | Luca | Gero |
| H2 · Vie 6 | Gero | — |
| H3 · Dom 8 | Loli | — |
| H4 · Lun 9 | Fran | Luca |

## 7. Arquitectura del back

Cada carpeta de `backend/src/` es un módulo de negocio (Screaming Architecture) y adentro tiene las cuatro capas de Clean Architecture, como pide ARQUITECTURA §6.1.

```text
backend/
├── main.py                    # crea la app y registra los routers (Enzo; cada dueño suma su línea)
├── pyproject.toml, uv.lock    # dependencias con uv (Enzo)
├── alembic.ini, alembic/      # migraciones: la inicial es de Enzo; después, una por PR que cambie tablas
├── Dockerfile, start.sh       # (Fran)
├── scripts/seed.py            # datos de prueba (Loli)
├── src/
│   ├── shared/                # config, base, errores, headers, roles, esquemas, emails, límite por IP (Enzo)
│   │   └── email/templates/   # plantillas HTML (Gero)
│   ├── autenticacion/         # usuarios, login, JWT, require_role (Luca)
│   ├── cohortes/              # cohortes, carreras, período de inscripción (Fran)
│   ├── inscripcion/           # formulario, link de seguimiento, recuperar acceso, enviar (Fran)
│   ├── gestion_documental/    # requisitos, subida y descarga de PDFs (Fran)
│   └── legajos/               # estados, transiciones, auditoría, número, búsqueda, Excel (Luca); tarea de vencimiento (Enzo)
└── tests/                     # una carpeta por módulo, mismo dueño; conftest.py y flujo completo (Enzo)
```

Adentro de cada módulo:

- `domain/`: entidades, value objects, reglas y las interfaces de los repositorios. Solo biblioteca estándar y `src.shared.errors`/`src.shared.roles`: nada de FastAPI, SQLModel ni SQLAlchemy. Se testea sin base.
- `application/`: casos de uso que orquestan el dominio. Reciben los repositorios y el notificador por parámetro.
- `infrastructure/`: modelos ORM (`orm_models.py`), repositorios con SQLModel, disco, SMTP, Excel, tareas programadas.
- `presentation/`: router de FastAPI, schemas de Pydantic y las dependencias que arman los casos de uso.

Las flechas van hacia adentro (ARQUITECTURA §2.1): si un `domain/` importa FastAPI o SQLModel, el PR no se aprueba. Entre módulos se puede importar el `domain` o el `application` de otro; la `infrastructure` ajena solo se usa para armar dependencias o para leer y escribir sus tablas.

### Nombres fijos entre módulos

Lo que otros importan tiene nombre y firma fijos desde el principio. Si alguien necesita cambiarlo, lo avisa en el grupo antes.

| Qué | Dónde | Lo hace | Lo usan |
| --- | --- | --- | --- |
| `settings` (config por variables de entorno) | `src/shared/config.py` | Enzo (E2) | Todos |
| `get_session()` | `src/shared/database.py` | Enzo (E2) | Todos |
| `importar_modelos()` | `src/shared/database.py` | Enzo (E3) | Alembic, tests, seed |
| `ErrorDeNegocio`, `NoAutenticado`, `SinPermiso`, `NoEncontrado`, `Conflicto`, `ErrorDeValidacion` | `src/shared/errors.py` | Enzo (E2) | Todos |
| `CamelModel` | `src/shared/schemas.py` | Enzo (E2) | Todos los schemas |
| `Rol`, `Actor(rol, email)` | `src/shared/roles.py` | Enzo (E2) | Luca, Fran |
| `enviar_email(destinatario, asunto, plantilla, contexto) -> bool` y `BANDEJA_DE_PRUEBA` | `src/shared/email/sender.py` | Enzo (E4) | Fran, Luca |
| Enums `EstadoLegajo`, `TipoDocumento`, `TipoCarrera`, `ComoConocio`, `TipoBeca` | `domain/tipos.py` o `domain/estados.py` de cada módulo | Enzo (E3) | Todos |
| `limite_inscripciones`, `limite_recuperar_acceso` (dependencias de FastAPI) | `src/shared/limite.py` | Enzo (E7) | Fran (sus dos rutas públicas) |
| `hashear_password`, `verificar_password` | `src/autenticacion/infrastructure/hashing.py` | Luca (L1) | Loli (seed) |
| `get_current_user`, `require_role(*roles)`, `actor_desde_usuario` | `src/autenticacion/presentation/dependencies.py` | Luca (L1) | Fran, Luca |
| `Accion`, `validar_transicion(estado, accion, rol)`, `acciones_permitidas(estado, rol)`, `TransicionInvalida` | `src/legajos/domain/estados.py` | Luca (L2) | Fran, Loli (vía API) |
| `generar_numero_legajo(anio, numero_cohorte, secuencial)`, `reserva_vencida(fecha_aprobacion, ahora)` | `src/legajos/domain/numero_legajo.py` y `src/legajos/domain/vencimiento.py` | Luca (L2) | Luca, Enzo (E6) |
| `ServicioEstados.cambiar(legajo_id, accion, actor, comentario=None)` y `get_servicio_estados` | `src/legajos/application/cambiar_estado.py` y `src/legajos/presentation/dependencies.py` | Luca (L3) | Fran (enviar y corregir), Enzo (vencimiento) |
| `documentos_requeridos(solicita_beca, tiene_titulo_posgrado)`, `documentos_faltantes(...)`, `armar_checklist(...)` | `src/gestion_documental/domain/requisitos.py` | Fran (F3) | Luca (detalle y listado) |
| `guardar_pdf(contenido, cohorte_id, legajo_id) -> PdfGuardado` | `src/gestion_documental/infrastructure/almacenamiento.py` | Fran (F5) | Loli (seed con PDFs) |
| `crear_link_seguimiento(session, legajo_id) -> str`, `legajo_id_desde_token` (dependencia), `LegajoNoEditable` | `src/inscripcion/infrastructure/links.py`, `src/inscripcion/presentation/dependencies.py`, `src/inscripcion/domain/errores.py` | Fran (F4) | Fran (F5 y F6) |
| `obtener_detalle(legajo_id, repo, vista)`, `LegajoDetalleAspiranteResponse`, `LegajoDetalleCoordinadorResponse` | `src/legajos/application/obtener_detalle.py`, `src/legajos/presentation/schemas.py` | Luca (L3) | Fran (`GET /seguimiento/{token}` en F5) |

## 8. Modelo de datos

Enzo crea las 8 tablas en la migración inicial (E3), así desde el viernes todos programan contra tablas reales. Si después alguien necesita cambiar una tabla, lo hace con una migración nueva en su PR. Los modelos ORM viven en el `infrastructure/orm_models.py` del módulo indicado. Fechas en UTC (`timestamptz`), ids `UUID`.

| Tabla | Columnas | Restricciones | Módulo |
| --- | --- | --- | --- |
| `usuarios` | id, email, nombre, password\_hash, rol, activo, created\_at | email único; rol en (COORDINADOR, DOCENTE, CPR, ADMIN) | autenticacion |
| `carreras` | id, nombre, tipo, activa | nombre único; tipo en (Especializacion, Maestria, Doctorado) | cohortes |
| `cohortes` | id, anio, numero, nombre, inscripcion\_abierta, fecha\_inicio, proxima\_apertura, created\_at | nombre único; (anio, numero) único; numero entre 1 y 999 | cohortes |
| `legajos` | id, cohorte\_id, codigo\_seguimiento, numero\_legajo, estado, apellido, nombre, nacionalidad, dni, telefono\_movil, telefono\_fijo, email, email\_alternativo, domicilio, ciudad, provincia, pais, titulo\_grado, titulo\_posgrado, como\_conocio, motivacion, solicita\_beca, tipo\_beca, fecha\_inscripcion, fecha\_aprobacion, fecha\_activacion, created\_at, updated\_at | (cohorte\_id, dni) único; (cohorte\_id, email) único; codigo\_seguimiento y numero\_legajo únicos; estado en los 10 valores; motivación de 50 caracteres o más; tipo\_beca en (30, 100) y obligatorio solo si solicita\_beca | legajos |
| `legajo_carreras` | legajo\_id, orden, carrera\_id | PK (legajo\_id, orden); orden en (1, 2); (legajo\_id, carrera\_id) único. Así la base garantiza BR-001 | legajos |
| `tokens_seguimiento` | id, legajo\_id, token\_hash, expira\_en, created\_at | token\_hash (SHA-256) único; se guarda el hash, nunca el token | inscripcion |
| `documentos` | id, legajo\_id, tipo, path\_storage, nombre\_original, checksum\_sha256, tamanio\_bytes, fecha\_subida | (legajo\_id, tipo) único: subir otro del mismo tipo lo reemplaza; tipo en los 7 valores; tamaño entre 1 byte y 5 MB | gestion\_documental |
| `auditoria_legajos` | id, legajo\_id, accion, estado\_anterior, estado\_nuevo, comentario, rol, usuario\_email, created\_at | usuario\_email nulo si fue el sistema | legajos |

Índices: `legajos(dni)`, `legajos(email)`, `legajos(cohorte_id, estado)`, `documentos(legajo_id)`, `auditoria_legajos(legajo_id)`.

Valores de los enums:

- `estado`: BORRADOR, PENDIENTE, EN\_REVISION, OBSERVADO, COMPLETADO, ACTIVO, VENCIDO, RECHAZADO, BAJA, GRADUADO.
- `documentos.tipo`: FORM\_INSCRIPCION, DNI, TITULO\_GRADO, PARTIDA, CUIT\_CUIL, TITULO\_POSGRADO, FORM\_BECA.
- `como_conocio`: SITIO\_WEB\_UTN, OTROS\_SITIOS, EGRESADOS, COLEGAS, OTROS.

Las columnas de semáforo que trae ARQUITECTURA §8.1 quedan para el módulo especializado. BR-001 (hasta 2 carreras) se resuelve con `legajo_carreras` y lo documenta Enzo en ADR-006.

## 9. Máquina de estados

El legajo nace en BORRADOR cuando el aspirante guarda el formulario. Desde ahí, cada cambio pasa por `ServicioEstados.cambiar(...)`, que valida la transición con la tabla, aplica los efectos, guarda una fila de auditoría y manda el email que corresponda.

Las dos flechas en color son las únicas acciones del aspirante. Las demás las dispara el coordinador desde el detalle del legajo, salvo las punteadas: VENCER corre en la tarea diaria (o con el comando manual) y GRADUAR no se usa en el Core.

| Acción | De → a | Quién | Efectos | Email |
| --- | --- | --- | --- | --- |
| ENVIAR | BORRADOR → PENDIENTE | Aspirante | Antes se controlan los documentos obligatorios; guarda `fecha_inscripcion` | `confirmacion_envio` al aspirante |
| REVISAR | PENDIENTE → EN\_REVISION | Coordinador | — | — |
| OBSERVAR | EN\_REVISION → OBSERVADO | Coordinador | Comentario obligatorio | `observacion` al aspirante, con el comentario |
| CORREGIR | OBSERVADO → PENDIENTE | Aspirante | Antes se controlan los documentos obligatorios | `confirmacion_envio` (como corrección) |
| APROBAR | EN\_REVISION → COMPLETADO | Coordinador | Genera `numero_legajo` y guarda `fecha_aprobacion` | `aprobacion` al aspirante |
| RECHAZAR | EN\_REVISION → RECHAZADO | Coordinador | Comentario opcional | `rechazo` al aspirante |
| MATRICULAR | COMPLETADO → ACTIVO | Coordinador | Guarda `fecha_activacion` | — |
| VENCER | COMPLETADO → VENCIDO | Sistema (tarea diaria) | 30 días o más desde `fecha_aprobacion` (BR-005) | `vencimiento_coordinador` a cada coordinador activo |
| DAR\_DE\_BAJA | ACTIVO → BAJA | Coordinador | Comentario opcional | — |
| GRADUAR | ACTIVO → GRADUADO | Sistema | Queda en la tabla para el módulo C; en el Core no se dispara | — |

- **Número de legajo:** `AA-CCC-SSS`, con el año de la cohorte en dos dígitos, el número de cohorte y el secuencial dentro de la cohorte, empezando en 001. Ejemplo: `26-001-045`. El siguiente es el mayor secuencial ya usado en la cohorte más 1. Para que dos aprobaciones simultáneas no repitan número, el repositorio bloquea la fila de la cohorte (`SELECT … FOR UPDATE`) antes de calcularlo.
- **Código de seguimiento:** 8 caracteres hexadecimales en mayúscula (por ejemplo `7F3A9C21`). Se genera al crear el borrador y es el "número de seguimiento" que ve el aspirante.
- **Transición inválida:** una acción que no corresponde al estado (por ejemplo, APROBAR un legajo PENDIENTE) devuelve 409 `TRANSICION_INVALIDA`; una acción que no corresponde al rol (por ejemplo, el coordinador intentando ENVIAR) devuelve 403. En los dos casos no cambia nada.

## 10. Contrato de la API

Todos los endpoints llevan el prefijo `/api/v1`, hablan JSON en camelCase (los schemas heredan de `CamelModel`) y devuelven los errores en el formato de ARQUITECTURA §11.2. Swagger queda en `/api/docs`. El front y el back se programan contra esta sección: si hace falta cambiar algo, se avisa a la dupla antes de tocarlo.

### Acceso

- **Coordinador:** `Authorization: Bearer <accessToken>` (JWT HS256, 8 horas, claims `sub`, `email`, `rol`). Sin token o vencido → 401. Con otro rol → 403.
- **Aspirante:** no tiene usuario. Entra con el link de seguimiento que recibe por email: `/seguimiento/{token}`, con un token aleatorio de 32 bytes que en la base se guarda hasheado y vence a los 60 días (ADR-005). Cada email de link genera un token nuevo.
- **Públicos:** `POST /auth/login`, `GET /health`, `GET /cohortes`, `GET /carreras`, `POST /legajos` y `POST /legajos/recuperar-acceso`. Los tres del medio son públicos porque los necesita el formulario (NFR-S01).

### Formato de error

```json
{
  "statusCode": 409,
  "error": "CONFLICT",
  "message": "Ya existe una preinscripción con este DNI para la cohorte actual",
  "field": "dni",
  "timestamp": "2026-11-03T14:20:00Z"
}
```

| HTTP | `error` | Cuándo |
| --- | --- | --- |
| 401 | `UNAUTHORIZED` | Sin token, token inválido o vencido, login incorrecto |
| 403 | `FORBIDDEN` | El rol no tiene permiso |
| 404 | `NOT_FOUND` | No existe el recurso, o el link de seguimiento no es válido o venció |
| 409 | `CONFLICT` | DNI o email repetido en la cohorte |
| 409 | `PERIODO_CERRADO` | Inscripción en una cohorte con el período cerrado |
| 409 | `TRANSICION_INVALIDA` | La acción no corresponde al estado actual del legajo |
| 409 | `LEGAJO_NO_EDITABLE` | Editar o subir documentos fuera de BORRADOR u OBSERVADO |
| 422 | `VALIDATION_ERROR` | Un campo no cumple una regla (`field` dice cuál) |
| 422 | `DOCUMENTOS_FALTANTES` | Enviar sin todos los documentos obligatorios |
| 422 | `ARCHIVO_INVALIDO` | No es PDF, supera 5 MB o el tipo no corresponde |
| 429 | `RATE_LIMITED` | Más de 10 envíos por IP en una hora al formulario o a recuperar acceso (solo si entra E7) |
| 500 | `INTERNAL_ERROR` | Error inesperado, sin detalles internos |

Los mensajes son en español y orientados a la acción (NFR-U02), y `field` usa el nombre en camelCase del campo.

### Endpoints

| Método y ruta | Acceso | Dueño | Respuesta |
| --- | --- | --- | --- |
| `GET /health` | Público | Enzo | `{"status": "ok", "baseDeDatos": "ok"}` |
| `POST /auth/login` | Público | Luca | Token y usuario |
| `GET /auth/me` | Coordinador | Luca | Usuario |
| `GET /cohortes` | Público | Fran | Lista de cohortes |
| `PATCH /cohortes/{id}/inscripcion` | Coordinador | Fran | Cohorte actualizada |
| `GET /carreras` | Público | Fran | Lista de carreras activas |
| `POST /legajos` | Público | Fran | 201 con `legajoId`, `codigoSeguimiento`, `token`, `estado` |
| `POST /legajos/recuperar-acceso` | Público | Fran | 202 con mensaje genérico |
| `GET /seguimiento/{token}` | Aspirante | Fran | Detalle del legajo (vista aspirante) |
| `PUT /seguimiento/{token}` | Aspirante | Fran | Detalle actualizado |
| `POST /seguimiento/{token}/documentos` | Aspirante | Fran | 201 con el documento |
| `GET /seguimiento/{token}/documentos/{documentoId}/download` | Aspirante | Fran | PDF |
| `POST /seguimiento/{token}/enviar` | Aspirante | Fran | Detalle con estado PENDIENTE |
| `GET /legajos` | Coordinador | Luca | Página de legajos |
| `GET /legajos/resumen` | Coordinador | Luca | Conteos para las tarjetas del dashboard |
| `GET /legajos/exportar` | Coordinador | Luca | Archivo `.xlsx` |
| `GET /legajos/{id}` | Coordinador | Luca | Detalle (vista coordinador) |
| `PATCH /legajos/{id}/estado` | Coordinador | Luca | Detalle actualizado |
| `GET /documentos/{id}/download` | Coordinador | Fran | PDF |

En el router de Luca, `/legajos/resumen` y `/legajos/exportar` se declaran antes que `/legajos/{id}`.

### Login

`POST /auth/login`

```json
{ "email": "admin@fenix.test", "password": "Admin1234!" }
```

Respuesta 200 (401 con "Email o contraseña incorrectos" si falla, el mismo mensaje para email inexistente, clave incorrecta o usuario inactivo):

```json
{
  "accessToken": "eyJhbGciOi...",
  "tokenType": "bearer",
  "expiraEn": 28800,
  "usuario": { "id": "8c1e…", "email": "admin@fenix.test", "nombre": "María González", "rol": "COORDINADOR" }
}
```

### Cohortes y carreras

`GET /cohortes` (ordenadas por año, de la más nueva a la más vieja):

```json
[
  { "id": "c1a2…", "anio": 2026, "numero": 1, "nombre": "Cohorte 2026", "inscripcionAbierta": true, "fechaInicio": "2026-04-01", "proximaApertura": null }
]
```

`PATCH /cohortes/{id}/inscripcion` (BR-009). `proximaApertura` es opcional y no puede ser una fecha pasada:

```json
{ "abierta": false, "proximaApertura": "2027-03-01" }
```

`GET /carreras`:

```json
[ { "id": "5d2f…", "nombre": "Maestría en Tecnología Informática", "tipo": "Maestria" } ]
```

### Inscripción

`POST /legajos` crea el legajo en BORRADOR, genera el código y el token, y manda el email `link_seguimiento`.

```json
{
  "cohorteId": "c1a2…",
  "carreraIds": ["5d2f…"],
  "apellido": "Rodríguez",
  "nombre": "Ana Laura",
  "nacionalidad": "Argentina",
  "dni": "28456789",
  "telefonoMovil": "+54 221 4567890",
  "telefonoFijo": null,
  "email": "ana.rodriguez@example.com",
  "emailAlternativo": "ana.trabajo@example.com",
  "domicilio": "Av. 7 Nro. 1234",
  "ciudad": "La Plata",
  "provincia": "Buenos Aires",
  "pais": "Argentina",
  "tituloGrado": "Ingeniería en Sistemas de Información",
  "tituloPosgrado": null,
  "comoConocio": "EGRESADOS",
  "motivacion": "Quiero profundizar en gestión de sistemas para aplicarlo en mi trabajo como analista.",
  "solicitaBeca": true,
  "tipoBeca": "30"
}
```

Reglas: DNI de 7 u 8 dígitos (se le sacan puntos y espacios); email y email alternativo válidos; teléfono móvil obligatorio; motivación de 50 caracteres o más; `carreraIds` con 1 o 2 carreras distintas y activas (BR-001); `tipoBeca` obligatorio si `solicitaBeca` y nulo si no; `comoConocio` dentro de los valores; cohorte con el período abierto.

Respuesta 201:

```json
{ "legajoId": "4b0e…", "codigoSeguimiento": "7F3A9C21", "token": "Q3JxV…", "estado": "BORRADOR" }
```

Errores: 409 `PERIODO_CERRADO` ("La inscripción está cerrada. Próxima apertura: 01/03/2027", o sin fecha si no hay), 409 `CONFLICT` en `dni` ("Ya existe una preinscripción con este DNI para la cohorte actual") o en `email` ("Ya hay una preinscripción con este email. Si ya empezaste, pedí el link para continuar"), 422 `VALIDATION_ERROR`.

`POST /legajos/recuperar-acceso` con `{ "email": "…" }` siempre responde 202, exista o no el email, para no revelar quién se inscribió. Si hay un legajo con ese email, manda un link nuevo del más reciente.

```json
{ "mensaje": "Si hay una preinscripción con ese email, te enviamos un link para continuar." }
```

### Detalle del legajo

`GET /seguimiento/{token}` y `GET /legajos/{id}` devuelven el mismo cuerpo; el coordinador recibe además `historial` y `accionesPermitidas`, y el aspirante, `puedeEditar`.

```json
{
  "id": "4b0e…",
  "codigoSeguimiento": "7F3A9C21",
  "numeroLegajo": null,
  "estado": "EN_REVISION",
  "cohorte": { "id": "c1a2…", "nombre": "Cohorte 2026", "anio": 2026 },
  "carreras": [ { "id": "5d2f…", "nombre": "Maestría en Tecnología Informática", "tipo": "Maestria" } ],
  "apellido": "Rodríguez", "nombre": "Ana Laura", "nacionalidad": "Argentina", "dni": "28456789",
  "telefonoMovil": "+54 221 4567890", "telefonoFijo": null,
  "email": "ana.rodriguez@example.com", "emailAlternativo": "ana.trabajo@example.com",
  "domicilio": "Av. 7 Nro. 1234", "ciudad": "La Plata", "provincia": "Buenos Aires", "pais": "Argentina",
  "tituloGrado": "Ingeniería en Sistemas de Información", "tituloPosgrado": null,
  "comoConocio": "EGRESADOS", "motivacion": "…",
  "solicitaBeca": true, "tipoBeca": "30",
  "fechaInscripcion": "2026-11-03T14:20:00Z", "fechaAprobacion": null, "fechaActivacion": null,
  "createdAt": "2026-11-03T13:58:00Z",
  "documentos": [
    { "tipo": "DNI", "nombre": "Copia del DNI o pasaporte", "obligatorio": true, "cargado": true,
      "documentoId": "9f1c…", "nombreOriginal": "dni.pdf", "tamanioBytes": 183412, "fechaSubida": "2026-11-03T14:01:00Z" },
    { "tipo": "TITULO_GRADO", "nombre": "Copia del título de grado", "obligatorio": true, "cargado": false,
      "documentoId": null, "nombreOriginal": null, "tamanioBytes": null, "fechaSubida": null }
  ],
  "documentosFaltantes": ["TITULO_GRADO"],
  "ultimaObservacion": null,
  "historial": [
    { "fecha": "2026-11-03T14:20:00Z", "accion": "ENVIAR", "estadoAnterior": "BORRADOR", "estadoNuevo": "PENDIENTE",
      "comentario": null, "rol": "ASPIRANTE", "usuarioEmail": null }
  ],
  "accionesPermitidas": ["OBSERVAR", "APROBAR", "RECHAZAR"],
  "puedeEditar": false
}
```

- `documentos` lista solo los que le corresponden: los 5 obligatorios, más el título de posgrado si declaró uno y el formulario de beca si pidió beca (`documentos_requeridos`).
- `ultimaObservacion` es el comentario de la última acción OBSERVAR.
- `puedeEditar` es verdadero en BORRADOR y OBSERVADO.

`PUT /seguimiento/{token}` recibe el mismo cuerpo que `POST /legajos` sin `cohorteId`, aplica las mismas reglas (DNI y email únicos sin contar al propio legajo) y solo anda en BORRADOR u OBSERVADO; si no, 409 `LEGAJO_NO_EDITABLE`.

`POST /seguimiento/{token}/enviar` (sin cuerpo): si el legajo está en BORRADOR hace ENVIAR, si está en OBSERVADO hace CORREGIR. Si falta un documento obligatorio, responde 422 `DOCUMENTOS_FALTANTES` con el mensaje "Faltan documentos obligatorios: Copia del título de grado, …" y no cambia el estado.

### Documentos

`POST /seguimiento/{token}/documentos` es `multipart/form-data` con los campos `tipo` y `archivo`. Valida el tipo real por los primeros bytes (`%PDF-`), no por la extensión ni por el Content-Type, y el tamaño (5 MB). Guarda el archivo como `{STORAGE_PATH}/uploads/{cohorte_id}/{legajo_id}/{uuid}.pdf` con su SHA-256. Si ya había uno de ese tipo, lo reemplaza. Mensajes del SRS: "Solo se aceptan archivos en formato PDF" y "El archivo es demasiado grande. Máximo permitido: 5MB".

Respuesta 201:

```json
{ "documentoId": "9f1c…", "tipo": "DNI", "nombreOriginal": "dni.pdf", "tamanioBytes": 183412,
  "checksumSha256": "5e88…", "fechaSubida": "2026-11-03T14:01:00Z" }
```

Las dos descargas responden `application/pdf` con `Content-Disposition: inline`, `Cache-Control: no-store` y `X-Content-Type-Options: nosniff`. No existe ninguna URL que sirva el disco directamente.

### Búsqueda y estados (coordinador)

`GET /legajos?q=&estado=&cohorte=&carrera=&beca=&page=1&size=20`

- `q`: si son solo dígitos, busca DNI exacto; si no, apellido parcial sin distinguir mayúsculas, con 3 letras como mínimo (con menos, 422).
- `estado`, `cohorte` (id), `carrera` (id) y `beca` (`true` o `false`) se combinan. `page` empieza en 1 y `size` va de 1 a 100.
- Orden: los más nuevos primero.

```json
{
  "items": [
    { "id": "4b0e…", "codigoSeguimiento": "7F3A9C21", "numeroLegajo": null, "apellido": "Rodríguez", "nombre": "Ana Laura",
      "dni": "28456789", "email": "ana.rodriguez@example.com", "estado": "PENDIENTE", "cohorte": "Cohorte 2026",
      "carreras": ["Maestría en Tecnología Informática"], "solicitaBeca": true, "tipoBeca": "30",
      "documentosCargados": 6, "documentosRequeridos": 6, "fechaInscripcion": "2026-11-03T14:20:00Z" }
  ],
  "total": 1, "page": 1, "size": 20
}
```

`GET /legajos/resumen?cohorte=<id>` (la cohorte es opcional):

```json
{ "total": 13,
  "porEstado": { "BORRADOR": 1, "PENDIENTE": 3, "EN_REVISION": 2, "OBSERVADO": 1, "COMPLETADO": 2, "ACTIVO": 4,
                 "VENCIDO": 0, "RECHAZADO": 0, "BAJA": 0, "GRADUADO": 0 },
  "conBeca": 4, "beca30": 2, "beca100": 2 }
```

`GET /legajos/exportar` recibe los mismos filtros que el listado, sin paginar, y descarga `inscriptos-cohorte2026-2026-11-08.xlsx` (sin filtro de cohorte: `inscriptos-todas-2026-11-08.xlsx`). Columnas: Nº Legajo, Apellido y nombre, DNI, Estado, Carrera, Fecha inscripción.

`PATCH /legajos/{id}/estado`:

```json
{ "accion": "OBSERVAR", "comentario": "Falta la copia del título de grado legalizada" }
```

Responde el detalle actualizado. OBSERVAR sin comentario (o con menos de 5 caracteres) → 422; acción que no corresponde → 409 `TRANSICION_INVALIDA`; ENVIAR, CORREGIR, VENCER o GRADUAR desde el coordinador → 403.

## 11. Emails

`enviar_email` (Enzo) arma el HTML con Jinja2 desde `backend/src/shared/email/templates/`, adjunta el logo como imagen embebida con `cid:logo-utn` y lo manda por SMTP (MailHog en desarrollo, `http://localhost:8025`). Si el SMTP falla, lo registra en el log y devuelve `False`: el cambio de estado no se deshace por un email. En los tests no sale nada: los emails quedan en `BANDEJA_DE_PRUEBA`.

| Plantilla | Cuándo | A quién | Variables | Asunto | La dispara |
| --- | --- | --- | --- | --- | --- |
| `link_seguimiento.html` | Al crear el borrador y al recuperar acceso | Aspirante | `nombre`, `codigo_seguimiento`, `link` | Tu preinscripción al Posgrado UTN FRLP | Fran |
| `confirmacion_envio.html` | ENVIAR y CORREGIR | Aspirante | `nombre`, `codigo_seguimiento`, `carreras`, `cohorte`, `es_correccion` | Recibimos tu preinscripción | Luca |
| `observacion.html` | OBSERVAR | Aspirante | `nombre`, `comentario`, `link_recuperar` | Tu legajo tiene observaciones | Luca |
| `aprobacion.html` | APROBAR | Aspirante | `nombre`, `numero_legajo`, `carreras`, `fecha_limite` | Tu legajo fue aprobado | Luca |
| `rechazo.html` | RECHAZAR | Aspirante | `nombre`, `comentario` (puede ser vacío) | Resultado de tu preinscripción | Luca |
| `vencimiento_coordinador.html` | VENCER | Cada coordinador activo | `apellido`, `nombre`, `numero_legajo`, `fecha_aprobacion` | Venció una reserva de vacante | Luca |

- Todas extienden `base.html` (encabezado con el logo y los colores del wireframe: `#2C5F8A` y `#1E293B`).
- `link` es `{FRONTEND_URL}/seguimiento/{token}`; `link_recuperar` es `{FRONTEND_URL}/inscripcion?recuperar=1`, porque el token se guarda hasheado y después no se puede volver a armar el link.
- `carreras` es una lista de nombres; las fechas van como texto `dd/mm/aaaa`.
- Los nombres de plantilla y de variables no cambian sin avisar: Gero las escribe y Fran y Luca las usan.

## 12. Front

Partimos del front de la entrega 2, el que portamos del wireframe. No se rehace: se conecta a la API. Las pantallas nuevas (Seguimiento y DetalleLegajo) se arman con los mismos componentes (`Card`, `Badge`, `Button`, `Field`, `UploadBox`, `StatCard`, `Topbar`) y los tokens de `index.css`, así se ven como el wireframe en claro y oscuro.

### Rutas

| Ruta | Pantalla | Acceso | Dueño |
| --- | --- | --- | --- |
| `/` | Redirige a `/login` | Público | Loli |
| `/login` | Login | Público | Loli |
| `/inscripcion` | Formulario de inscripción | Público | Gero |
| `/seguimiento/:token` | Seguimiento del aspirante: estado, PDFs, enviar | Público con token | Gero |
| `/coordinador` | Dashboard | Coordinador | Loli |
| `/coordinador/legajos/:id` | DetalleLegajo | Coordinador | Loli |
| `/coordinador/legajo-academico` | Legajo académico (datos de prueba, módulo C) | Coordinador | — |
| `/coordinador/estadisticas` | Estadísticas (datos de prueba, módulo D) | Coordinador | — |
| `/coordinador/planilla` | Planilla docente (datos de prueba, módulo B) | Coordinador | — |
| `*` | No encontrado | Público | Loli |

### Piezas compartidas (Loli, D1)

- `react-router` (v8) con `BrowserRouter`, `Routes`, `Route`, `NavLink` y `Outlet`. Layout público y layout del coordinador con el `Sidebar`.
- `vite.config.ts`: `server.host = true` y proxy de `/api` a `process.env.VITE_PROXY_TARGET ?? 'http://localhost:8000'`. Así el front llama a `/api/v1/...` sin CORS, en local y en Docker. Con `VITE_USE_POLLING=true` (lo pone el compose) Vite vigila los archivos por sondeo, que es lo que hace falta en Docker sobre Windows.
- `src/shared/api/client.ts`: `apiFetch<T>(ruta, opciones)` le pone `/api/v1`, el token y el JSON; si la respuesta no es 2xx, tira `ApiError` con `status`, `codigo`, `mensaje` y `campo` (el formato de la sección 10). Ante un 401 con sesión, cierra la sesión y manda a `/login`. `apiDescargar(ruta)` devuelve el `Blob` y el nombre del archivo, para los PDFs y el Excel.
- `src/shared/api/tipos.ts`: los tipos del contrato (`EstadoLegajo`, `TipoDocumento`, `AccionLegajo`, `LegajoDetalle`, `ItemDocumento`, `Cohorte`, `Carrera`, `Paginado<T>`) y las etiquetas y colores de cada estado, documento y acción.
- `src/shared/auth/`: sesión en `localStorage` (con "Recordarme") o en `sessionStorage`, `AuthProvider`, `useAuth` y `RutaProtegida` (por rol).
- `src/shared/hooks/useCatalogos.ts`: `useCohortes()` y `useCarreras()`.
- `src/shared/components/`: `Modal`, `Alerta`, `EstadoBadge` y `Cargando`.
- TanStack Query: un hook por pantalla, claves `['cohortes']`, `['carreras']`, `['legajos', filtros]`, `['legajo', id]`, `['resumen', cohorteId]` y `['seguimiento', token]`; cada mutación invalida lo que cambia.

### Reglas del front

- Todo lo que viene de la API pasa por `apiFetch` y por un hook de TanStack Query; nada de `fetch` suelto en los componentes.
- Los mocks de Inscripción y Dashboard se borran cuando su pantalla queda conectada. Legajo académico, Estadísticas y Planilla siguen con mocks y en el menú dicen "(demo)".
- Errores en español, al lado del campo (`field` del error) o en una `Alerta`. Nunca un error en blanco ni solo en la consola.
- Responsive desde 375 px (NFR-U01) y labels asociados a cada input (`htmlFor` e `id`, NFR-U03).
- `npm run lint` sin warnings y `npm run build` sin errores antes de abrir el PR.

## 13. Tests, CI y Docker

- **Dominio:** tests unitarios sin base, en milisegundos (máquina de estados, número de legajo, vencimiento, requisitos, validación de PDF, reglas de inscripción).
- **Endpoints:** tests de integración con `TestClient` contra una base PostgreSQL de test (`postgrado_test`), que el `conftest.py` crea sola. Cada test corre en una transacción que se deshace al final, así ningún test ve los datos de otro.
- **Fixtures comunes** (`backend/tests/conftest.py`): `session`, `client`, `bandeja` (emails enviados) y las fábricas de `tests/fabricas.py` (`crear_cohorte`, `crear_carrera`, `crear_usuario`, `crear_legajo`). Luca suma `headers_coordinador` y `headers_docente` en L1.
- **De punta a punta:** `tests/test_flujo_completo.py` (Enzo, E8) recorre por la API el flujo del hito 3: inscripción, PDFs, enviar, revisar, observar, corregir, aprobar, matricular, un rechazo y el período cerrado. `tests/test_permisos.py` (Luca, L6) prueba 401 y 403 en todos los endpoints protegidos.
- **Cobertura:** 70% o más sobre `src/` (`fail_under = 70`); el CI la exige.
- **CI** (`.github/workflows/ci.yml`, Fran): en cada push y PR a `develop` y `main`. Job `backend`: Postgres 16 como servicio, `uv sync --locked`, `ruff check`, `ruff format --check`, `alembic upgrade head`, `alembic check` (falla si un modelo cambió sin migración) y `pytest --cov`. Job `frontend`: Node 22, `npm ci`, `npm run lint` y `npm run build`. Cuando entra, Enzo marca los dos jobs como obligatorios en `develop` y `main`.
- **Docker** (`docker-compose.yml`): `db` (postgres:16-alpine con healthcheck), `mailhog` (1025 y 8025), `backend` (8000; `start.sh` migra, carga el seed y levanta uvicorn) y `frontend` (3000, Vite con proxy a `http://backend:8000`). Volúmenes `pgdata` y `pdfs`. Anda sin `.env`, con valores por defecto de desarrollo.

| Comando | Para qué |
| --- | --- |
| `docker compose up --build` | Levantar todo (front en `localhost:3000`, API en `localhost:8000/api/docs`, MailHog en `localhost:8025`) |
| `docker compose down -v` | Bajar todo y borrar la base y los PDFs (para probar desde cero) |
| `docker compose up -d db mailhog` | Solo la base y MailHog, para correr el back o los tests en tu máquina |
| `cd backend && uv sync` | Instalar dependencias del back |
| `uv run uvicorn main:app --reload` | Correr el back en tu máquina |
| `uv run pytest --cov` | Tests con cobertura |
| `uv run ruff check . && uv run ruff format .` | Lint y formato |
| `uv run alembic upgrade head` | Aplicar migraciones |
| `uv run alembic revision --autogenerate -m "…"` | Nueva migración (revisarla a mano antes de commitear) |
| `uv run python -m scripts.seed` | Cargar los datos de prueba |
| `uv run python -m src.legajos.infrastructure.job_vencimiento` | Correr el vencimiento una vez (para la demo) |
| `cd frontend && npm ci && npm run dev` | Correr el front en tu máquina |

## 14. Terminado

Un PR está terminado cuando:

- Anda desde el front contra el back (o, si es solo back, desde Swagger y con su test de integración).
- Tiene tests, pasan, y la cobertura sigue en 70% o más.
- `ruff` y `npm run lint` no dan errores ni warnings, y el CI está en verde.
- Swagger muestra el endpoint con descripción, ejemplo y errores posibles.
- Lo revisó la persona de la tabla y lo probó en su máquina.
- Sumó su línea al CHANGELOG y, si hay variables nuevas, a `.env.example`.

Checklist del release (Enzo, lunes 9 y martes 10):

- [ ] Clon limpio + `docker compose up --build` en una máquina que no sea la de Enzo.
- [ ] Demo completa: inscripción con PDFs, link en MailHog, enviar, revisar, observar, corregir, aprobar con número y email, matricular.
- [ ] Sin token, los endpoints protegidos dan 401; con otro rol, 403. Ningún PDF se baja por URL directa.
- [ ] CI en verde en `develop`, con la prueba del flujo completo y la de permisos.
- [ ] CHANGELOG con la sección v0.5.0 y README con cómo levantar el proyecto.
- [ ] PR `develop` → `main` aprobado y mergeado, `git tag -a v0.5 -m "Core completo"` y `git push origin v0.5`.

## 15. Decisiones (ADRs)

Cada una va en `adr/` con el template `ADR-000-template.md`, en el mismo PR de la parte que decide. La opción de la tabla ya está decidida para no frenar a nadie; el ADR explica por qué.

| ADR | Decisión | Lo escribe |
| --- | --- | --- |
| ADR-001 | Stack: FastAPI + SQLModel/Alembic + PostgreSQL 16 + React 19, con uv y npm | Enzo (E5) |
| ADR-002 | PDFs en disco, en un volumen fuera de cualquier carpeta servida, nombre UUID, SHA-256 y tipo real por magic bytes | Fran (F5) |
| ADR-003 | Sesión con JWT de acceso de 8 horas, sin refresh token, guardado en el navegador | Luca (L1) |
| ADR-004 | Máquina de estados como tabla de transiciones por rol en `domain/`, más CHECK en la base y auditoría | Luca (L2) |
| ADR-005 | Acceso del aspirante con link por email: token de 32 bytes, guardado como SHA-256, vence a los 60 días | Fran (F4) |
| ADR-006 | BR-001: hasta 2 carreras por legajo en `legajo_carreras` con `orden` 1 o 2 | Enzo (E3) |
| ADR-007 | Tarea de vencimiento dentro del proceso de la API con APScheduler, más un comando para correrla a mano | Enzo (E6) |

## 16. Defensa

En la defensa el profe le puede preguntar a cualquiera por cualquier parte, y si alguien no conoce lo suyo, su nota individual puede bajar. Por eso:

- Nadie commitea algo que no puede explicar: antes de cada commit, cada uno tiene que poder contar qué hace ese código y responder dos preguntas como las del profe.
- En cada hito, cada uno muestra su parte al resto en 5 minutos.
- Antes del martes, cada uno tiene que poder explicar: el flujo completo de un legajo, por qué la lógica va en `domain/` sin FastAPI ni SQL, cómo se protege un PDF, cómo funciona el JWT, y qué hace su PR más importante.

## 17. Cómo arrancar hoy

1. Enzo hace el paso 0 y avisa en el grupo cuando `develop` está reiniciada y este plan está adentro.
2. Cada uno configura git con su email de GitHub y actualiza `develop` (sección 6).
3. Cada uno arranca por su checkpoint 0: dejar el entorno andando (Git, Node, uv, Docker) y leer este plan.
4. Dudas de alcance o de contrato: al grupo, antes de programar. Bloqueos: issue de GitHub el mismo día.
