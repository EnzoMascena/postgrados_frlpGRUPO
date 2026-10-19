"""
Contrato de auth — lo que entra y sale por la API (schemas).

Igual que los modelos UserLogin / Token / UserRead del módulo 04, con dos
diferencias:

  1. Heredan de CamelModel: el JSON viaja en camelCase (`accessToken`,
     `legajoId`), como lo esperan los types.ts del front.
  2. El email del login es un `str`, NO un `EmailStr`. email-validator
     rechaza los dominios reservados como `.test`, y los usuarios demo son
     `admin@fenix.test`. La normalización (minúsculas, sin espacios) es una
     regla de negocio y la hace el service, como en el módulo 04.

Los schemas NO son las tablas: la tabla Usuario tiene password_hash, y eso
JAMÁS sale por la API (lección Nº2 del módulo 04).
"""

from uuid import UUID

from pydantic import ConfigDict, Field

from app.core.schemas import CamelModel
from app.core.security import TipoToken
from app.models.enums import Rol


class LoginRequest(CamelModel):
    """Lo que manda el front para iniciar sesión."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"email": "admin@fenix.test", "password": "Admin1234!"}]}
    )

    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(CamelModel):
    """Lo que devuelve el login: el JWT que el front manda en cada request,
    en el header `Authorization: Bearer <accessToken>`."""

    access_token: str
    token_type: str = "bearer"


class PrincipalRead(CamelModel):
    """Quién está usando el sistema (GET /auth/me).

    Con esto el front decide qué menú mostrar (rol) y a qué recurso apunta
    cada pantalla: el aspirante a SU legajo, el docente a SU seminario.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "tipo": "usuario",
                    "rol": "COORDINADOR",
                    "email": "admin@fenix.test",
                    "nombre": "María González",
                    "usuarioId": "6f1c8a52-1f8e-5b6e-9a51-2d3c4b5a6978",
                    "legajoId": None,
                    "seminarioId": None,
                }
            ]
        }
    )

    tipo: TipoToken
    rol: Rol
    email: str | None = None
    nombre: str | None = None
    usuario_id: UUID | None = None
    legajo_id: UUID | None = None
    seminario_id: UUID | None = None
