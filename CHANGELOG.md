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

### Changed
- `docker-compose.yml` y `.env.example` reemplazan las plantillas viejas de Node

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
