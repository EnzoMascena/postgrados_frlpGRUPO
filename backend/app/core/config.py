"""
Configuración de la aplicación — variables de entorno y constantes.

Misma filosofía que el config.py del módulo 06 de la cátedra:

  - Todo tiene un DEFAULT DE DESARROLLO, así el backend corre sin .env
    contra el postgres local (docker run o docker compose).
  - En producción lo sensible es OBLIGATORIO: si falta SECRET_KEY la app
    NO arranca (fail-loud). Un default silencioso en producción sería una
    bomba: cualquiera que lea el repo podría fabricar tokens válidos.

Regla de oro (NFR-M04): ningún secreto en el código. Salen del entorno.

Los valores se leen UNA sola vez, al importar este módulo. Por eso los
tests fijan ENVIRONMENT=testing ANTES de importar la app (tests/conftest.py).
"""

import os
from pathlib import Path


def _env_bool(nombre: str, default: bool) -> bool:
    """Lee una variable booleana: "true", "1", "si" o "yes" valen True."""
    valor = os.getenv(nombre)
    if valor is None:
        return default
    return valor.strip().lower() in {"1", "true", "si", "sí", "yes"}


# ──────────────────────────────────────────────────────────────────────────
# Entorno
# ──────────────────────────────────────────────────────────────────────────
# "development" (default) | "production" | "testing"
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()
IS_PRODUCTION: bool = ENVIRONMENT == "production"
IS_TESTING: bool = ENVIRONMENT == "testing"

# Todas las rutas cuelgan de acá (ARQUITECTURA §11.1).
API_PREFIX: str = "/api/v1"

# ──────────────────────────────────────────────────────────────────────────
# JWT
# ──────────────────────────────────────────────────────────────────────────
_SECRET_KEY = os.getenv("SECRET_KEY")
if not _SECRET_KEY:
    if IS_PRODUCTION:
        # Fail-loud: sin SECRET_KEY no hay firma segura → no se puede arrancar.
        raise RuntimeError(
            "SECRET_KEY es OBLIGATORIA en producción. Generala con: "
            "openssl rand -hex 32   y pasala por variable de entorno. "
            "NUNCA hardcodeada en el código."
        )
    # Solo para desarrollo local. Generá la tuya con `openssl rand -hex 32`.
    _SECRET_KEY = "dev-only-posgrado-frlp-3c1f9a7e5b2d4c86-no-usar-en-produccion"
SECRET_KEY: str = _SECRET_KEY

# Fijo a propósito: el algoritmo NUNCA sale del entorno ni del token
# (si lo eligiera el token, habilitaríamos el "algorithm confusion attack").
ALGORITHM: str = "HS256"

# Token de usuario (coordinador y CPR): 8 horas, sin refresh token.
USUARIO_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("USUARIO_TOKEN_EXPIRE_MINUTES", "480"))

# Token de seguimiento del aspirante: se renueva pidiendo /legajos/recuperar.
ASPIRANTE_TOKEN_EXPIRE_DAYS: int = int(os.getenv("ASPIRANTE_TOKEN_EXPIRE_DAYS", "7"))

# ──────────────────────────────────────────────────────────────────────────
# Base de datos (PostgreSQL 16)
# ──────────────────────────────────────────────────────────────────────────
# El default apunta al postgres local con los datos del docker-compose.
# Dentro de Docker, DATABASE_URL llega por entorno con el host `db`.
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgrado_user:postgrado_dev_password@localhost:5432/postgrado_dev",
)

# Base APARTE para los tests: se crea sola si no existe (tests/conftest.py).
TEST_DATABASE_URL: str = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://postgrado_user:postgrado_dev_password@localhost:5432/postgrado_test",
)

# ──────────────────────────────────────────────────────────────────────────
# PDFs de los aspirantes (ASR-001)
# ──────────────────────────────────────────────────────────────────────────
# Fuera de cualquier carpeta pública. En local: backend/.storage/ (ignorada
# por Git). En Docker: un volumen, por ejemplo /var/postgrado-storage.
_BACKEND_DIR = Path(__file__).resolve().parents[2]
STORAGE_PATH: Path = Path(os.getenv("STORAGE_PATH", str(_BACKEND_DIR / ".storage")))

# RF-CORE-002: hasta 5 MB por archivo.
MAX_PDF_BYTES: int = 5 * 1024 * 1024

# ──────────────────────────────────────────────────────────────────────────
# Mail (MailHog en desarrollo: SMTP en el 1025, interfaz en el 8025)
# ──────────────────────────────────────────────────────────────────────────
SMTP_HOST: str = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "1025"))
SMTP_USER: str | None = os.getenv("SMTP_USER") or None
SMTP_PASSWORD: str | None = os.getenv("SMTP_PASSWORD") or None
SMTP_STARTTLS: bool = _env_bool("SMTP_STARTTLS", False)
EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@posgrado.frlp.utn.edu.ar")

# A dónde apuntan los links de los mails (seguimiento del aspirante,
# acceso del docente).
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

# ──────────────────────────────────────────────────────────────────────────
# Tareas programadas (ARQUITECTURA §12)
# ──────────────────────────────────────────────────────────────────────────
# Apagadas en los tests: un job corriendo en segundo plano los volvería
# impredecibles.
SCHEDULER_ENABLED: bool = _env_bool("SCHEDULER_ENABLED", default=not IS_TESTING)
ZONA_HORARIA: str = os.getenv("ZONA_HORARIA", "America/Argentina/Buenos_Aires")
