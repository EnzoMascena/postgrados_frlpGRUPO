"""Tipos de carrera. Python puro."""

from enum import StrEnum


class TipoCarrera(StrEnum):
    ESPECIALIZACION = "Especializacion"
    MAESTRIA = "Maestria"
    DOCTORADO = "Doctorado"
