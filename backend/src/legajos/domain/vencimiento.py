"""Vencimiento de la reserva de vacante (BR-005). Python puro.

Un legajo COMPLETADO tiene 30 días corridos desde `fecha_aprobacion` para matricularse; cumplidos,
la tarea diaria de Enzo (E6) lo pasa a VENCIDO con `ServicioEstados` y `Accion.VENCER`.
Las fechas llegan con zona horaria (UTC desde la base); comparar una con zona y otra sin zona
levanta `TypeError`, a propósito.
"""

from datetime import datetime, timedelta

DIAS_RESERVA = 30


def fecha_limite(fecha_aprobacion: datetime) -> datetime:
    """El momento en que vence la reserva: la aprobación más 30 días corridos."""
    return fecha_aprobacion + timedelta(days=DIAS_RESERVA)


def reserva_vencida(fecha_aprobacion: datetime, ahora: datetime) -> bool:
    """Verdadero si ya pasaron 30 días o más desde la aprobación."""
    return ahora >= fecha_limite(fecha_aprobacion)
