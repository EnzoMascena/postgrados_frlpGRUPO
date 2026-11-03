"""Configuración del back por variables de entorno.

Se lee una sola vez, al importar este módulo: una variable que necesite un test tiene que
estar puesta antes de importar `src` o `main`.
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LARGO_MINIMO_JWT_SECRET = 32


class Settings(BaseSettings):
    # Corriendo desde backend/, busca el .env de la raíz del repo y, después, uno en backend/.
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    environment: str = "development"

    database_url: str = (
        "postgresql+psycopg://postgrado_user:postgrado_dev_password@localhost:5432/postgrado_dev"
    )
    test_database_url: str = (
        "postgresql+psycopg://postgrado_user:postgrado_dev_password@localhost:5432/postgrado_test"
    )

    # Sin valor por defecto: un secreto no se escribe en el código (NFR-M04).
    jwt_secret: str
    jwt_expira_minutos: int = 480

    storage_path: str = "./.storage"

    smtp_host: str = "localhost"
    smtp_port: int = 1025
    email_from: str = "noreply@posgrado.frlp.utn.edu.ar"
    frontend_url: str = "http://localhost:3000"

    # Orígenes permitidos, separados por comas.
    cors_origins: str = "http://localhost:3000"

    token_seguimiento_dias: int = 60
    zona_horaria: str = "America/Argentina/Buenos_Aires"

    # Datos del coordinador que carga el seed. Tampoco llevan valor en el código.
    seed_coordinador_email: str | None = None
    seed_coordinador_password: str | None = None

    @field_validator("jwt_secret")
    @classmethod
    def validar_largo_del_secreto(cls, valor: str) -> str:
        if len(valor) < LARGO_MINIMO_JWT_SECRET:
            raise ValueError(
                f"JWT_SECRET tiene que tener {LARGO_MINIMO_JWT_SECRET} caracteres o más"
            )
        return valor

    @property
    def cors_origins_lista(self) -> list[str]:
        return [origen.strip() for origen in self.cors_origins.split(",") if origen.strip()]


settings = Settings()
