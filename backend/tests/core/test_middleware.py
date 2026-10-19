"""Tests de los headers de seguridad (NFR-S05, módulo 05)."""

import pytest


def test_las_respuestas_de_la_api_llevan_los_headers_de_seguridad(client):
    respuesta = client.get("/api/v1/health")
    assert respuesta.headers["x-content-type-options"] == "nosniff"
    assert respuesta.headers["x-frame-options"] == "DENY"
    assert respuesta.headers["referrer-policy"] == "no-referrer"
    assert (
        respuesta.headers["content-security-policy"] == "default-src 'none'; frame-ancestors 'none'"
    )
    assert respuesta.headers["cache-control"] == "no-store"


def test_las_respuestas_de_error_tambien_llevan_los_headers(client):
    respuesta = client.get("/api/v1/no-existe")
    assert respuesta.status_code == 404
    assert respuesta.headers["x-content-type-options"] == "nosniff"
    assert "content-security-policy" in respuesta.headers


@pytest.mark.parametrize("ruta", ["/api/docs", "/api/openapi.json"])
def test_swagger_no_lleva_csp_para_poder_cargar_su_js(client, ruta):
    respuesta = client.get(ruta)
    assert respuesta.status_code == 200
    assert "content-security-policy" not in respuesta.headers
    # El resto de los headers se mantiene.
    assert respuesta.headers["x-frame-options"] == "DENY"
