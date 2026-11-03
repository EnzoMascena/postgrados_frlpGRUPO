"""Cómo viaja un error del dominio al JSON que ve el front (formato de ARQUITECTURA §11.2).

No usan la app real ni la base: arman una app mínima con los mismos manejadores de errores.
"""

import re

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from src.shared.error_handlers import MENSAJES_HTTP, registrar_manejadores_de_errores
from src.shared.errors import (
    Conflicto,
    ErrorDeNegocio,
    ErrorDeValidacion,
    NoAutenticado,
    NoEncontrado,
    SinPermiso,
)
from src.shared.schemas import CamelModel

CLAVES = {"statusCode", "error", "message", "field", "timestamp"}
TIMESTAMP_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class PeriodoCerrado(Conflicto):
    """Un error propio de un módulo: hereda el status y cambia el código."""

    codigo = "PERIODO_CERRADO"


CLASES = {
    clase.__name__: clase
    for clase in (
        ErrorDeNegocio,
        NoAutenticado,
        SinPermiso,
        NoEncontrado,
        Conflicto,
        ErrorDeValidacion,
        PeriodoCerrado,
    )
}


class Formulario(CamelModel):
    telefono_movil: str
    carrera_ids: list[int]


@pytest.fixture
def cliente():
    app = FastAPI()
    registrar_manejadores_de_errores(app)

    @app.get("/levantar/{nombre}")
    def levantar(nombre: str):
        raise CLASES[nombre]("Mensaje de prueba", campo="dni")

    @app.get("/sin-campo")
    def sin_campo():
        raise NoEncontrado("No está")

    @app.post("/formulario")
    def formulario(datos: Formulario):
        return datos

    @app.get("/pagina")
    def pagina(page: int = 1):
        return {"page": page}

    @app.get("/http/{codigo}")
    def levantar_http(codigo: int, detalle: str | None = None):
        raise HTTPException(status_code=codigo, detail=detalle)

    @app.get("/roto")
    def roto():
        raise RuntimeError("detalle interno que no tiene que salir")

    # Con el valor por defecto, el TestClient vuelve a levantar la excepción de los 500
    # aunque el manejador ya haya respondido.
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize(
    ("clase", "status", "codigo"),
    [
        (ErrorDeNegocio, 400, "BAD_REQUEST"),
        (NoAutenticado, 401, "UNAUTHORIZED"),
        (SinPermiso, 403, "FORBIDDEN"),
        (NoEncontrado, 404, "NOT_FOUND"),
        (Conflicto, 409, "CONFLICT"),
        (ErrorDeValidacion, 422, "VALIDATION_ERROR"),
        (PeriodoCerrado, 409, "PERIODO_CERRADO"),
    ],
)
def test_cada_error_de_negocio_da_su_status_y_el_cuerpo_con_los_cinco_campos(
    cliente, clase, status, codigo
):
    respuesta = cliente.get(f"/levantar/{clase.__name__}")

    cuerpo = respuesta.json()
    assert respuesta.status_code == status
    assert set(cuerpo) == CLAVES
    assert cuerpo["statusCode"] == status
    assert cuerpo["error"] == codigo
    assert cuerpo["message"] == "Mensaje de prueba"
    assert cuerpo["field"] == "dni"
    assert TIMESTAMP_UTC.match(cuerpo["timestamp"])


def test_el_campo_es_nulo_si_el_error_no_lo_indica(cliente):
    cuerpo = cliente.get("/sin-campo").json()

    assert cuerpo["message"] == "No está"
    assert cuerpo["field"] is None


def test_el_422_de_pydantic_dice_que_campo_falta_en_camel_case(cliente):
    respuesta = cliente.post("/formulario", json={"carreraIds": [1]})

    cuerpo = respuesta.json()
    assert respuesta.status_code == 422
    assert set(cuerpo) == CLAVES
    assert cuerpo["error"] == "VALIDATION_ERROR"
    assert cuerpo["field"] == "telefonoMovil"
    assert cuerpo["message"] == "El campo telefonoMovil es obligatorio"


def test_el_422_con_un_valor_invalido_usa_el_campo_y_no_el_indice_de_la_lista(cliente):
    respuesta = cliente.post("/formulario", json={"telefonoMovil": "1", "carreraIds": ["a"]})

    cuerpo = respuesta.json()
    assert respuesta.status_code == 422
    assert cuerpo["field"] == "carreraIds"
    assert cuerpo["message"] == "El valor de carreraIds no es válido"


def test_el_422_tambien_aplica_a_los_parametros_de_la_url(cliente):
    cuerpo = cliente.get("/pagina?page=abc").json()

    assert cuerpo["error"] == "VALIDATION_ERROR"
    assert cuerpo["field"] == "page"


def test_una_ruta_que_no_existe_da_404_en_el_formato_y_en_español(cliente):
    respuesta = cliente.get("/no-existe")

    cuerpo = respuesta.json()
    assert respuesta.status_code == 404
    assert set(cuerpo) == CLAVES
    assert cuerpo["error"] == "NOT_FOUND"
    assert cuerpo["message"] == "No encontramos lo que buscás"


def test_un_metodo_no_permitido_da_405(cliente):
    respuesta = cliente.post("/pagina")

    assert respuesta.status_code == 405
    assert respuesta.json()["error"] == "METHOD_NOT_ALLOWED"


@pytest.mark.parametrize(
    ("status", "codigo"), [(401, "UNAUTHORIZED"), (403, "FORBIDDEN"), (429, "RATE_LIMITED")]
)
def test_un_http_exception_se_convierte_al_formato_con_su_codigo(cliente, status, codigo):
    respuesta = cliente.get(f"/http/{status}")

    assert respuesta.status_code == status
    assert respuesta.json()["error"] == codigo
    assert respuesta.json()["message"] == MENSAJES_HTTP[status]


def test_un_http_exception_con_mensaje_propio_lo_conserva(cliente):
    respuesta = cliente.get("/http/404", params={"detalle": "Legajo no encontrado"})

    assert respuesta.json()["message"] == "Legajo no encontrado"


def test_un_status_sin_codigo_propio_da_http_error(cliente):
    assert cliente.get("/http/418").json()["error"] == "HTTP_ERROR"


def test_un_error_inesperado_da_500_sin_detalles_internos_y_queda_en_el_log(cliente, caplog):
    respuesta = cliente.get("/roto")

    cuerpo = respuesta.json()
    assert respuesta.status_code == 500
    assert set(cuerpo) == CLAVES
    assert cuerpo["error"] == "INTERNAL_ERROR"
    assert "detalle interno" not in respuesta.text
    assert "detalle interno" in caplog.text
    assert respuesta.headers["x-content-type-options"] == "nosniff"
