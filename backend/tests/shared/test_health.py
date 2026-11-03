from sqlalchemy.exc import OperationalError

from main import app
from src.shared.database import get_session


def test_health_responde_200_con_la_base_viva(client):
    respuesta = client.get("/api/v1/health")

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"] == "application/json"
    assert respuesta.json() == {"status": "ok", "baseDeDatos": "ok"}


class SesionSinBase:
    def exec(self, *args, **kwargs):
        raise OperationalError("SELECT 1", {}, Exception("sin conexión"))


def test_health_responde_503_si_la_base_no_responde(client):
    app.dependency_overrides[get_session] = lambda: SesionSinBase()

    respuesta = client.get("/api/v1/health")

    assert respuesta.status_code == 503
    assert respuesta.json() == {"status": "error", "baseDeDatos": "error"}
