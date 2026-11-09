# Changelog — Sistema de  Posgrado

Todos los cambios notables de este proyecto se documentan en este archivo.

Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).  
Este proyecto sigue [Versionado Semántico](https://semver.org/lang/es/).

---

## [Unreleased]

> Los cambios que están en `develop` pero no en un release van acá.

### Added
- Estructura inicial del repositorio
- Documentación base: SRS, PRD, BFD, Arquitectura, Cronograma
- Plan del Módulo Core con alcance, reparto, contrato de la API y modelo de datos
- Esqueleto del backend en FastAPI con Clean Architecture: configuración por variables de entorno, errores uniformes, headers de seguridad y health check
- Entorno de desarrollo con PostgreSQL 16 y MailHog en `docker-compose.yml`, y tests de integración con rollback por test
- Base del front para conectarse a la API: rutas con React Router y layouts público y del coordinador, cliente HTTP con el formato de errores del plan, sesión del coordinador con rutas protegidas por rol, catálogos de cohortes y carreras, y los componentes Modal, Alerta, EstadoBadge y Cargando
- Modelo de datos del Core (8 tablas con sus restricciones), migración inicial con Alembic, fábricas de datos para los tests y ADR-006 (carreras por legajo)
- Login del coordinador con JWT de 8 horas y contraseñas con bcrypt, y control de acceso por rol (`require_role`) para los endpoints protegidos (ADR-003)
- Plantillas HTML de los 6 emails del core (Jinja2, estilos en línea, logo como `cid:logo-utn`), con sus tests y un script de vista previa
- `docker compose up --build` levanta front, API, base y MailHog; el back migra y carga el seed al arrancar
- Requisitos de documentos del aspirante: qué corresponde según beca y título de posgrado, checklist de cargados y pendientes, y el error `DOCUMENTOS_FALTANTES` que frena el envío
- Envío de emails con `enviar_email`: arma el HTML desde las plantillas, embebe el logo de la UTN y lo manda por SMTP (MailHog en desarrollo), con una bandeja de prueba para los tests
- Período de inscripción por cohorte: `GET /cohortes` y `GET /carreras` públicos para el formulario, y `PATCH /cohortes/{id}/inscripcion` para que el coordinador abra o cierre la inscripción con la próxima apertura
- Máquina de estados del legajo: tabla de transiciones por rol con las acciones permitidas en cada estado, número de legajo `AA-CCC-SSS` y regla de vencimiento de la reserva a los 30 días (BR-005), documentada en el ADR-004
- Seed idempotente de datos de prueba (`uv run python -m scripts.seed`): 3 carreras, 3 cohortes, el coordinador con la clave de la configuración y 11 legajos con su historial, uno de ellos COMPLETADO hace 31 días para mostrar el vencimiento en la demo
- Login del coordinador conectado a la API: errores del back en pantalla, "Recordarme", aviso de sesión vencida, rutas del coordinador protegidas por rol y cierre de sesión
- README con cómo levantar el proyecto (URLs, usuario de prueba, comandos del día a día y problemas comunes en Windows), ADR-001 del stack y la forma de vincular un PR con su issue (`Closes #N`) en CONTRIBUTING
- Inscripción del aspirante: `POST /legajos` crea el legajo en BORRADOR con su código de seguimiento y manda por email el link para continuar, y `POST /legajos/recuperar-acceso` manda uno nuevo; el link lleva un token de 32 bytes guardado como SHA-256 que vence a los 60 días (ADR-005)
- Límite de envíos por IP (NFR-S06): hasta 10 por hora en `POST /legajos` y otros 10 en `POST /legajos/recuperar-acceso`; el siguiente responde 429 `RATE_LIMITED` con `Retry-After` y cuánto falta en el mensaje
- Formulario de inscripción conectado a la API: validación en tiempo real, guarda el borrador con `POST /legajos`, muestra los errores del back al lado de cada campo y permite pedir un link nuevo
- Retro del hito 1 en `docs/retros/2026-11-01.md`
- Cambio de estado del legajo con `ServicioEstados`: valida la transición, genera el número de legajo sin repetirlo, guarda la auditoría y manda el email de cada acción (incluido el aviso de vencimiento a los coordinadores). Detalle del legajo con checklist de documentos, historial y acciones permitidas: `GET /legajos/{id}` y `PATCH /legajos/{id}/estado` para el coordinador
- Página de seguimiento del aspirante (`/seguimiento/:token`) conectada a la API: estado y código de seguimiento, un aviso de qué hacer según el estado (con la observación del coordinador y el plazo para matricularse), el resumen de sus datos y la subida de PDFs con validación de tipo y tamaño en el navegador, reemplazo y "Ver"; si el link venció, ofrece pedir uno nuevo
- Búsqueda de legajos para el dashboard del coordinador: `GET /legajos` busca por DNI exacto o parte del apellido (sin distinguir mayúsculas, con los comodines `%` y `_` tomados literales), filtra por estado, cohorte, carrera y beca, pagina con los más nuevos primero y cuenta los documentos cargados de los requeridos; `GET /legajos/resumen` da el total, los 10 estados y las becas por tipo, con cohorte opcional
- PDFs del aspirante: `POST /seguimiento/{token}/documentos` acepta solo PDFs reales (por sus primeros bytes) de hasta 5 MB y del tipo que le corresponde, los guarda en disco con nombre UUID y SHA-256 y reemplaza al anterior del mismo tipo; descargas del aspirante (solo de su legajo) y del coordinador sin caché, y `GET /seguimiento/{token}` con el detalle del aspirante (ADR-002)
- Dashboard del coordinador conectado a la API: selector de cohorte, abrir y cerrar el período con la próxima apertura, tarjetas del resumen, tabla de legajos con búsqueda por DNI o apellido, filtros por estado, carrera y beca y páginas de 20, y el menú lateral usable en el celular
- Detalle del legajo para el coordinador: datos, carreras y beca, documentación con vista previa del PDF (descargado con el token, sin URL directa), historial en hora argentina y las acciones permitidas (pasar a revisión, observar con comentario obligatorio, aprobar, rechazar, matricular y dar de baja) con su confirmación
- Vencimiento de reservas: todos los días a las 3:00 (hora de Argentina) los legajos COMPLETADO con 30 días o más desde la aprobación pasan a VENCIDO, con auditoría del sistema y email a cada coordinador activo; se corre a mano con `uv run python -m src.legajos.infrastructure.job_vencimiento` (ADR-007)
- Edición y envío del legajo desde el link del aspirante: `PUT /seguimiento/{token}` cambia los datos en BORRADOR u OBSERVADO con las mismas reglas que el formulario (DNI y email únicos sin contar al propio legajo, período abierto), y `POST /seguimiento/{token}/enviar` hace ENVIAR o CORREGIR con `ServicioEstados` solo si están todos los documentos obligatorios (si no, 422 `DOCUMENTOS_FALTANTES`)

### Changed
- `docker-compose.yml` y `.env.example` reemplazan las plantillas viejas de Node
- El CI reemplaza el pipeline de Node por ruff, Alembic y pytest con PostgreSQL 16 en el back, y lint y build en el front
- En `docker compose`, el front monta el código y recarga solo al guardar, y el back corre el seed siempre al arrancar (ya sin el `if` provisorio)
- El seed valida cada paso del historial con la máquina de estados del legajo y arma los números con `generar_numero_legajo`; la etiqueta "Constancia de CUIT / CUIL" del front ahora coincide con la del back
- Ajustes de la inscripción tras la revisión del PR #44: el teléfono pide 8 números o más como el formulario, el 422 muestra el mensaje de cada regla en vez del genérico, Swagger aclara de dónde salen los ids y muestra el 409 de período cerrado, y recuperar acceso manda el email después de responder

### Fixed
- En `POST /legajos`, el teléfono fijo y el título de posgrado vacíos o con solo espacios se guardan como `null`: así no se pide la copia del título de posgrado a quien no lo tiene
- En `POST /legajos`, el email alternativo es obligatorio, como piden el SRS y el contrato del plan (antes se aceptaba vacío o nulo), y la motivación puede tener hasta 2000 caracteres (antes no tenía tope y el endpoint es público)
- En el formulario de inscripción, la motivación se frena en 2000 caracteres: el textarea no deja escribir más, el contador muestra "N / 2000" y la validación usa el mismo mensaje que el 422 del back
- Los logs del back ya no guardan el token del link de seguimiento: el log de accesos y el de errores muestran `/seguimiento/***` (ADR-005)

---

## [v0.1.0-alpha] — Sprint 0 (esperado 15/05/2026)

### Added
- Autenticación JWT básica (login/logout)
- Modelo de base de datos inicial con migraciones
- Docker Compose funcional para ambiente de desarrollo
- Pipeline de CI/CD base en GitHub Actions (lint + test + build)

---

## Historial de versiones planificadas

| Versión | Fecha planificada | Descripción |
|---------|:-----------------:|------------|
| v0.1.0-alpha | 15/05/2026 | Auth + DB + Docker |
| v0.5.0-beta | 31/07/2026 | Core completo |
| v0.8.0-rc | 11/09/2026 | Core + Módulo especializado |
| v1.0.0 | 23/10/2026 | Sistema completo + docs |
