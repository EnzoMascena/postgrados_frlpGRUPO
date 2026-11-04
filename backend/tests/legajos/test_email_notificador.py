"""`EmailNotificadorLegajos` con las plantillas de verdad: los emails quedan en la `bandeja`.

Se usa `enviar_email` real (no uno falso) a propósito: las plantillas tienen `StrictUndefined`,
así que si falta una variable del plan §11 el render falla y el test también.
"""

from datetime import UTC, datetime

import pytest

from src.autenticacion.infrastructure.pg_repository import PgUsuarioRepository
from src.legajos.domain.estados import Accion, EstadoLegajo
from src.legajos.infrastructure.email_notificador import EmailNotificadorLegajos, fecha_para_email
from src.legajos.infrastructure.pg_repository import PgLegajoRepository
from src.shared.roles import Rol
from tests.fabricas import crear_carrera, crear_cohorte, crear_legajo, crear_usuario

# 3/11 a las 01:30 UTC son las 22:30 del 2/11 en Argentina.
APROBADO = datetime(2026, 11, 3, 1, 30, tzinfo=UTC)


@pytest.fixture
def repo(session) -> PgLegajoRepository:
    return PgLegajoRepository(session)


@pytest.fixture
def notificador(session, repo) -> EmailNotificadorLegajos:
    return EmailNotificadorLegajos(repo, PgUsuarioRepository(session))


@pytest.fixture
def legajo(session, repo):
    cohorte = crear_cohorte(session, nombre="Cohorte 2026")
    carreras = [
        crear_carrera(session, nombre="Maestría en Tecnología Informática"),
        crear_carrera(session, nombre="Especialización en Ingeniería Gerencial"),
    ]
    fila = crear_legajo(
        session,
        cohorte,
        carreras,
        estado=EstadoLegajo.COMPLETADO,
        nombre="Ana Laura",
        apellido="Rodríguez",
        email="ana@example.com",
        numero_legajo="26-001-001",
        fecha_aprobacion=APROBADO,
        codigo_seguimiento="7F3A9C21",
    )
    return repo.obtener(fila.id)


CARRERAS = ["Maestría en Tecnología Informática", "Especialización en Ingeniería Gerencial"]


@pytest.mark.parametrize(
    ("accion", "es_correccion"), [(Accion.ENVIAR, False), (Accion.CORREGIR, True)]
)
def test_enviar_y_corregir_mandan_la_confirmacion(
    notificador, legajo, bandeja, accion, es_correccion
):
    notificador.notificar(legajo, accion, None)

    [email] = bandeja
    assert (email.destinatario, email.asunto, email.plantilla) == (
        "ana@example.com",
        "Recibimos tu preinscripción",
        "confirmacion_envio.html",
    )
    assert email.contexto == {
        "nombre": "Ana Laura",
        "codigo_seguimiento": "7F3A9C21",
        "carreras": CARRERAS,
        "cohorte": "Cohorte 2026",
        "es_correccion": es_correccion,
    }


def test_observar_manda_el_comentario_y_el_link_para_recuperar_el_acceso(
    notificador, legajo, bandeja, monkeypatch
):
    monkeypatch.setattr("src.shared.config.settings.frontend_url", "http://localhost:3000/")

    notificador.notificar(legajo, Accion.OBSERVAR, "Falta la copia del título legalizada")

    [email] = bandeja
    assert (email.destinatario, email.plantilla) == ("ana@example.com", "observacion.html")
    assert email.contexto == {
        "nombre": "Ana Laura",
        "comentario": "Falta la copia del título legalizada",
        "link_recuperar": "http://localhost:3000/inscripcion?recuperar=1",
    }
    assert "Falta la copia del título legalizada" in email.html


def test_aprobar_manda_el_numero_y_la_fecha_limite_en_hora_argentina(notificador, legajo, bandeja):
    notificador.notificar(legajo, Accion.APROBAR, None)

    [email] = bandeja
    assert (email.asunto, email.plantilla) == ("Tu legajo fue aprobado", "aprobacion.html")
    # Aprobado el 2/11 a las 22:30 de Argentina: vence 30 días después, el 2/12.
    assert email.contexto == {
        "nombre": "Ana Laura",
        "numero_legajo": "26-001-001",
        "carreras": CARRERAS,
        "fecha_limite": "02/12/2026",
    }
    assert "26-001-001" in email.html


@pytest.mark.parametrize(
    ("comentario", "esperado"),
    [("No cumple los requisitos de admisión", "No cumple los requisitos de admisión"), (None, "")],
)
def test_rechazar_manda_el_rechazo_con_o_sin_comentario(
    notificador, legajo, bandeja, comentario, esperado
):
    notificador.notificar(legajo, Accion.RECHAZAR, comentario)

    [email] = bandeja
    assert (email.asunto, email.plantilla) == ("Resultado de tu preinscripción", "rechazo.html")
    assert email.contexto == {"nombre": "Ana Laura", "comentario": esperado}


def test_vencer_avisa_a_cada_coordinador_activo(session, notificador, legajo, bandeja):
    crear_usuario(session, email="coord1@example.com", rol=Rol.COORDINADOR)
    crear_usuario(session, email="coord2@example.com", rol=Rol.COORDINADOR)
    crear_usuario(session, email="inactivo@example.com", rol=Rol.COORDINADOR, activo=False)
    crear_usuario(session, email="docente@example.com", rol=Rol.DOCENTE)

    notificador.notificar(legajo, Accion.VENCER, None)

    assert [email.destinatario for email in bandeja] == ["coord1@example.com", "coord2@example.com"]
    for email in bandeja:
        assert (email.asunto, email.plantilla) == (
            "Venció una reserva de vacante",
            "vencimiento_coordinador.html",
        )
        assert email.contexto == {
            "apellido": "Rodríguez",
            "nombre": "Ana Laura",
            "numero_legajo": "26-001-001",
            "fecha_aprobacion": "02/11/2026",
        }


@pytest.mark.parametrize(
    "accion", [Accion.REVISAR, Accion.MATRICULAR, Accion.DAR_DE_BAJA, Accion.GRADUAR]
)
def test_las_acciones_sin_email_no_mandan_nada(notificador, legajo, bandeja, accion):
    notificador.notificar(legajo, accion, None)

    assert bandeja == []


def test_aprobar_sin_fecha_de_aprobacion_es_un_error_de_programacion(notificador, legajo):
    legajo.fecha_aprobacion = None

    with pytest.raises(ValueError, match="fecha de aprobación"):
        notificador.notificar(legajo, Accion.APROBAR, None)


def test_fecha_para_email_pasa_de_utc_a_la_hora_argentina():
    assert fecha_para_email(datetime(2026, 11, 3, 2, 59, tzinfo=UTC)) == "02/11/2026"
    assert fecha_para_email(datetime(2026, 11, 3, 3, 0, tzinfo=UTC)) == "03/11/2026"
