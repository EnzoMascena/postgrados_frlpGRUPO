#!/usr/bin/env sh
# ─────────────────────────────────────────────────────────────────────────
# start.sh — arranque del backend: migra, siembra y levanta la API.
#
# Lo llama el Dockerfile (CMD ["./start.sh"]) y también sirve en local:
#   cd backend && ./start.sh
#
#   1. alembic upgrade head  → crea o actualiza las tablas (nunca create_all)
#   2. python -m app.seed    → los datos demo; es idempotente, no duplica nada
#   3. uvicorn en 0.0.0.0    → 0.0.0.0 para que se vea desde fuera del contenedor
#
# --frozen: usa uv.lock tal cual, sin volver a resolver (lo mismo en todas
# las máquinas). Si la imagen se arma con `uv sync --frozen --no-dev`,
# definí UV_NO_SYNC=1 para que `uv run` no intente instalar lo de desarrollo.
# ─────────────────────────────────────────────────────────────────────────
set -e
cd "$(dirname "$0")"

echo "→ Migraciones: alembic upgrade head"
uv run --frozen alembic upgrade head

echo "→ Seed (idempotente)"
uv run --frozen python -m app.seed

echo "→ API en http://0.0.0.0:8000 · Swagger en /api/docs"
# exec: uvicorn reemplaza al shell y recibe las señales de Docker (docker stop).
exec uv run --frozen uvicorn app.main:app --host 0.0.0.0 --port 8000
