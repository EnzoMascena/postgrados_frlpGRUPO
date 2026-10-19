"""
Tareas programadas (ARQUITECTURA §12) con APScheduler 3.

    | Job                   | Hora  | Módulo               |
    |-----------------------|-------|----------------------|
    | recalcular_semaforos  | 02:00 | legajo (Gero)        |
    | vencer_reservas       | 03:00 | dashboard (Dolores)  |
    | recordatorio_docentes | 08:00 | planilla (Luca)      |

core/ no conoce la lógica de ningún job. Cada módulo escribe su función en
su dependencies.py (ahí arma la cadena repository → service, porque un job
no tiene request), y main.py la registra con `registrar_job()`. Al arrancar
la app, `iniciar()` programa todo; al apagarla, `detener()` lo frena.

Detalles que importan:
  - Apagado en los tests (SCHEDULER_ENABLED=false en testing).
  - Corre en un hilo del mismo proceso que uvicorn, así que asume UN worker.
    Con varios, cada uno correría los jobs: haría falta un lock en la base o
    un proceso aparte.
  - Un job que todavía es TODO (NotImplementedError) solo se loguea. Si un
    job falla, se loguea con el traceback y la API sigue andando.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core import config

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Job:
    """Un job diario: su nombre, la función que corre y la hora (local)."""

    nombre: str
    funcion: Callable[[], None]
    hora: int
    minuto: int = 0


_jobs: dict[str, Job] = {}
_scheduler: BackgroundScheduler | None = None


def registrar_job(nombre: str, funcion: Callable[[], None], *, hora: int, minuto: int = 0) -> None:
    """Anota un job para que `iniciar()` lo programe todos los días a esa hora."""
    _jobs[nombre] = Job(nombre=nombre, funcion=funcion, hora=hora, minuto=minuto)


def jobs_registrados() -> list[Job]:
    """Los jobs anotados, en el orden en que se registraron."""
    return list(_jobs.values())


def ejecutar_job(job: Job) -> None:
    """Corre un job atrapando sus errores: un job roto no tira la API."""
    try:
        job.funcion()
    except NotImplementedError as pendiente:
        logger.info("Job %s pendiente de implementar: %s", job.nombre, pendiente)
    except Exception:
        logger.exception("Falló el job %s", job.nombre)
    else:
        logger.info("Job %s terminado", job.nombre)


def obtener_scheduler() -> BackgroundScheduler | None:
    """El scheduler en marcha, o None si está apagado."""
    return _scheduler


def iniciar() -> None:
    """Programa los jobs registrados y arranca el scheduler (si está habilitado)."""
    global _scheduler
    if not config.SCHEDULER_ENABLED or _scheduler is not None:
        return

    scheduler = BackgroundScheduler(timezone=config.ZONA_HORARIA)
    for job in _jobs.values():
        scheduler.add_job(
            ejecutar_job,
            CronTrigger(hour=job.hora, minute=job.minuto, timezone=config.ZONA_HORARIA),
            args=[job],
            id=job.nombre,
            replace_existing=True,
            # Si el server estuvo apagado a la hora del job, corre una vez al volver.
            coalesce=True,
            misfire_grace_time=3600,
        )
    scheduler.start()
    _scheduler = scheduler
    logger.info("Scheduler en marcha con %d jobs (%s)", len(_jobs), config.ZONA_HORARIA)


def detener() -> None:
    """Frena el scheduler sin esperar a que termine un job en curso."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
