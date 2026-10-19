"""Tests de autenticación y autorización (NFR-S01, ASR-002, módulo 06).

Una app chica con una ruta por guarda, la sesión de test y los mismos
handlers de errores que la app real. Prueba 401 frente a 403, el rol
releído de la base y el IDOR del aspirante y del docente.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.database import get_session
from app.core.dependencies import (
    require_legajo_propio,
    require_role,
    require_seminario_propio,
)
from app.core.errores import registrar_handlers
from app.core.principal import Principal
from app.core.security import crear_token_aspirante, crear_token_docente, crear_token_usuario
from app.models.enums import Rol, RolUsuario


@pytest.fixture
def cliente(session) -> TestClient:
    app = FastAPI()
    registrar_handlers(app)

    @app.get("/solo-coordinador")
    def solo_coordinador(principal: Principal = Depends(require_role(Rol.COORDINADOR))):
        return {"rol": principal.rol, "email": principal.email}

    @app.get("/cualquiera")
    def cualquiera(principal: Principal = Depends(require_role(*Rol))):
        return {
            "tipo": principal.tipo,
            "rol": principal.rol,
            "legajoId": str(principal.legajo_id) if principal.legajo_id else None,
            "seminarioId": str(principal.seminario_id) if principal.seminario_id else None,
        }

    @app.get("/legajos/{legajo_id}")
    def ver_legajo(
        legajo_id: UUID,
        principal: Principal = Depends(require_legajo_propio(Rol.ASPIRANTE, Rol.COORDINADOR)),
    ):
        return {"legajoId": str(legajo_id)}

    @app.get("/seminarios/{seminario_id}")
    def ver_seminario(
        seminario_id: UUID,
        principal: Principal = Depends(require_seminario_propio(Rol.DOCENTE)),
    ):
        return {"seminarioId": str(seminario_id)}

    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app)


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ── 401: no sabemos quién sos ──────────────────────────────────────────────


def test_sin_token_da_401_con_www_authenticate(cliente):
    respuesta = cliente.get("/solo-coordinador")
    assert respuesta.status_code == 401
    assert respuesta.headers["www-authenticate"] == "Bearer"
    assert respuesta.json()["error"] == "UNAUTHORIZED"


@pytest.mark.parametrize("token", ["abc", "Bearer", "eyJhbGciOiJIUzI1NiJ9.e30.firma-falsa"])
def test_un_token_que_no_es_jwt_valido_da_401(cliente, token):
    assert cliente.get("/solo-coordinador", headers=_bearer(token)).status_code == 401


def test_un_token_de_un_usuario_que_no_existe_da_401(cliente):
    token = crear_token_usuario(uuid4(), "COORDINADOR")
    assert cliente.get("/solo-coordinador", headers=_bearer(token)).status_code == 401


def test_un_usuario_inactivo_no_entra_aunque_el_token_no_venza(cliente, session, coordinador):
    token = crear_token_usuario(coordinador.id, coordinador.rol)
    coordinador.activo = False
    session.add(coordinador)
    session.commit()
    assert cliente.get("/solo-coordinador", headers=_bearer(token)).status_code == 401


def test_un_aspirante_cuyo_legajo_no_existe_da_401(cliente):
    token = crear_token_aspirante(uuid4())
    assert cliente.get("/cualquiera", headers=_bearer(token)).status_code == 401


def test_el_token_del_docente_deja_de_valer_si_vence_su_acceso(cliente, session, acceso_docente):
    token = crear_token_docente(
        acceso_docente.id, acceso_docente.seminario_id, datetime.now(UTC) + timedelta(hours=1)
    )
    acceso_docente.expira_en = datetime.now(UTC) - timedelta(minutes=1)
    session.add(acceso_docente)
    session.commit()
    assert cliente.get("/cualquiera", headers=_bearer(token)).status_code == 401


def test_un_token_docente_con_otro_seminario_que_su_acceso_da_401(cliente, acceso_docente):
    adulterado = crear_token_docente(
        acceso_docente.id, uuid4(), datetime.now(UTC) + timedelta(hours=1)
    )
    assert cliente.get("/cualquiera", headers=_bearer(adulterado)).status_code == 401


# ── 403: sabemos quién sos, pero no podés ──────────────────────────────────


def test_el_coordinador_pasa_por_su_ruta(cliente, headers_por_rol):
    respuesta = cliente.get("/solo-coordinador", headers=headers_por_rol[Rol.COORDINADOR])
    assert respuesta.status_code == 200
    assert respuesta.json() == {"rol": "COORDINADOR", "email": "coordinador@fenix.test"}


@pytest.mark.parametrize("rol", [Rol.CPR, Rol.ASPIRANTE, Rol.DOCENTE])
def test_los_otros_roles_reciben_403_en_la_ruta_del_coordinador(cliente, headers_por_rol, rol):
    respuesta = cliente.get("/solo-coordinador", headers=headers_por_rol[rol])
    assert respuesta.status_code == 403
    assert respuesta.json()["error"] == "FORBIDDEN"


def test_el_rol_se_relee_de_la_base_en_cada_request(cliente, session, coordinador):
    # El token dice COORDINADOR, pero en la base ya es CPR: manda la base.
    token = crear_token_usuario(coordinador.id, "COORDINADOR")
    coordinador.rol = RolUsuario.CPR
    session.add(coordinador)
    session.commit()
    assert cliente.get("/solo-coordinador", headers=_bearer(token)).status_code == 403


def test_cada_rol_llega_con_su_principal(cliente, headers_por_rol, legajo, acceso_docente):
    aspirante = cliente.get("/cualquiera", headers=headers_por_rol[Rol.ASPIRANTE]).json()
    docente = cliente.get("/cualquiera", headers=headers_por_rol[Rol.DOCENTE]).json()
    assert aspirante == {
        "tipo": "aspirante",
        "rol": "ASPIRANTE",
        "legajoId": str(legajo.id),
        "seminarioId": None,
    }
    assert docente["rol"] == "DOCENTE"
    assert docente["seminarioId"] == str(acceso_docente.seminario_id)


# ── IDOR: solo lo propio ───────────────────────────────────────────────────


def test_el_aspirante_entra_a_su_propio_legajo(cliente, headers_por_rol, legajo):
    respuesta = cliente.get(f"/legajos/{legajo.id}", headers=headers_por_rol[Rol.ASPIRANTE])
    assert respuesta.status_code == 200


def test_el_aspirante_no_entra_a_un_legajo_ajeno(cliente, headers_por_rol):
    respuesta = cliente.get(f"/legajos/{uuid4()}", headers=headers_por_rol[Rol.ASPIRANTE])
    assert respuesta.status_code == 403
    assert respuesta.json()["message"] == "Solo podés acceder a tu propio legajo."


def test_el_coordinador_entra_a_cualquier_legajo(cliente, headers_por_rol):
    respuesta = cliente.get(f"/legajos/{uuid4()}", headers=headers_por_rol[Rol.COORDINADOR])
    assert respuesta.status_code == 200


def test_el_docente_entra_a_su_seminario(cliente, headers_por_rol, seminario):
    respuesta = cliente.get(f"/seminarios/{seminario.id}", headers=headers_por_rol[Rol.DOCENTE])
    assert respuesta.status_code == 200


def test_el_docente_no_entra_a_un_seminario_ajeno(cliente, headers_por_rol):
    # ASR-002: el docente del seminario 88 pide el 99 → 403.
    respuesta = cliente.get(f"/seminarios/{uuid4()}", headers=headers_por_rol[Rol.DOCENTE])
    assert respuesta.status_code == 403
    assert respuesta.json()["message"] == "Solo podés acceder a tu propio seminario."
