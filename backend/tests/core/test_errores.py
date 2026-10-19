"""Tests del formato uniforme de errores (ARQUITECTURA §11.2, NFR-U02).

Se arma una app chica, con una ruta por cada tipo de error y los mismos
handlers que registra main.py. No necesita base de datos.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import Field, field_validator

from app.core.errores import ErrorAPI, registrar_handlers, respuestas
from app.core.excepciones import Conflicto, ErrorDeDominio
from app.core.schemas import CamelModel


class Inscripcion(CamelModel):
    apellido_nombre: str = Field(min_length=3)
    edad: int
    dni: str

    @field_validator("dni")
    @classmethod
    def dni_sin_puntos(cls, valor: str) -> str:
        if "." in valor:
            raise ValueError("El DNI va sin puntos")
        return valor


def _app_de_prueba() -> FastAPI:
    app = FastAPI()
    registrar_handlers(app)

    @app.post("/validar")
    def validar(body: Inscripcion):
        return body

    @app.get("/duplicado")
    def duplicado():
        # El patrón del controller: atrapa la excepción de dominio y elige el status.
        try:
            raise Conflicto("Ya existe una preinscripción con este DNI", campo="dni")
        except Conflicto as error:
            raise ErrorAPI(400, error.mensaje, campo=error.campo) from error

    @app.get("/sin-token")
    def sin_token():
        raise ErrorAPI(401, "Credenciales inválidas", headers={"WWW-Authenticate": "Bearer"})

    @app.get("/todo")
    def todo():
        raise NotImplementedError("TODO(Gero): US-C-002 calcular el semáforo")

    @app.get("/explota")
    def explota():
        raise RuntimeError("detalle interno que no tiene que salir")

    return app


@pytest.fixture
def cliente() -> TestClient:
    # raise_server_exceptions=False: así se ve la respuesta 500 en vez de la excepción.
    return TestClient(_app_de_prueba(), raise_server_exceptions=False)


def test_error_api_sale_con_el_formato_uniforme(cliente):
    respuesta = cliente.get("/duplicado")
    cuerpo = respuesta.json()
    assert respuesta.status_code == 400
    assert cuerpo["statusCode"] == 400
    assert cuerpo["error"] == "VALIDATION_ERROR"
    assert cuerpo["message"] == "Ya existe una preinscripción con este DNI"
    assert cuerpo["field"] == "dni"
    assert cuerpo["timestamp"].endswith("Z")


def test_el_401_conserva_el_header_www_authenticate(cliente):
    respuesta = cliente.get("/sin-token")
    assert respuesta.status_code == 401
    assert respuesta.headers["www-authenticate"] == "Bearer"
    assert respuesta.json()["error"] == "UNAUTHORIZED"


@pytest.mark.parametrize(
    ("body", "campo", "mensaje"),
    [
        ({"edad": 30, "dni": "30456789"}, "apellidoNombre", "Este campo es obligatorio."),
        (
            {"apellidoNombre": "Al", "edad": 30, "dni": "30456789"},
            "apellidoNombre",
            "Tiene que tener al menos 3 caracteres.",
        ),
        (
            {"apellidoNombre": "López, Ana", "edad": "abc", "dni": "30456789"},
            "edad",
            "Tiene que ser un número entero.",
        ),
        (
            {"apellidoNombre": "López, Ana", "edad": 30, "dni": "30.456.789"},
            "dni",
            "El DNI va sin puntos",
        ),
    ],
)
def test_el_422_viene_en_espanol_con_el_campo_en_camel_case(cliente, body, campo, mensaje):
    respuesta = cliente.post("/validar", json=body)
    cuerpo = respuesta.json()
    assert respuesta.status_code == 422
    assert cuerpo["error"] == "VALIDATION_ERROR"
    assert cuerpo["field"] == campo
    assert cuerpo["message"] == mensaje


def test_un_json_roto_da_422_sin_campo(cliente):
    respuesta = cliente.post(
        "/validar", content="{no es json", headers={"Content-Type": "application/json"}
    )
    assert respuesta.status_code == 422
    assert respuesta.json()["field"] is None
    assert respuesta.json()["message"] == "El cuerpo de la solicitud no es un JSON válido."


def test_not_implemented_da_501_con_el_todo_del_duenio(cliente):
    respuesta = cliente.get("/todo")
    assert respuesta.status_code == 501
    assert respuesta.json()["error"] == "NOT_IMPLEMENTED"
    assert respuesta.json()["message"] == "TODO(Gero): US-C-002 calcular el semáforo"


def test_un_error_inesperado_da_500_sin_filtrar_el_detalle(cliente):
    respuesta = cliente.get("/explota")
    assert respuesta.status_code == 500
    assert respuesta.json()["error"] == "INTERNAL_ERROR"
    assert "detalle interno" not in respuesta.text


def test_ruta_inexistente_da_404_en_espanol(client):
    respuesta = client.get("/api/v1/no-existe")
    assert respuesta.status_code == 404
    assert respuesta.json()["error"] == "NOT_FOUND"
    assert respuesta.json()["message"] == "El recurso solicitado no existe."


def test_metodo_no_permitido_da_405_en_espanol(client):
    respuesta = client.post("/api/v1/health")
    assert respuesta.status_code == 405
    assert respuesta.json()["message"] == "Método no permitido en esta ruta."


def test_las_excepciones_de_dominio_guardan_mensaje_y_campo():
    error = ErrorDeDominio("El DNI tiene que tener 7 u 8 dígitos", campo="dni")
    assert str(error) == "El DNI tiene que tener 7 u 8 dígitos"
    assert error.campo == "dni"


def test_respuestas_documenta_los_errores_en_swagger():
    documentados = respuestas(401, 403)
    assert set(documentados) == {401, 403}
    assert documentados[403]["description"] == "No tenés permiso para realizar esta operación."
