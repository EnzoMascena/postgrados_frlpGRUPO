"""`POST /legajos`, `POST /legajos/recuperar-acceso` y el link de seguimiento, contra la app real
y la base de test."""

import hashlib
import re
from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlmodel import select

from src.inscripcion.domain.inscripcion import (
    MENSAJE_DNI_REPETIDO,
    MENSAJE_EMAIL_REPETIDO,
    DatosInscripcion,
)
from src.inscripcion.infrastructure.links import crear_link_seguimiento
from src.inscripcion.infrastructure.orm_models import TokenSeguimientoORM
from src.inscripcion.infrastructure.pg_repository import PgInscripcionRepository
from src.inscripcion.presentation.dependencies import legajo_id_desde_token
from src.inscripcion.presentation.schemas import InscripcionRequest
from src.legajos.infrastructure.orm_models import LegajoCarreraORM, LegajoORM
from src.shared.config import settings
from src.shared.errors import Conflicto, NoEncontrado
from src.shared.orm import ahora_utc
from tests.fabricas import crear_carrera, crear_cohorte, crear_legajo

LEGAJOS = "/api/v1/legajos"
RECUPERAR = "/api/v1/legajos/recuperar-acceso"


@pytest.fixture
def cohorte(session):
    return crear_cohorte(session)


@pytest.fixture
def carrera(session):
    return crear_carrera(session)


@pytest.fixture
def formulario(cohorte, carrera) -> dict:
    return {
        "cohorteId": str(cohorte.id),
        "carreraIds": [str(carrera.id)],
        "apellido": "Rodríguez",
        "nombre": "Ana Laura",
        "nacionalidad": "Argentina",
        "dni": "28.456.789",
        "telefonoMovil": "+54 221 4567890",
        "telefonoFijo": None,
        "email": "Ana.Rodriguez@Example.com",
        "emailAlternativo": None,
        "domicilio": "Av. 7 Nro. 1234",
        "ciudad": "La Plata",
        "provincia": "Buenos Aires",
        "pais": "Argentina",
        "tituloGrado": "Ingeniería en Sistemas de Información",
        "tituloPosgrado": None,
        "comoConocio": "EGRESADOS",
        "motivacion": "Quiero profundizar en gestión de sistemas para aplicarlo en mi trabajo.",
        "solicitaBeca": True,
        "tipoBeca": "30",
    }


def legajos_guardados(session) -> list[LegajoORM]:
    return list(session.exec(select(LegajoORM)))


# --- POST /legajos ---


def test_inscribirse_da_201_con_el_cuerpo_del_plan(client, formulario):
    respuesta = client.post(LEGAJOS, json=formulario)

    cuerpo = respuesta.json()
    assert respuesta.status_code == 201
    assert set(cuerpo) == {"legajoId", "codigoSeguimiento", "token", "estado"}
    assert cuerpo["estado"] == "BORRADOR"
    assert re.fullmatch(r"[0-9A-F]{8}", cuerpo["codigoSeguimiento"])


def test_el_legajo_queda_guardado_normalizado_y_con_sus_carreras(
    client, session, formulario, carrera
):
    otra = crear_carrera(session)
    formulario["carreraIds"] = [str(otra.id), str(carrera.id)]

    cuerpo = client.post(LEGAJOS, json=formulario).json()

    legajo = session.get(LegajoORM, cuerpo["legajoId"])
    assert legajo.estado == "BORRADOR"
    assert legajo.dni == "28456789"
    assert legajo.email == "ana.rodriguez@example.com"
    assert legajo.codigo_seguimiento == cuerpo["codigoSeguimiento"]
    assert (legajo.solicita_beca, legajo.tipo_beca) == (True, "30")
    carreras = session.exec(
        select(LegajoCarreraORM).where(LegajoCarreraORM.legajo_id == legajo.id)
    ).all()
    assert sorted((c.orden, c.carrera_id) for c in carreras) == [(1, otra.id), (2, carrera.id)]


def test_el_token_se_guarda_hasheado_y_vence_a_los_60_dias(client, session, formulario):
    cuerpo = client.post(LEGAJOS, json=formulario).json()

    fila = session.exec(select(TokenSeguimientoORM)).one()
    assert fila.token_hash == hashlib.sha256(cuerpo["token"].encode()).hexdigest()
    assert fila.token_hash != cuerpo["token"]
    dias = (fila.expira_en - ahora_utc()) / timedelta(days=1)
    assert 59.99 < dias <= 60


def test_inscribirse_manda_el_email_con_el_link(client, formulario, bandeja):
    cuerpo = client.post(LEGAJOS, json=formulario).json()

    assert len(bandeja) == 1
    email = bandeja[0]
    assert email.destinatario == "ana.rodriguez@example.com"
    assert email.plantilla == "link_seguimiento.html"
    assert email.asunto == "Tu preinscripción al Posgrado UTN FRLP"
    assert email.contexto == {
        "nombre": "Ana Laura",
        "codigo_seguimiento": cuerpo["codigoSeguimiento"],
        "link": f"{settings.frontend_url}/seguimiento/{cuerpo['token']}",
    }


