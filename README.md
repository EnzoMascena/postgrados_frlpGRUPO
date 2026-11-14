# 🎓 Sistema de Posgrado
### Sistema de Gestión Académica · UTN FRLP · Desarrollo de Software 2026

[![Estado](https://img.shields.io/badge/estado-En%20Desarrollo-yellow)](#)
[![Cobertura objetivo](https://img.shields.io/badge/cobertura-≥70%25-green)](#)
[![Versión](https://img.shields.io/badge/versión-v0.5%20·%20Core-blue)](CHANGELOG.md)

> **Proyecto integrador** de la cátedra **Desarrollo de Software** — 3° año · Turno NOche · Ingeniería en Sistemas de Información · UTN FRLP · 2026

---

## ¿Qué es este proyecto?

**Sistema Postgrados** reemplaza el proceso manual de gestión de posgrado de UTN FRLP —hoy basado en Excel, carpetas físicas y correos— por una plataforma web centralizada que digitaliza el ciclo de vida del estudiante: desde la preinscripción hasta la graduación.

**Este repositorio es el punto de entrada único** para todos los equipos del curso. Cada equipo implementa el **Módulo Core (obligatorio para todos)** más **un módulo especializado** asignado por sorteo.

---

## Cómo levantar el proyecto

### Qué necesitás instalado

| Herramienta | Versión | Para qué |
|---|---|---|
| Git | cualquiera | Clonar el repo |
| Docker Desktop (con Compose v2) | actual | Levanta todo con un solo comando |
| Node.js | **22.22 o más nuevo** | Solo si corrés el front fuera de Docker |
| uv | actual | Solo si corrés el back o los tests fuera de Docker. Instala Python 3.12 si no lo tenés |

- **Node en Windows:** `winget install OpenJS.NodeJS.22`. React Router 8 exige Node 22.22 o más nuevo: con una 22 más vieja, `npm` avisa `EBADENGINE`.
- **uv:** en Linux o macOS `curl -LsSf https://astral.sh/uv/install.sh | sh`; en Windows `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`.

### Levantar todo con un comando

```bash
git clone https://github.com/EnzoMascena/postgrados_frlpGRUPO.git
cd postgrados_frlpGRUPO
cp .env.example .env        # en PowerShell: Copy-Item .env.example .env
docker compose up --build
```

La primera vez tarda unos minutos, porque construye las imágenes. Levanta cuatro servicios: la base (PostgreSQL 16), MailHog, el back y el front. Al arrancar, el back **migra la base y carga los datos de prueba** (3 carreras, 3 cohortes, el coordinador y 11 legajos), así que no hay que correr nada más.

El `.env` **nunca se commitea**. El de `.env.example` ya sirve para desarrollo, pero cambiá `JWT_SECRET` por uno propio si lo vas a usar fuera de tu máquina.

### Dónde está cada cosa

| Qué | URL |
|---|---|
| Front | http://localhost:3000 |
| API, con Swagger | http://localhost:8000/api/docs |
| Estado de la API y de la base | http://localhost:8000/api/v1/health |
| MailHog (los emails que manda el sistema) | http://localhost:8025 |
| PostgreSQL | `localhost:5432` (usuario, clave y nombre en tu `.env`) |

### Usuario de prueba

Entrá a http://localhost:3000/login con el coordinador que crea el seed:

| Email | Clave | Rol |
|---|---|---|
| `admin@fenix.test` | `Admin1234!` | Coordinador |

Son datos de prueba de la cátedra, no una clave real. El aspirante no tiene usuario: entra al formulario público y después sigue su trámite con un link que le llega por email, que se ve en MailHog (esta parte está en construcción).

---

## Trabajar en el día a día

### Comandos de Docker

| Comando | Qué hace |
|---|---|
| `docker compose up -d` | Levanta todo en segundo plano |
| `docker compose logs -f backend` | Muestra los logs del back (también `frontend`, `db`, `mailhog`) |
| `docker compose down` | Frena todo y conserva la base |
| `docker compose down -v` | Frena todo y **borra la base**: el próximo `up --build` la recrea con el seed |
| `docker compose up -d --build backend` | Reconstruye el back después de cambiar su código o sus dependencias (el back **no** monta el código en el contenedor) |
| `docker compose exec backend uv run python -m src.legajos.infrastructure.job_vencimiento` | Corre ya el vencimiento de reservas, la tarea que corre sola todos los días a las 3:00 (ADR-007). El seed deja un legajo listo para vencer |

El front monta `./frontend` en el contenedor: cuando cambiás el código, Vite recarga el navegador sin reconstruir. Si cambia `package.json`, usá `docker compose up -d --build -V frontend`.

### Tests, lint y migraciones del back

Los tests necesitan la base. Con Docker, adentro del contenedor:

```bash
docker compose exec backend uv run pytest
```

O desde tu máquina (levantá antes la base con `docker compose up -d db`):

```bash
cd backend
uv sync                                   # instala las dependencias fijadas en uv.lock
uv run pytest                             # tests y cobertura (mínimo 70 %)
uv run ruff check . && uv run ruff format --check .
uv run alembic upgrade head               # aplica las migraciones
uv run python -m scripts.seed             # carga los datos de prueba (se puede correr varias veces)
uv run python -m src.legajos.infrastructure.job_vencimiento   # vence ya las reservas de 30 días o más
```

Las migraciones nuevas: `uv run alembic revision --autogenerate -m "descripcion"`. Ojo: Alembic **no detecta los cambios en los `CHECK`**; esos hay que escribirlos a mano en la migración.

### Correr el back o el front fuera de Docker

**Back** (si el back de Docker está corriendo, frenalo antes con `docker compose stop backend`: usa el mismo puerto 8000):
```bash
docker compose up -d db mailhog
cd backend
uv sync
uv run alembic upgrade head
uv run python -m scripts.seed
uv run uvicorn main:app --reload          # http://localhost:8000
```

**Front:**
```bash
docker compose stop frontend              # libera el puerto 3000
cd frontend
npm install
npm run dev                               # http://localhost:3000
npm run lint && npm run build             # lo mismo que corre el CI
```

Con `npm run dev` el proxy de Vite manda `/api` a `http://localhost:8000`, es decir, al back de Docker (o al que tengas corriendo en tu máquina). La variable `VITE_PROXY_TARGET` del `.env` **no** tiene efecto: Vite la lee del entorno del proceso, no de ese archivo. Para apuntar a otro back: `VITE_PROXY_TARGET=http://localhost:9000 npm run dev` (en PowerShell: `$env:VITE_PROXY_TARGET="http://localhost:9000"; npm run dev`).

---

## Si algo falla

| Síntoma | Causa y solución |
|---|---|
| `npm` avisa `EBADENGINE` o el front no arranca | Tenés una Node más vieja que 22.22. En Windows: `winget install OpenJS.NodeJS.22`. |
| `npm run build` falla con `TS2307: Cannot find module 'react-router'` (y un `TS7031` en `isActive`) | Tu `node_modules` está desactualizado: `git pull` trae el código nuevo pero no las dependencias. Cada vez que cambie `package.json` o `package-lock.json`, corré `cd frontend && npm ci` (instala exactamente lo del `package-lock.json`). En el back pasa lo mismo con `uv sync` cuando cambian `pyproject.toml` o `uv.lock`. |
| El back dice «la autentificación password falló para el usuario postgrado_user» | Hay **otro PostgreSQL ocupando el puerto 5432** y el back se conecta a ese en vez de al contenedor. Es común en Windows, donde el instalador de PostgreSQL deja un servicio (`postgresql-x64-NN`). Dos salidas: **a)** frenarlo, en PowerShell como administrador: `Stop-Service postgresql-x64-NN`; **b)** mover la base del TP a otro puerto: en el `.env` poné `DB_PORT=5433` y cambiá el `5432` por `5433` en `DATABASE_URL` y `TEST_DATABASE_URL`. El compose ya usa `${DB_PORT}`. |
| `port is already allocated` o `address already in use` | Otro programa o un contenedor de otra materia usa el 3000, 8000, 5432, 1025 u 8025. Con `docker ps` ves qué contenedores están corriendo; frenalos con `docker stop <nombre>`. |
| `failed to connect to the docker API` | Docker Desktop no está abierto. Abrilo y esperá a que diga que el motor está corriendo. |
| Al correr el back fuera de Docker falla con `ValidationError ... jwt_secret` | Falta el `.env` en la raíz del repo o su `JWT_SECRET` tiene menos de 32 caracteres. Copiá `.env.example` otra vez. (Con Docker no pasa: el compose trae un valor de desarrollo.) |
| El formulario o "pedir un link nuevo" responden 429 `RATE_LIMITED` | Hubo más de 10 envíos en la última hora desde la misma IP (NFR-S06). En desarrollo todo el front llega con la IP del proxy de Vite, así que el límite es por máquina. Esperá lo que dice el mensaje o reiniciá el back, porque los contadores están en memoria: `docker compose restart backend`. |
| Querés empezar de cero | `docker compose down -v` y después `docker compose up --build`. |

---

## Estructura del repositorio

```
backend/                 API en FastAPI
  main.py                crea la app y registra los routers
  src/<modulo>/          autenticacion, cohortes, inscripcion, gestion_documental, legajos y shared
    domain/              reglas del negocio, en Python puro
    application/         casos de uso
    infrastructure/      tablas (SQLModel) y repositorios
    presentation/        endpoints y schemas de la API
  alembic/               migraciones de la base
  scripts/               seed y vista previa de los emails
  tests/                 un directorio por módulo
frontend/src/<modulo>/   React: pantallas por módulo y lo compartido en shared/
adr/                     decisiones de arquitectura (por qué elegimos lo que elegimos)
docs/                    plan del Core, SRS, arquitectura y wireframes
```

### Documentación

- [`docs/PLAN_CORE.md`](docs/PLAN_CORE.md): alcance, reparto de tareas y contrato de la API del Core.
- [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) y [`adr/`](adr/): cómo está armado y por qué.
- [`CONTRIBUTING.md`](CONTRIBUTING.md): ramas, commits, Pull Requests y revisión de código.
- [`docs/DEFINITION_OF_DONE.md`](docs/DEFINITION_OF_DONE.md): cuándo una tarea está terminada.
- [`CHANGELOG.md`](CHANGELOG.md): qué cambió en cada versión.

---

## Equipo

| Nombre              | Rol                          | GitHub                          | Email                          |
|---------------------|------------------------------|---------------------------------|--------------------------------|
| Mascena Enzo Mario           | Líder / Desarrollador Principal | [@EnzoMascena](https://github.com/EnzoMascena) | enzo.mascena.dev@gmail.com         |
| Garrote Geronino    | Diseñador UI/UX / Frontend         | [@GeronimoGarrote](https://github.com/GeronimoGarrote)   | garrote.gero@gmail.com            |
| Buscaglia Francisco Nicolas  | Desarrollador Backend        | [@FranBusqui](https://github.com/FranBusqui)   | franbuscag@gmail.com            |
| Goñi Dolores  | Diseñador / Frontend         | [@lologoni](https://github.com/lologoni)   | lolagoni2004@gmail.com            |
| De Paola Luca | Desarrollador / Backend        | [@LucaDP16](https://github.com/LucaDP16)   | ludepa3110@gmail.com            |
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

| Capa | Tecnología | Por qué |
|------|------------|---------|
| **Frontend** | React 19 + TypeScript + Vite + Tailwind CSS 4 + TanStack Query + React Router | Es lo que ya tenía la entrega del front |
| **Backend** | FastAPI (Python 3.12) | Swagger automático, validación con Pydantic y lógica de negocio en Python puro |
| **Base de datos** | PostgreSQL 16 con SQLModel (SQLAlchemy 2) y Alembic | La base hace cumplir las reglas (restricciones `UNIQUE` y `CHECK`) y migra con Alembic |
| **Testing** | pytest + httpx, con cobertura mínima del 70 % | Los tests corren contra el mismo PostgreSQL que el sistema real |
| **Dependencias** | uv (back) y npm (front), con `uv.lock` y `package-lock.json` | Todos instalamos exactamente las mismas versiones |
| **DevOps** | Docker Compose y GitHub Actions | `docker compose up --build` levanta todo; el CI corre ruff, Alembic, pytest, lint y build |

El detalle de por qué elegimos este stack y qué trade-offs aceptamos está en [`adr/ADR-001-stack.md`](adr/ADR-001-stack.md).

> El stack lo sugiere la cátedra. Si el equipo quiere otra tecnología, debe presentar un **RFC aprobado antes de la semana 4**.


---
*Proyecto académico · Cátedra Desarrollo de Software · UTN FRLP · 2026*
