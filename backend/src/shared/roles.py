"""Roles del sistema y quién hace una acción. Python puro."""

from dataclasses import dataclass
from enum import StrEnum


class Rol(StrEnum):
    ASPIRANTE = "ASPIRANTE"
    COORDINADOR = "COORDINADOR"
    DOCENTE = "DOCENTE"
    CPR = "CPR"
    ADMIN = "ADMIN"
    SISTEMA = "SISTEMA"


@dataclass(frozen=True)
class Actor:
    rol: Rol
    email: str | None = None
