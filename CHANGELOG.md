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
- Envío de emails con `enviar_email`: arma el HTML desde las plantillas, embebe el logo de la UTN y lo manda por SMTP (MailHog en desarrollo), con una bandeja de prueba para los tests
- Período de inscripción por cohorte: `GET /cohortes` y `GET /carreras` públicos para el formulario, y `PATCH /cohortes/{id}/inscripcion` para que el coordinador abra o cierre la inscripción con la próxima apertura

### Changed
- `docker-compose.yml` y `.env.example` reemplazan las plantillas viejas de Node
- El CI reemplaza el pipeline de Node por ruff, Alembic y pytest con PostgreSQL 16 en el back, y lint y build en el front

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
