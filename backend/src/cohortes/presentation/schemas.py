"""Schemas de cohortes y carreras (plan §10): JSON en camelCase, atributos en snake_case."""

from datetime import date
from uuid import UUID

from pydantic import ConfigDict

from src.cohortes.domain.tipos import TipoCarrera
from src.shared.schemas import CamelModel


class CohorteResponse(CamelModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "c1a2b3c4-d5e6-4f70-8a9b-0c1d2e3f4a5b",
                    "anio": 2026,
                    "numero": 1,
                    "nombre": "Cohorte 2026",
                    "inscripcionAbierta": True,
                    "fechaInicio": "2026-04-01",
                    "proximaApertura": None,
                }
            ]
        }
    )

    id: UUID
    anio: int
    numero: int
    nombre: str
    inscripcion_abierta: bool
    fecha_inicio: date | None
    proxima_apertura: date | None


class CarreraResponse(CamelModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "5d2f8a1b-3c4d-4e5f-9a0b-1c2d3e4f5a6b",
                    "nombre": "Maestría en Tecnología Informática",
                    "tipo": "Maestria",
                }
            ]
        }
    )

    id: UUID
    nombre: str
    tipo: TipoCarrera
