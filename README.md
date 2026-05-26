# 🎓 Sistema de Posgrado
### Sistema de Gestión Académica · UTN FRLP · Desarrollo de Software 2026

[![Estado](https://img.shields.io/badge/estado-En%20Desarrollo-yellow)](#)
[![Cobertura objetivo](https://img.shields.io/badge/cobertura-≥70%25-green)](#)
[![Semana actual](https://img.shields.io/badge/semana-1%20de%2032-blue)](#)

> **Proyecto integrador** de la cátedra **Desarrollo de Software** — 3° año · Turno NOche · Ingeniería en Sistemas de Información · UTN FRLP · 2026

---

## ¿Qué es este proyecto?

**Sistema Postgrados** reemplaza el proceso manual de gestión de posgrado de UTN FRLP —hoy basado en Excel, carpetas físicas y correos— por una plataforma web centralizada que digitaliza el ciclo de vida del estudiante: desde la preinscripción hasta la graduación.

**Este repositorio es el punto de entrada único** para todos los equipos del curso. Cada equipo implementa el **Módulo Core (obligatorio para todos)** más **un módulo especializado** asignado por sorteo.

---
## Equipo
**Esta seccion es un template para el equipo, debe completarse en le primer commit**

| Nombre              | Rol                          | GitHub                          | Email                          |
|---------------------|------------------------------|---------------------------------|--------------------------------|
| Mascena Enzo Mario           | Líder / Desarrollador Principal | [@EnzoMascena](https://github.com/EnzoMascena) | enzo.mascena.dev@gmail.com         |
| Buscaglia Francisco Nicolas  | Desarrollador Backend        | [@FranBusqui](https://github.com/FranBusqui)   | franbuscag@gmail.com            |
| Nombre Compañero 3  | Diseñador / Frontend         | [@usuario3](https://github.com/usuario3)   | email3@ejemplo.com            |
| Nombre Compañero 4  | Diseñador / Frontend         | [@usuario4](https://github.com/usuario4)   | email4@ejemplo.com            |
| Nombre Compañero 5  | Diseñador / Frontend         | [@usuario5](https://github.com/usuario5)   | email5@ejemplo.com            |
### Reglas básicas del equipo

- **Commits**: Usa mensajes claros y en presente (ej: "Agrega login con GitHub"). Sigue la convención [Conventional Commits](https://www.conventionalcommits.org) si es posible.
- **Branching**: Nunca pushes directos a `main`. Crea una rama con tu nombre o tarea (`feature/nombre-tarea` o `bugfix/...`).
- **Pull Requests**: Siempre abre un PR para revisar el código. Mínimo 1 aprobación antes de mergear.
- **Código**: Mantén el código limpio, comenta lo complejo y respeta el estilo del proyecto (usa el `.editorconfig` si existe).
- **Issues**: Reporta bugs o ideas en la sección de Issues con la plantilla correspondiente.

**Revisa las reglas completas** CONTRIBUTING.md

### Comunicación
- **Comunicacion con docentes:** Mediante CVG o presencial en horarios de catedra
- **Principal del grupo**: Usamos **Discord/Slack/Teams** (agrega el link del canal).
- **Discusiones técnicas**: En los **Issues** y **Pull Requests** del repositorio.
- **Urgencias**: Mensaje directo por WhatsApp/Telegram/Slack.
- **Horario de pair programming**: Reuniones de trabajo virtual programadas
- **Reuniones**: [Breve weekly los miércoles a las XX hs] o según necesidad.


---

## Reglas No Negociables

## Stack Tecnológico 
** Template a completar por el equipo** 

## Stack Tecnológico

| Capa              | Recomendado (Prioridad: Simplicidad + Demanda) | Alternativa (Mayor estructura / Enterprise) | Justificación |
|-------------------|------------------------------------------------|---------------------------------------------|-------------|
| **Frontend**     | **React 19 + TypeScript + Vite + TailwindCSS + TanStack Query** | Next.js 15+ (App Router) | React sigue siendo la tecnología frontend **más demandada** del mercado. Vite es muy rápido y simple. TanStack Query simplifica mucho la gestión de datos. |
| **Backend**      | **FastAPI (Python 3.12+)**                    | NestJS (TypeScript)                        | FastAPI es **mucho más simple**, rápido de desarrollar, tiene documentación automática (Swagger) y excelente rendimiento. Ideal para proyectos académicos y APIs modernas. NestJS ofrece más estructura pero aumenta la complejidad. |
| **ORM / DB Layer** | **SQLAlchemy 2.0 + Alembic** (con async support) | Tortoise ORM o Prisma (si vas full TypeScript) | SQLAlchemy es el estándar más maduro y potente para Python. Alembic maneja migraciones muy bien. Para proyectos simples también puedes usar **SQLModel** (de tiangolo, creador de FastAPI) → aún más simple. |
| **Base de Datos** | **PostgreSQL 16/17 (Docker)**                 | ← igual                                    | Mejor relación rendimiento / features / ecosistema. Excelente con Docker. |
| **Testing**       | **Pytest + HTTPX** (unitarias + integración) + **Playwright** (E2E opcional) | Vitest + Supertest (si usas NestJS)       | Pytest es muy simple y potente. Enfocarte solo en **unitarias** como dijiste es una buena decisión para no complicar el proyecto. |
| **DevOps / Infra**| **Docker + Docker Compose + GitHub Actions** | ← igual                                    | Estándar actual. Muy simple de configurar con `docker-compose.yml`. |

### Por qué elegimos este stack

- **Alta empleabilidad**: React y PostgreSQL son de las tecnologías más solicitadas en 2026.
- **Simplicidad y velocidad de desarrollo**: FastAPI + SQLModel permite crear APIs completas con muy poco código.
- **Moderno pero maduro**: Evitamos tecnologías demasiado experimentales.
- **Full Docker**: Todo el entorno se levanta con un solo comando (`docker compose up`).

**¿Quieres cambiar algo?**  
El stack es flexible. Si prefieres **full TypeScript** (React + NestJS + Prisma), también es una excelente opción (más demandada en algunas empresas, pero más verbose).
> El stack es sugerido. Si el equipo quiere otra tecnología, debe presentar un **RFC aprobado antes de la semana 4**.


---
*Proyecto académico · Cátedra Desarrollo de Software · UTN FRLP · 2026*