def test_con_el_periodo_cerrado_da_409_y_no_guarda_nada(client, session, formulario, cohorte):
    cohorte.inscripcion_abierta = False
    cohorte.proxima_apertura = date(2027, 3, 1)
    session.commit()

    respuesta = client.post(LEGAJOS, json=formulario)

    assert respuesta.status_code == 409
    assert respuesta.json()["error"] == "PERIODO_CERRADO"
    assert respuesta.json()["message"] == (
        "La inscripción está cerrada. Próxima apertura: 01/03/2027"
    )
    assert legajos_guardados(session) == []


@pytest.mark.parametrize(
    ("cambio", "campo", "mensaje"),
    [
        ({"email": "otra@example.com", "dni": "28456789"}, "dni", MENSAJE_DNI_REPETIDO),
        (
            {"dni": "30111222", "email": "ANA.RODRIGUEZ@example.com"},
            "email",
            MENSAJE_EMAIL_REPETIDO,
        ),
    ],
)
def test_un_dni_o_email_repetido_en_la_cohorte_da_409_con_el_campo(
    client, formulario, cambio, campo, mensaje
):
    client.post(LEGAJOS, json=formulario)

    respuesta = client.post(LEGAJOS, json={**formulario, **cambio})

    assert respuesta.status_code == 409
    assert respuesta.json()["error"] == "CONFLICT"
    assert (respuesta.json()["field"], respuesta.json()["message"]) == (campo, mensaje)


def test_el_mismo_dni_en_otra_cohorte_se_acepta(client, session, formulario):
    client.post(LEGAJOS, json=formulario)
    otra_cohorte = crear_cohorte(session, anio=2027)

    respuesta = client.post(LEGAJOS, json={**formulario, "cohorteId": str(otra_cohorte.id)})

    assert respuesta.status_code == 201


@pytest.mark.parametrize("en_blanco", ["", "   "])
def test_un_opcional_en_blanco_se_guarda_como_none(client, session, formulario, en_blanco):
    # Si el título de posgrado quedara como "", el envío y el detalle le pedirían su copia.
    opcionales = {"telefonoFijo": en_blanco, "emailAlternativo": en_blanco}
    opcionales["tituloPosgrado"] = en_blanco

    cuerpo = client.post(LEGAJOS, json={**formulario, **opcionales}).json()

    legajo = session.get(LegajoORM, cuerpo["legajoId"])
    assert (legajo.telefono_fijo, legajo.email_alternativo, legajo.titulo_posgrado) == (
        None,
        None,
        None,
    )


@pytest.mark.parametrize(
    ("cambio", "campo"),
    [
        ({"cohorteId": str(uuid4())}, "cohorteId"),
        ({"carreraIds": [str(uuid4())]}, "carreraIds"),
        ({"carreraIds": []}, "carreraIds"),
        ({"carreraIds": [str(uuid4()), str(uuid4()), str(uuid4())]}, "carreraIds"),
        ({"dni": "123456"}, "dni"),
        ({"dni": "28-456-789"}, "dni"),
        ({"email": "no-es-un-email"}, "email"),
        ({"emailAlternativo": "tampoco"}, "emailAlternativo"),
        ({"telefonoMovil": ""}, "telefonoMovil"),
        ({"telefonoMovil": "a"}, "telefonoMovil"),
        ({"telefonoMovil": "1234567"}, "telefonoMovil"),
        ({"telefonoMovil": "221 456 789a"}, "telefonoMovil"),
        ({"telefonoFijo": "abc"}, "telefonoFijo"),
        ({"motivacion": "Muy corta"}, "motivacion"),
        ({"comoConocio": "TELEVISION"}, "comoConocio"),
        ({"solicitaBeca": True, "tipoBeca": None}, "tipoBeca"),
        ({"solicitaBeca": False, "tipoBeca": "30"}, "tipoBeca"),
        ({"tipoBeca": "50"}, "tipoBeca"),
    ],
)
def test_un_campo_que_no_cumple_su_regla_da_422_con_el_campo(
    client, session, formulario, cambio, campo
):
    respuesta = client.post(LEGAJOS, json={**formulario, **cambio})

    assert respuesta.status_code == 422
    assert respuesta.json()["error"] == "VALIDATION_ERROR"
    assert respuesta.json()["field"] == campo
    assert legajos_guardados(session) == []


@pytest.mark.parametrize("telefono", ["+54 221 4567890", "(0221) 456-7890", "22145678"])
def test_un_telefono_con_8_numeros_o_mas_se_acepta_con_el_formato_que_sea(
    client, formulario, telefono
):
    cambio = {"telefonoMovil": telefono, "telefonoFijo": telefono}

    respuesta = client.post(LEGAJOS, json={**formulario, **cambio})

    assert respuesta.status_code == 201


def test_una_carrera_inactiva_da_422(client, session, formulario):
    inactiva = crear_carrera(session, activa=False)

    respuesta = client.post(LEGAJOS, json={**formulario, "carreraIds": [str(inactiva.id)]})

    assert (respuesta.status_code, respuesta.json()["field"]) == (422, "carreraIds")


