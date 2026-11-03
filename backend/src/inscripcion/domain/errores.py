"""Errores propios de la inscripción. Python puro."""

from src.shared.errors import Conflicto


class PeriodoCerrado(Conflicto):
    codigo = "PERIODO_CERRADO"


class LegajoNoEditable(Conflicto):
    """Editar o subir documentos fuera de BORRADOR u OBSERVADO (lo usan F5 y F6)."""

    codigo = "LEGAJO_NO_EDITABLE"
