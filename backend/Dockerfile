# Imagen del back: Python 3.12 con las dependencias instaladas por uv (US-TECH-002).
FROM python:3.12-slim

# uv en versión fija, copiado de su imagen oficial.
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /usr/local/bin/uv

# uv usa el Python de la imagen en vez de bajar otro; los logs salen sin buffer.
ENV UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Primero las dependencias: si solo cambia el código, Docker reusa esta capa y el build es rápido.
# Con las de desarrollo, para poder correr pytest adentro del contenedor.
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked

COPY . .
RUN chmod +x start.sh

EXPOSE 8000
CMD ["./start.sh"]
