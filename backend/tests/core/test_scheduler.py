"""Tests del scheduler de tareas programadas (ARQUITECTURA §12)."""

import logging

import pytest

from app.core import config, scheduler


@pytest.fixture(autouse=True)
def registro_limpio(monkeypatch):
    """Cada test arranca sin jobs registrados y con el scheduler apagado."""
    monkeypatch.setattr(scheduler, "_jobs", {})
    yield
    scheduler.detener()


def test_en_testing_el_scheduler_no_arranca():
    scheduler.registrar_job("vencer_reservas", lambda: None, hora=3)
    scheduler.iniciar()
    assert scheduler.obtener_scheduler() is None


def test_programa_cada_job_registrado_a_su_hora(monkeypatch):
    monkeypatch.setattr(config, "SCHEDULER_ENABLED", True)
    scheduler.registrar_job("recalcular_semaforos", lambda: None, hora=2)
    scheduler.registrar_job("recordatorio_docentes", lambda: None, hora=8, minuto=30)

    scheduler.iniciar()

    en_marcha = scheduler.obtener_scheduler()
    assert en_marcha is not None
    trigger = en_marcha.get_job("recordatorio_docentes").trigger
    campos = {campo.name: str(campo) for campo in trigger.fields}
    assert (campos["hour"], campos["minute"]) == ("8", "30")
    assert str(trigger.timezone) == config.ZONA_HORARIA
    assert [job.nombre for job in scheduler.jobs_registrados()] == [
        "recalcular_semaforos",
        "recordatorio_docentes",
    ]


def test_detener_frena_el_scheduler(monkeypatch):
    monkeypatch.setattr(config, "SCHEDULER_ENABLED", True)
    scheduler.iniciar()
    scheduler.detener()
    assert scheduler.obtener_scheduler() is None


def test_un_job_terminado_queda_en_el_log(caplog):
    llamadas = []
    job = scheduler.Job("vencer_reservas", lambda: llamadas.append(1), hora=3)
    with caplog.at_level(logging.INFO):
        scheduler.ejecutar_job(job)
    assert llamadas == [1]
    assert "Job vencer_reservas terminado" in caplog.text


def test_un_job_todavia_todo_solo_se_loguea(caplog):
    def pendiente():
        raise NotImplementedError("TODO(Dolores): US-CORE-010 vencer reservas")

    with caplog.at_level(logging.INFO):
        scheduler.ejecutar_job(scheduler.Job("vencer_reservas", pendiente, hora=3))
    assert "pendiente de implementar" in caplog.text
    assert "US-CORE-010" in caplog.text


def test_un_job_que_falla_no_lanza_y_deja_el_traceback(caplog):
    def roto():
        raise RuntimeError("se cayó la base")

    with caplog.at_level(logging.ERROR):
        scheduler.ejecutar_job(scheduler.Job("recalcular_semaforos", roto, hora=2))
    assert "Falló el job recalcular_semaforos" in caplog.text
    assert "se cayó la base" in caplog.text
