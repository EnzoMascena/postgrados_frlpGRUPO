"""Tarea diaria de vencimiento de reservas (US-CORE-010, ADR-007).

Corre todos los días a las 3:00 (hora de Argentina) dentro del proceso de la API, con APScheduler:
`main.py` la programa al arrancar. Para la demo, o si la API estuvo apagada a esa hora, se corre
una vez a mano (desde backend/):

    uv run python -m src.legajos.infrastructure.job_vencimiento
"""

import logging
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session, col, select

from src.autenticacion.infrastructure.pg_repository import PgUsuarioRepository
from src.legajos.application.cambiar_estado import ServicioEstados
from src.legajos.application.vencer_reservas import (
    ReservaAprobada,
    ResultadoVencimiento,
    vencer_reservas,
)
from src.legajos.domain.estados import EstadoLegajo
from src.legajos.infrastructure.email_notificador import EmailNotificadorLegajos
from src.legajos.infrastructure.orm_models import LegajoORM
from src.legajos.infrastructure.pg_repository import PgLegajoRepository
from src.shared.config import settings
from src.shared.database import engine, importar_modelos

logger = logging.getLogger(__name__)

ID_TAREA = "vencimiento_reservas"
HORA = 3
# APScheduler saltea una corrida que arranca más de 1 segundo tarde (su valor por defecto). Con una
# hora de margen, un proceso ocupado o una máquina que se despierta a las 3:05 igual la corre.
MARGEN_SEGUNDOS = 3600


def reservas_aprobadas(session: Session) -> list[ReservaAprobada]:
    """Los legajos COMPLETADO con su fecha de aprobación, de la más vieja a la más nueva."""
    filas = session.exec(
        select(LegajoORM.id, LegajoORM.fecha_aprobacion)
        .where(
            LegajoORM.estado == EstadoLegajo.COMPLETADO.value,
            col(LegajoORM.fecha_aprobacion).is_not(None),
        )
        .order_by(col(LegajoORM.fecha_aprobacion))
    ).all()
    return [ReservaAprobada(legajo_id, fecha) for legajo_id, fecha in filas]


def correr_vencimiento(session: Session, ahora: datetime | None = None) -> ResultadoVencimiento:
    """Vence las reservas cumplidas con el mismo `ServicioEstados` que usa la API."""
    repo = PgLegajoRepository(session)
    servicio = ServicioEstados(repo, EmailNotificadorLegajos(repo, PgUsuarioRepository(session)))
    return vencer_reservas(reservas_aprobadas(session), servicio, ahora or datetime.now(UTC))


def resumen(resultado: ResultadoVencimiento) -> str:
    vencidos = len(resultado.vencidos)
    texto = f"Vencimiento: {vencidos} de {resultado.revisadas} legajos COMPLETADO pasaron a VENCIDO"
    if vencidos:
        texto += " (" + ", ".join(str(legajo.numero_legajo) for legajo in resultado.vencidos) + ")"
    return texto


def tarea_diaria() -> str:
    """Lo que corre APScheduler: abre su propia sesión, porque no hay un request detrás."""
    with Session(engine) as session:
        texto = resumen(correr_vencimiento(session))
    logger.info(texto)
    return texto


def crear_programador() -> BackgroundScheduler:
    """El programador con la tarea de las 3:00, sin arrancar. Corre en un hilo aparte de la API."""
    zona = ZoneInfo(settings.zona_horaria)
    programador = BackgroundScheduler(timezone=zona)
    programador.add_job(
        tarea_diaria,
        CronTrigger(hour=HORA, minute=0, timezone=zona),
        id=ID_TAREA,
        coalesce=True,  # si se juntaron varias corridas pendientes, corre una sola
        max_instances=1,  # nunca dos a la vez
        misfire_grace_time=MARGEN_SEGUNDOS,
    )
    return programador


def iniciar_programador() -> BackgroundScheduler:
    programador = crear_programador()
    programador.start()
    return programador


def main() -> None:
    importar_modelos()
    print(tarea_diaria())


if __name__ == "__main__":
    main()
