"""Estados del legajo. Python puro: sin FastAPI ni SQLModel.

Acá solo está el vocabulario. Luca suma las acciones y la tabla de transiciones en L2.
"""

from enum import StrEnum


class EstadoLegajo(StrEnum):
    BORRADOR = "BORRADOR"
    PENDIENTE = "PENDIENTE"
    EN_REVISION = "EN_REVISION"
    OBSERVADO = "OBSERVADO"
    COMPLETADO = "COMPLETADO"
    ACTIVO = "ACTIVO"
    VENCIDO = "VENCIDO"
    RECHAZADO = "RECHAZADO"
    BAJA = "BAJA"
    GRADUADO = "GRADUADO"
