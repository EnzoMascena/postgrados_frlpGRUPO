"""
Base de todos los schemas de la API: entran y salen en camelCase.

El front (los types.ts de cada pantalla) habla camelCase y Python habla
snake_case. En vez de escribir cada alias a mano, CamelModel los genera:
el campo `apellido_nombre` en Python es `apellidoNombre` en el JSON.

  - alias_generator=to_camel → el JSON usa camelCase, al entrar y al salir.
  - validate_by_name=True    → en Python también se construye con snake_case.
  - serialize_by_alias=True  → model_dump() devuelve camelCase sin pedirlo.
  - from_attributes=True     → se arma directo desde un modelo de la base:
                               LegajoRead.model_validate(legajo).

Regla: los schemas de un módulo heredan de CamelModel, nunca de BaseModel.
"""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Schema con alias camelCase para la API."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
        serialize_by_alias=True,
        from_attributes=True,
    )
