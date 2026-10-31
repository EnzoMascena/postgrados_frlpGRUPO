#!/bin/sh
# Arranque del contenedor del back: migra la base, carga el seed y levanta la API.
# Con `set -e`, si falla la migración o el seed, el contenedor se cae en vez de arrancar a medias.
set -e

uv run alembic upgrade head

# shortcut: el seed llega con D2 (Loli, dom 1); cuando entre, sacar el if y correrlo siempre.
if [ -f scripts/seed.py ]; then
  uv run python -m scripts.seed
fi

# exec: uvicorn queda como proceso principal y recibe el Ctrl+C / `docker compose down`.
exec uv run uvicorn main:app --host 0.0.0.0 --port 8000