def test_la_misma_carrera_dos_veces_da_422(client, formulario, carrera):
    respuesta = client.post(LEGAJOS, json={**formulario, "carreraIds": [str(carrera.id)] * 2})

    assert (respuesta.status_code, respuesta.json()["field"]) == (422, "carreraIds")


def test_si_la_base_frena_un_dni_repetido_se_responde_el_mismo_409(session, cohorte, carrera):
    # Dos envíos al mismo tiempo: el segundo pasó el control previo y lo frena la base.
    crear_legajo(session, cohorte, [carrera], dni="28456789")
    formulario = InscripcionRequest.model_validate(
        {
            "cohorteId": str(cohorte.id),
            "carreraIds": [str(carrera.id)],
            "apellido": "Rodríguez",
            "nombre": "Ana",
            "nacionalidad": "Argentina",
            "dni": "28456789",
            "telefonoMovil": "221 4567890",
            "email": "nueva@example.com",
            "domicilio": "Calle 1",
            "ciudad": "La Plata",
            "provincia": "Buenos Aires",
            "pais": "Argentina",
            "tituloGrado": "Ingeniería",
            "comoConocio": "OTROS",
            "motivacion": "x" * 50,
            "solicitaBeca": False,
        }
    )
    datos: DatosInscripcion = formulario.a_datos()

    with pytest.raises(Conflicto) as error:
        PgInscripcionRepository(session).crear_legajo(datos, "ABCD1234")

    assert (error.value.campo, error.value.mensaje) == ("dni", MENSAJE_DNI_REPETIDO)


# --- POST /legajos/recuperar-acceso ---


def test_recuperar_acceso_manda_un_link_nuevo_que_sirve(client, session, formulario, bandeja):
    client.post(LEGAJOS, json=formulario)
    bandeja.clear()

    respuesta = client.post(RECUPERAR, json={"email": "  ANA.rodriguez@example.com "})

    assert respuesta.status_code == 202
    assert respuesta.json() == {
        "mensaje": "Si hay una preinscripción con ese email, te enviamos un link para continuar."
    }
    assert len(bandeja) == 1
    token = bandeja[0].contexto["link"].rsplit("/", 1)[1]
    legajo = legajos_guardados(session)[0]
    assert legajo_id_desde_token(token, session) == legajo.id
    assert len(session.exec(select(TokenSeguimientoORM)).all()) == 2


def test_recuperar_acceso_usa_el_legajo_mas_reciente(client, session, formulario, bandeja):
    client.post(LEGAJOS, json=formulario)
    otra_cohorte = crear_cohorte(session, anio=2027)
    nuevo = client.post(LEGAJOS, json={**formulario, "cohorteId": str(otra_cohorte.id)}).json()
    bandeja.clear()

    client.post(RECUPERAR, json={"email": "ana.rodriguez@example.com"})

    assert bandeja[0].contexto["codigo_seguimiento"] == nuevo["codigoSeguimiento"]


def test_recuperar_acceso_sin_legajo_responde_lo_mismo_y_no_manda_nada(client, bandeja):
    respuesta = client.post(RECUPERAR, json={"email": "nadie@example.com"})

    assert respuesta.status_code == 202
    assert respuesta.json()["mensaje"].startswith("Si hay una preinscripción con ese email")
    assert bandeja == []


def test_recuperar_acceso_con_un_email_invalido_da_422(client):
    respuesta = client.post(RECUPERAR, json={"email": "no-es-un-email"})

    assert (respuesta.status_code, respuesta.json()["field"]) == (422, "email")


# --- link de seguimiento ---


def test_un_token_valido_lleva_a_su_legajo(session, cohorte, carrera):
    legajo = crear_legajo(session, cohorte, [carrera])

    token = crear_link_seguimiento(session, legajo.id)

    assert legajo_id_desde_token(token, session) == legajo.id


def test_un_token_que_no_existe_da_404(session):
    with pytest.raises(NoEncontrado):
        legajo_id_desde_token("token-inventado", session)


def test_un_token_vencido_da_404(session, cohorte, carrera):
    legajo = crear_legajo(session, cohorte, [carrera])
    token = crear_link_seguimiento(session, legajo.id)
    fila = session.exec(select(TokenSeguimientoORM)).one()
    fila.expira_en = ahora_utc() - timedelta(seconds=1)
    session.commit()

    with pytest.raises(NoEncontrado):
        legajo_id_desde_token(token, session)


# --- Swagger ---


def test_swagger_aclara_de_donde_salen_los_ids_y_da_los_dos_ejemplos_de_409(client):
    documentacion = client.get("/api/openapi.json").json()["paths"][LEGAJOS]["post"]

    assert "GET /cohortes" in documentacion["description"]
    assert "GET /carreras" in documentacion["description"]
    ejemplos = documentacion["responses"]["409"]["content"]["application/json"]["examples"]
    assert {ejemplo["value"]["error"] for ejemplo in ejemplos.values()} == {
        "CONFLICT",
        "PERIODO_CERRADO",
    }
