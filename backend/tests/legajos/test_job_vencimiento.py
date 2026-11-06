"""La tarea de vencimiento contra la base: qué vence, qué queda auditado, a quién avisa y cuándo corre.

Usa el `ServicioEstados` y el notificador reales: los emails quedan en la bandeja de prueba.
"""

import logging
from contextlib import nullcontext
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlmodel import select

from src.legajos.domain.estados import EstadoLegajo
from src.legajos.infrastructure import job_vencimiento
from src.legajos.infrastructure.job_vencimiento import (
    ID_TAREA,
    MARGEN_SEGUNDOS,
    correr_vencimiento,
    crear_programador,
    iniciar_programador,
    reservas_aprobadas,
)
from src.legajos.infrastructure.orm_models import AuditoriaLegajoORM
from src.shared.roles import Rol
from tests.fabricas import crear_carrera, crear_cohorte, crear_legajo, crear_usuario

AHORA = datetime(2026, 11, 6, 6, 0, tzinfo=UTC)  # las 3:00 en Argentina
ARGENTINA = ZoneInfo("America/Argentina/Buenos_Aires")


@pytest.fixture
def aprobado(session):
    """Crea un legajo en `estado` (COMPLETADO si no se dice) aprobado hace `dias` días."""
    cohorte, carrera = crear_cohorte(session), crear_carrera(session)

    def crear(dias, numero, estado=EstadoLegajo.COMPLETADO, desde=AHORA):
        return crear_legajo(
            session,
            cohorte,
            [carrera],
            estado=estado,
            numero_legajo=numero,
            fecha_aprobacion=desde - timedelta(days=dias),
        )

    return crear


@pytest.fixture
def sesion_de_la_tarea(session, monkeypatch):
    """La tarea abre su propia sesión con `Session(engine)`: en los tests usa la del test."""
    monkeypatch.setattr(job_vencimiento, "Session", lambda _engine: nullcontext(session))


def _auditoria(session, legajo):
    return session.exec(
        select(AuditoriaLegajoORM).where(AuditoriaLegajoORM.legajo_id == legajo.id)
    ).all()


# --- La consulta ---


def test_trae_los_completados_de_la_aprobacion_mas_vieja_a_la_mas_nueva(session, aprobado):
    nueva = aprobado(5, "26-001-001")
    vieja = aprobado(40, "26-001-002")
    aprobado(40, "26-001-003", estado=EstadoLegajo.ACTIVO)

    reservas = reservas_aprobadas(session)

    assert [reserva.legajo_id for reserva in reservas] == [vieja.id, nueva.id]
    assert reservas[0].fecha_aprobacion == AHORA - timedelta(days=40)


# --- La corrida ---


def test_vence_el_legajo_lo_audita_como_sistema_y_avisa_a_cada_coordinador_activo(
    session, aprobado, bandeja
):
    crear_usuario(session, email="coord1@example.com", rol=Rol.COORDINADOR)
    crear_usuario(session, email="coord2@example.com", rol=Rol.COORDINADOR)
    crear_usuario(session, email="inactivo@example.com", rol=Rol.COORDINADOR, activo=False)
    legajo = aprobado(31, "26-001-007")

    resultado = correr_vencimiento(session, AHORA)

    session.refresh(legajo)
    assert legajo.estado == EstadoLegajo.VENCIDO
    (registro,) = _auditoria(session, legajo)
    assert (
        registro.accion,
        registro.estado_anterior,
        registro.estado_nuevo,
        registro.rol,
        registro.usuario_email,
    ) == ("VENCER", "COMPLETADO", "VENCIDO", "SISTEMA", None)
    assert [email.destinatario for email in bandeja] == ["coord1@example.com", "coord2@example.com"]
    assert {email.plantilla for email in bandeja} == {"vencimiento_coordinador.html"}
    assert bandeja[0].contexto["numero_legajo"] == "26-001-007"
    assert [vencido.numero_legajo for vencido in resultado.vencidos] == ["26-001-007"]


def test_no_toca_los_completados_de_menos_de_30_dias_ni_los_de_otros_estados(
    session, aprobado, bandeja
):
    joven = aprobado(29, "26-001-001")
    activo = aprobado(60, "26-001-002", estado=EstadoLegajo.ACTIVO)

    resultado = correr_vencimiento(session, AHORA)

    session.refresh(joven)
    session.refresh(activo)
    assert (joven.estado, activo.estado) == (EstadoLegajo.COMPLETADO, EstadoLegajo.ACTIVO)
    assert (resultado.revisadas, resultado.vencidos, bandeja) == (1, [], [])


def test_correrla_dos_veces_no_vence_ni_avisa_dos_veces(session, aprobado, bandeja):
    crear_usuario(session, rol=Rol.COORDINADOR)
    legajo = aprobado(31, "26-001-001")

    primera = correr_vencimiento(session, AHORA)
    segunda = correr_vencimiento(session, AHORA + timedelta(days=1))

    assert (len(primera.vencidos), len(segunda.vencidos), segunda.revisadas) == (1, 0, 0)
    assert len(_auditoria(session, legajo)) == 1
    assert len(bandeja) == 1


# --- La tarea diaria y el comando manual ---


def test_la_tarea_diaria_usa_la_hora_actual_y_deja_el_resumen_en_el_log(
    session, aprobado, sesion_de_la_tarea, caplog
):
    aprobado(31, "26-001-009", desde=datetime.now(UTC))
    caplog.set_level(logging.INFO, logger=job_vencimiento.__name__)

    texto = job_vencimiento.tarea_diaria()

    assert texto == "Vencimiento: 1 de 1 legajos COMPLETADO pasaron a VENCIDO (26-001-009)"
    assert texto in caplog.text


def test_el_comando_corre_la_tarea_una_vez_y_muestra_el_resumen(sesion_de_la_tarea, capsys):
    job_vencimiento.main()

    assert capsys.readouterr().out == "Vencimiento: 0 de 0 legajos COMPLETADO pasaron a VENCIDO\n"


# --- Cuándo corre ---


def test_esta_programada_todos_los_dias_a_las_3_de_la_argentina():
    programador = crear_programador()
    programador.start(paused=True)  # en pausa: arma la tarea con su configuración y no corre nada
    try:
        tarea = programador.get_job(ID_TAREA)
        proxima = tarea.trigger.get_next_fire_time
        antes_de_las_3 = datetime(2026, 11, 6, 2, 0, tzinfo=ARGENTINA)
        despues_de_las_3 = datetime(2026, 11, 6, 3, 30, tzinfo=ARGENTINA)

        assert proxima(None, antes_de_las_3) == datetime(2026, 11, 6, 3, 0, tzinfo=ARGENTINA)
        assert proxima(None, despues_de_las_3) == datetime(2026, 11, 7, 3, 0, tzinfo=ARGENTINA)
        assert tarea.func is job_vencimiento.tarea_diaria
        assert (tarea.coalesce, tarea.max_instances, tarea.misfire_grace_time) == (
            True,
            1,
            MARGEN_SEGUNDOS,
        )
    finally:
        programador.shutdown()


def test_iniciar_programador_lo_deja_corriendo_hasta_que_se_frena():
    programador = iniciar_programador()
    try:
        assert programador.running
    finally:
        programador.shutdown()

    assert not programador.running
