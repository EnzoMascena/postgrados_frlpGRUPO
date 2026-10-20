"""Tests del health check y de la documentación de la API (NFR-M02)."""

from sqlalchemy.exc import OperationalError

from app.core.database import get_session
from app.main import app


def test_health_responde_ok_si_la_base_contesta(client):
    # Act
    respuesta = client.get("/api/v1/health")
    # Assert: camelCase en el JSON, como espera el front.
    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok", "baseDeDatos": "ok"}


def test_health_da_503_si_la_base_no_contesta(client):
    # Arrange: una sesión que falla como si postgres estuviera caído.
    class SesionCaida:
        def exec(self, *args, **kwargs):
            raise OperationalError("SELECT 1", {}, Exception("conexión rechazada"))

    app.dependency_overrides[get_session] = lambda: SesionCaida()
    # Act
    respuesta = client.get("/api/v1/health")
    # Assert: el detalle técnico NO sale en la respuesta.
    assert respuesta.status_code == 503
    assert respuesta.json() == {"estado": "error", "baseDeDatos": "sin conexión"}


def test_swagger_se_sirve_en_api_docs(client):
    assert client.get("/api/docs").status_code == 200


def test_openapi_lista_el_health_bajo_api_v1(client):
    esquema = client.get("/api/openapi.json").json()
    assert esquema["info"]["title"] == "Sistema de Posgrado — API"
    assert "/api/v1/health" in esquema["paths"]
