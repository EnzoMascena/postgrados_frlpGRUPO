"""La app real (`main.app`): Swagger, headers de seguridad y CORS. No necesitan la base."""

import pytest
from fastapi.testclient import TestClient

from main import app

CSP_DE_LA_API = "default-src 'none'; frame-ancestors 'none'"
ORIGEN_DEL_FRONT = "http://localhost:3000"


@pytest.fixture
def cliente_sin_base():
    return TestClient(app)


def test_swagger_responde_200_en_api_docs(cliente_sin_base):
    respuesta = cliente_sin_base.get("/api/docs")

    assert respuesta.status_code == 200
    assert "text/html" in respuesta.headers["content-type"]


def test_el_esquema_openapi_esta_en_api_openapi_json_con_titulo_y_version(cliente_sin_base):
    respuesta = cliente_sin_base.get("/api/openapi.json")

    assert respuesta.status_code == 200
    assert respuesta.json()["info"]["title"] == "Sistema de Posgrado UTN FRLP · API"
    assert respuesta.json()["info"]["version"] == "0.5.0"
    assert "/api/v1/health" in respuesta.json()["paths"]


def test_redoc_no_esta_publicado(cliente_sin_base):
    assert cliente_sin_base.get("/api/redoc").status_code == 404


def test_las_respuestas_json_llevan_los_headers_de_seguridad_y_la_csp(cliente_sin_base):
    respuesta = cliente_sin_base.get("/ruta-que-no-existe")

    assert respuesta.headers["content-type"] == "application/json"
    assert respuesta.headers["x-content-type-options"] == "nosniff"
    assert respuesta.headers["x-frame-options"] == "DENY"
    assert respuesta.headers["referrer-policy"] == "no-referrer"
    assert respuesta.headers["content-security-policy"] == CSP_DE_LA_API


def test_swagger_lleva_los_headers_basicos_pero_no_la_csp_que_lo_rompería(cliente_sin_base):
    respuesta = cliente_sin_base.get("/api/docs")

    assert respuesta.headers["x-content-type-options"] == "nosniff"
    assert respuesta.headers["x-frame-options"] == "DENY"
    assert respuesta.headers["referrer-policy"] == "no-referrer"
    assert "content-security-policy" not in respuesta.headers


def test_cors_permite_el_origen_del_front(cliente_sin_base):
    respuesta = cliente_sin_base.options(
        "/api/v1/health",
        headers={"Origin": ORIGEN_DEL_FRONT, "Access-Control-Request-Method": "GET"},
    )

    assert respuesta.headers["access-control-allow-origin"] == ORIGEN_DEL_FRONT


def test_cors_no_permite_otros_origenes(cliente_sin_base):
    respuesta = cliente_sin_base.options(
        "/api/v1/health",
        headers={"Origin": "http://sitio-ajeno.example", "Access-Control-Request-Method": "GET"},
    )

    assert "access-control-allow-origin" not in respuesta.headers
