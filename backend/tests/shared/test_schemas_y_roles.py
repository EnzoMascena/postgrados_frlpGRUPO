from dataclasses import FrozenInstanceError

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.shared.roles import Actor, Rol
from src.shared.schemas import CamelModel


class Ejemplo(CamelModel):
    telefono_movil: str
    tipo_beca: str | None = None


def test_camel_model_serializa_en_camel_case():
    ejemplo = Ejemplo(telefono_movil="221 4567890")

    assert ejemplo.model_dump(by_alias=True) == {"telefonoMovil": "221 4567890", "tipoBeca": None}


def test_camel_model_acepta_los_nombres_en_camel_y_en_snake_case():
    assert Ejemplo(telefonoMovil="1") == Ejemplo(telefono_movil="1")


def test_camel_model_se_arma_desde_un_objeto_con_atributos():
    class FilaDeLaBase:
        telefono_movil = "221 4567890"
        tipo_beca = "30"

    ejemplo = Ejemplo.model_validate(FilaDeLaBase())

    assert ejemplo.tipo_beca == "30"


def test_un_endpoint_con_camel_model_responde_el_json_en_camel_case():
    app = FastAPI()

    @app.get("/ejemplo", response_model=Ejemplo)
    def ejemplo():
        return Ejemplo(telefono_movil="1", tipo_beca="100")

    assert TestClient(app).get("/ejemplo").json() == {"telefonoMovil": "1", "tipoBeca": "100"}


def test_los_roles_se_comparan_con_su_nombre_como_texto():
    assert Rol.COORDINADOR == "COORDINADOR"
    assert {rol.value for rol in Rol} == {
        "ASPIRANTE",
        "COORDINADOR",
        "DOCENTE",
        "CPR",
        "ADMIN",
        "SISTEMA",
    }


def test_un_actor_del_sistema_no_tiene_email():
    assert Actor(Rol.SISTEMA).email is None


def test_un_actor_es_inmutable():
    actor = Actor(Rol.COORDINADOR, "coord@example.com")

    with pytest.raises(FrozenInstanceError):
        actor.rol = Rol.ADMIN
