"""Schemas del login (plan §10): JSON en camelCase, atributos en snake_case."""

from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, Field

from src.shared.roles import Rol
from src.shared.schemas import CamelModel


class LoginRequest(CamelModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"email": "admin@fenix.test", "password": "Admin1234!"}]}
    )

    # `str` y no `EmailStr`: `.test` es un dominio reservado y `EmailStr` rechaza el usuario del
    # seed (admin@fenix.test). En el login no hace falta validar el formato: un email que no
    # existe da el mismo 401 que una clave incorrecta (ADR-003).
    email: str = Field(min_length=1, max_length=255)
    # Tope barato contra bodies enormes. El límite real de bcrypt (72 bytes) lo controla
    # `hashing.py`, que cuenta bytes y no caracteres.
    password: str = Field(min_length=1, max_length=128)


class UsuarioResponse(CamelModel):
    # Se arma desde el `Usuario` del dominio, pero sin `password_hash` ni `activo`.
    id: UUID
    email: str
    nombre: str
    rol: Rol


class LoginResponse(CamelModel):
    """Se arma directo desde `SesionIniciada`: `LoginResponse.model_validate(sesion)`."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "tokenType": "bearer",
                    "expiraEn": 28800,
                    "usuario": {
                        "id": "8c1e4f2a-3b5d-4e6f-9a1b-2c3d4e5f6a7b",
                        "email": "admin@fenix.test",
                        "nombre": "María González",
                        "rol": "COORDINADOR",
                    },
                }
            ]
        }
    )

    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expira_en: int  # segundos de validez del token
    usuario: UsuarioResponse
