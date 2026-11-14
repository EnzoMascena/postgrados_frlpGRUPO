"""`GET /legajos` y `GET /legajos/resumen` contra la app real y la base de test.

El detalle del filtrado SQL está en `test_pg_repository_busqueda.py`; acá, el contrato del plan
§10 de punta a punta: query params, JSON en camelCase, errores y permisos.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.gestion_documental.domain.tipos import TipoDocumento
from src.gestion_documental.infrastructure.orm_models import DocumentoORM
from src.legajos.application.buscar_legajos import MENSAJE_APELLIDO_CORTO
from src.legajos.domain.estados import EstadoLegajo
from tests.fabricas import crear_carrera, crear_cohorte, crear_legajo

LISTADO = "/api/v1/legajos"
RESUMEN = "/api/v1/legajos/resumen"
AHORA = datetime(2026, 11, 4, 12, 0, tzinfo=UTC)
CLAVES_DE_ERROR = {"statusCode", "error", "message", "field", "timestamp"}
CLAVES_DE_FILA = {
    "id",
    "codigoSeguimiento",
    "numeroLegajo",
    "apellido",
    "nombre",
    "dni",
    "email",
    "estado",
    "cohorte",
    "carreras",
    "solicitaBeca",
    "tipoBeca",
    "documentosCargados",
    "documentosRequeridos",
    "fechaInscripcion",
}


@pytest.fixture
def cohorte(session):
    return crear_cohorte(session, anio=2026, numero=1, nombre="Cohorte 2026")


@pytest.fixture
def carrera(session):
    return crear_carrera(session, nombre="Maestría en Tecnología Informática")


def _legajo(session, cohorte, carreras, minutos: int = 0, **campos):
    return crear_legajo(
        session, cohorte, carreras, created_at=AHORA - timedelta(minutes=minutos), **campos
    )


def _subir_documento(session, legajo, tipo: TipoDocumento) -> None:
    session.add(
        DocumentoORM(
            legajo_id=legajo.id,
            tipo=tipo.value,
            path_storage=f"uploads/{legajo.cohorte_id}/{legajo.id}/{uuid4()}.pdf",
            nombre_original=f"{tipo.value.lower()}.pdf",
            checksum_sha256="0" * 64,
            tamanio_bytes=183_412,
        )
    )
    session.commit()


def _ids(respuesta) -> list[str]:
    return [fila["id"] for fila in respuesta.json()["items"]]


# --- GET /legajos: el cuerpo ---


def test_listado_con_el_cuerpo_del_plan(client, session, headers_coordinador, cohorte, carrera):
    legajo = _legajo(
        session,
        cohorte,
        [carrera],
        apellido="Rodríguez",
        nombre="Ana Laura",
        dni="28456789",
        email="ana.rodriguez@example.com",
        estado=EstadoLegajo.PENDIENTE,
        solicita_beca=True,
        tipo_beca="30",
        fecha_inscripcion=datetime(2026, 11, 3, 14, 20, tzinfo=UTC),
    )
    for tipo in TipoDocumento:
        if tipo != TipoDocumento.TITULO_POSGRADO:
            _subir_documento(session, legajo, tipo)

    respuesta = client.get(LISTADO, headers=headers_coordinador)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert (cuerpo["total"], cuerpo["page"], cuerpo["size"]) == (1, 1, 20)
    [fila] = cuerpo["items"]
    assert set(fila) == CLAVES_DE_FILA
    assert fila == {
        "id": str(legajo.id),
        "codigoSeguimiento": legajo.codigo_seguimiento,
        "numeroLegajo": None,
        "apellido": "Rodríguez",
        "nombre": "Ana Laura",
        "dni": "28456789",
        "email": "ana.rodriguez@example.com",
        "estado": "PENDIENTE",
        "cohorte": "Cohorte 2026",
        "carreras": ["Maestría en Tecnología Informática"],
        "solicitaBeca": True,
        "tipoBeca": "30",
        "documentosCargados": 6,
        "documentosRequeridos": 6,
        "fechaInscripcion": "2026-11-03T14:20:00Z",
    }


def test_listado_vacio(client, headers_coordinador):
    respuesta = client.get(LISTADO, headers=headers_coordinador)

    assert respuesta.status_code == 200
    assert respuesta.json() == {"items": [], "total": 0, "page": 1, "size": 20}


# --- GET /legajos: q ---


def test_q_con_digitos_busca_dni_exacto(client, session, headers_coordinador, cohorte, carrera):
    buscado = _legajo(session, cohorte, [carrera], dni="28456789")
    _legajo(session, cohorte, [carrera], dni="284567890")

    respuesta = client.get(LISTADO, params={"q": "28456789"}, headers=headers_coordinador)

    assert _ids(respuesta) == [str(buscado.id)]


@pytest.mark.parametrize("q", ["rodr", "RODR", "Rodríguez", "ríguez", "rodriguez", "RODRIGUEZ"])
def test_q_con_letras_busca_apellido_parcial(
    client, session, headers_coordinador, cohorte, carrera, q
):
    buscado = _legajo(session, cohorte, [carrera], apellido="Rodríguez")
    _legajo(session, cohorte, [carrera], apellido="González")

    respuesta = client.get(LISTADO, params={"q": q}, headers=headers_coordinador)

    assert _ids(respuesta) == [str(buscado.id)]


@pytest.mark.parametrize("q", ["ro", "a", " ab "])
def test_q_con_menos_de_3_letras_da_422(client, headers_coordinador, q):
    respuesta = client.get(LISTADO, params={"q": q}, headers=headers_coordinador)

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert set(cuerpo) == CLAVES_DE_ERROR
    assert cuerpo["error"] == "VALIDATION_ERROR"
    assert cuerpo["message"] == MENSAJE_APELLIDO_CORTO
    assert cuerpo["field"] == "q"


def test_q_con_comodines_no_trae_todos(client, session, headers_coordinador, cohorte, carrera):
    _legajo(session, cohorte, [carrera], apellido="Rodríguez")

    respuesta = client.get(LISTADO, params={"q": "%%%"}, headers=headers_coordinador)

    assert respuesta.status_code == 200
    assert respuesta.json()["total"] == 0


# --- GET /legajos: cada filtro solo y combinados ---


def test_filtro_por_estado(client, session, headers_coordinador, cohorte, carrera):
    buscado = _legajo(session, cohorte, [carrera], estado=EstadoLegajo.EN_REVISION)
    _legajo(session, cohorte, [carrera], estado=EstadoLegajo.PENDIENTE)

    respuesta = client.get(LISTADO, params={"estado": "EN_REVISION"}, headers=headers_coordinador)

    assert _ids(respuesta) == [str(buscado.id)]


def test_filtro_por_cohorte(client, session, headers_coordinador, cohorte, carrera):
    otra = crear_cohorte(session, anio=2025, numero=1, nombre="Cohorte 2025")
    buscado = _legajo(session, otra, [carrera])
    _legajo(session, cohorte, [carrera])

    respuesta = client.get(LISTADO, params={"cohorte": str(otra.id)}, headers=headers_coordinador)

    assert _ids(respuesta) == [str(buscado.id)]


def test_filtro_por_carrera(client, session, headers_coordinador, cohorte, carrera):
    otra = crear_carrera(session, nombre="Doctorado en Ingeniería")
    buscado = _legajo(session, cohorte, [otra, carrera])
    _legajo(session, cohorte, [otra])

    respuesta = client.get(
        LISTADO, params={"carrera": str(carrera.id)}, headers=headers_coordinador
    )

    assert _ids(respuesta) == [str(buscado.id)]


@pytest.mark.parametrize(("beca", "con_beca"), [("true", True), ("false", False)])
def test_filtro_por_beca(client, session, headers_coordinador, cohorte, carrera, beca, con_beca):
    pidio = _legajo(session, cohorte, [carrera], solicita_beca=True, tipo_beca="100")
    no_pidio = _legajo(session, cohorte, [carrera])

    respuesta = client.get(LISTADO, params={"beca": beca}, headers=headers_coordinador)

    assert _ids(respuesta) == [str(pidio.id if con_beca else no_pidio.id)]


def test_filtros_combinados(client, session, headers_coordinador, cohorte, carrera):
    otra_carrera = crear_carrera(session, nombre="Doctorado en Ingeniería")
    datos = {"apellido": "González", "estado": EstadoLegajo.PENDIENTE}
    beca = {"solicita_beca": True, "tipo_beca": "30"}
    buscado = _legajo(session, cohorte, [carrera], **datos, **beca)
    _legajo(session, cohorte, [carrera], **datos)  # sin beca
    _legajo(session, cohorte, [otra_carrera], **datos, **beca)  # otra carrera
    _legajo(session, cohorte, [carrera], **{**datos, "estado": EstadoLegajo.ACTIVO}, **beca)

    respuesta = client.get(
        LISTADO,
        params={
            "q": "gonz",
            "estado": "PENDIENTE",
            "cohorte": str(cohorte.id),
            "carrera": str(carrera.id),
            "beca": "true",
        },
        headers=headers_coordinador,
    )

    assert _ids(respuesta) == [str(buscado.id)]
    assert respuesta.json()["total"] == 1


# --- GET /legajos: páginas y orden ---


def test_paginas_con_total_page_y_size(client, session, headers_coordinador, cohorte, carrera):
    legajos = [_legajo(session, cohorte, [carrera], minutos=m) for m in range(5)]

    primera = client.get(LISTADO, params={"size": 2}, headers=headers_coordinador)
    tercera = client.get(LISTADO, params={"page": 3, "size": 2}, headers=headers_coordinador)
    fuera = client.get(LISTADO, params={"page": 4, "size": 2}, headers=headers_coordinador)

    assert _ids(primera) == [str(legajos[0].id), str(legajos[1].id)]
    assert {k: primera.json()[k] for k in ("total", "page", "size")} == {
        "total": 5,
        "page": 1,
        "size": 2,
    }
    assert _ids(tercera) == [str(legajos[4].id)]
    assert tercera.json()["page"] == 3
    assert fuera.json()["items"] == [] and fuera.json()["total"] == 5


def test_los_mas_nuevos_primero(client, session, headers_coordinador, cohorte, carrera):
    viejo = _legajo(session, cohorte, [carrera], minutos=60)
    nuevo = _legajo(session, cohorte, [carrera], minutos=1)

    respuesta = client.get(LISTADO, headers=headers_coordinador)

    assert _ids(respuesta) == [str(nuevo.id), str(viejo.id)]


@pytest.mark.parametrize(
    ("params", "campo"),
    [
        ({"page": 0}, "page"),
        ({"size": 0}, "size"),
        ({"size": 101}, "size"),
        ({"estado": "INEXISTENTE"}, "estado"),
        ({"cohorte": "no-es-uuid"}, "cohorte"),
        ({"carrera": "no-es-uuid"}, "carrera"),
        ({"beca": "quizas"}, "beca"),
    ],
)
def test_parametros_invalidos_dan_422_con_el_campo(client, headers_coordinador, params, campo):
    respuesta = client.get(LISTADO, params=params, headers=headers_coordinador)

    assert respuesta.status_code == 422
    assert set(respuesta.json()) == CLAVES_DE_ERROR
    assert respuesta.json()["field"] == campo


def test_size_100_es_el_maximo_permitido(client, headers_coordinador):
    respuesta = client.get(LISTADO, params={"size": 100}, headers=headers_coordinador)

    assert respuesta.status_code == 200
    assert respuesta.json()["size"] == 100


# --- GET /legajos/resumen ---


def test_resumen_con_conteos_correctos(client, session, headers_coordinador, cohorte, carrera):
    for estado in [EstadoLegajo.PENDIENTE] * 3 + [EstadoLegajo.ACTIVO, EstadoLegajo.BORRADOR]:
        _legajo(session, cohorte, [carrera], estado=estado)
    _legajo(
        session,
        cohorte,
        [carrera],
        estado=EstadoLegajo.EN_REVISION,
        solicita_beca=True,
        tipo_beca="30",
    )
    _legajo(
        session,
        cohorte,
        [carrera],
        estado=EstadoLegajo.COMPLETADO,
        solicita_beca=True,
        tipo_beca="100",
    )
    _legajo(
        session,
        cohorte,
        [carrera],
        estado=EstadoLegajo.COMPLETADO,
        solicita_beca=True,
        tipo_beca="100",
    )

    respuesta = client.get(RESUMEN, headers=headers_coordinador)

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "total": 8,
        "porEstado": {
            "BORRADOR": 1,
            "PENDIENTE": 3,
            "EN_REVISION": 1,
            "OBSERVADO": 0,
            "COMPLETADO": 2,
            "ACTIVO": 1,
            "VENCIDO": 0,
            "RECHAZADO": 0,
            "BAJA": 0,
            "GRADUADO": 0,
        },
        "conBeca": 3,
        "beca30": 1,
        "beca100": 2,
    }


def test_resumen_sin_legajos_trae_los_10_estados_en_cero(client, headers_coordinador):
    cuerpo = client.get(RESUMEN, headers=headers_coordinador).json()

    assert cuerpo["total"] == 0
    assert cuerpo["porEstado"] == {estado.value: 0 for estado in EstadoLegajo}
    assert (cuerpo["conBeca"], cuerpo["beca30"], cuerpo["beca100"]) == (0, 0, 0)


def test_resumen_filtra_por_cohorte(client, session, headers_coordinador, cohorte, carrera):
    otra = crear_cohorte(session, anio=2025, numero=1, nombre="Cohorte 2025")
    _legajo(session, cohorte, [carrera], estado=EstadoLegajo.PENDIENTE)
    _legajo(
        session, otra, [carrera], estado=EstadoLegajo.ACTIVO, solicita_beca=True, tipo_beca="30"
    )

    de_una = client.get(RESUMEN, params={"cohorte": str(cohorte.id)}, headers=headers_coordinador)
    de_todas = client.get(RESUMEN, headers=headers_coordinador)

    assert de_una.json()["total"] == 1
    assert de_una.json()["porEstado"]["PENDIENTE"] == 1
    assert de_una.json()["porEstado"]["ACTIVO"] == 0
    assert de_una.json()["conBeca"] == 0
    assert de_todas.json()["total"] == 2
    assert de_todas.json()["conBeca"] == 1


def test_resumen_no_se_confunde_con_un_legajo_id(client, headers_coordinador):
    # Si `/{legajo_id}` estuviera declarada antes, "resumen" se leería como UUID y daría 422.
    respuesta = client.get(RESUMEN, headers=headers_coordinador)

    assert respuesta.status_code == 200
    assert "porEstado" in respuesta.json()


# --- Permisos ---


@pytest.mark.parametrize("url", [LISTADO, RESUMEN])
def test_sin_token_da_401(client, url):
    respuesta = client.get(url)

    assert respuesta.status_code == 401
    assert set(respuesta.json()) == CLAVES_DE_ERROR
    assert respuesta.json()["error"] == "UNAUTHORIZED"


@pytest.mark.parametrize("url", [LISTADO, RESUMEN])
def test_con_un_token_invalido_da_401(client, url):
    respuesta = client.get(url, headers={"Authorization": "Bearer no-es-un-jwt"})

    assert respuesta.status_code == 401


@pytest.mark.parametrize("url", [LISTADO, RESUMEN])
def test_con_un_docente_da_403(client, headers_docente, url):
    respuesta = client.get(url, headers=headers_docente)

    assert respuesta.status_code == 403
    assert respuesta.json()["error"] == "FORBIDDEN"


def test_el_permiso_se_controla_antes_que_los_parametros(client, headers_docente):
    # Un docente con un `q` inválido recibe 403, no 422: no se le dice nada de la búsqueda.
    respuesta = client.get(LISTADO, params={"q": "ab"}, headers=headers_docente)

    assert respuesta.status_code == 403


# --- Swagger ---


def test_los_endpoints_aparecen_en_swagger(client):
    rutas = client.get("/api/openapi.json").json()["paths"]

    listado = rutas["/api/v1/legajos"]["get"]
    assert listado["tags"] == ["Legajos"]
    assert {"200", "401", "403", "422"} <= set(listado["responses"])
    assert {"q", "estado", "cohorte", "carrera", "beca", "page", "size"} <= {
        p["name"] for p in listado["parameters"]
    }
    resumen = rutas["/api/v1/legajos/resumen"]["get"]
    assert {"200", "401", "403"} <= set(resumen["responses"])
    # POST /legajos de Fran sigue en la misma ruta, con su propio tag.
    assert "post" in rutas["/api/v1/legajos"]
