"""Permisos de todos los endpoints de la API (NFR-S01, plan §10).

En lugar de una lista fija de endpoints protegidos, se recorren las rutas reales de la app (las
que publica en el OpenAPI, lo mismo que muestra Swagger). Así, cada endpoint nuevo que se mergee
queda cubierto sin tocar este archivo, y si alguien se olvida el `require_role`, el test falla.

Se clasifican en tres grupos:

- Públicos: la lista del plan §10, la única que se mantiene a mano.
- Del aspirante (`/seguimiento/{token}...`): no usan Bearer sino el token del link; un token
  inválido da 404.
- Todo lo demás es del coordinador: 401 sin token y 403 con un rol que no corresponde (docente).
"""

import re
from uuid import uuid4

import pytest
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles

from main import app

PREFIJO = "/api/v1"

PUBLICOS = {
    ("GET", f"{PREFIJO}/health"),
    ("POST", f"{PREFIJO}/auth/login"),
    ("GET", f"{PREFIJO}/cohortes"),
    ("GET", f"{PREFIJO}/carreras"),
    ("POST", f"{PREFIJO}/legajos"),
    ("POST", f"{PREFIJO}/legajos/recuperar-acceso"),
}
PREFIJO_ASPIRANTE = f"{PREFIJO}/seguimiento/"
METODOS_HTTP = {"get", "post", "put", "patch", "delete"}
TOKEN_INVALIDO = "token-que-no-existe"


def _rutas_de_la_app() -> list[tuple[str, str]]:
    """(método, ruta) de cada endpoint de la app, tal como aparece en el OpenAPI.

    En FastAPI 0.162 `app.routes` guarda cada `include_router` como un envoltorio y no lista los
    endpoints: el OpenAPI sí, y es lo que consume el front.
    """
    rutas = app.openapi()["paths"]
    return sorted(
        (metodo.upper(), ruta)
        for ruta, operaciones in rutas.items()
        for metodo in operaciones
        if metodo in METODOS_HTTP
    )


def _con_parametros(ruta: str) -> str:
    """Reemplaza cada `{param}`: el token del aspirante por uno inválido, el resto por un UUID."""
    ruta = ruta.replace("{token}", TOKEN_INVALIDO)
    return re.sub(r"\{[^}]+\}", lambda _: str(uuid4()), ruta)


RUTAS = _rutas_de_la_app()
ASPIRANTE = [r for r in RUTAS if r[1].startswith(PREFIJO_ASPIRANTE)]
PROTEGIDAS = [r for r in RUTAS if r not in PUBLICOS and r not in ASPIRANTE]


def _id(ruta: tuple[str, str]) -> str:
    return f"{ruta[0]} {ruta[1]}"


def test_la_lista_de_publicos_coincide_con_la_app():
    assert sorted(PUBLICOS - set(RUTAS)) == [], "Hay públicos del plan que la app no tiene"


def test_hay_rutas_en_cada_grupo():
    # Si el recorrido de rutas se rompe (por ejemplo, otra versión de FastAPI), que no pase en
    # silencio con cero casos.
    assert PROTEGIDAS
    assert ASPIRANTE


@pytest.mark.parametrize(("metodo", "ruta"), PROTEGIDAS, ids=map(_id, PROTEGIDAS))
def test_protegida_sin_token_da_401(client, metodo, ruta):
    respuesta = client.request(metodo, _con_parametros(ruta))

    assert respuesta.status_code == 401
    assert respuesta.json()["error"] == "UNAUTHORIZED"


@pytest.mark.parametrize(("metodo", "ruta"), PROTEGIDAS, ids=map(_id, PROTEGIDAS))
def test_protegida_con_token_invalido_da_401(client, metodo, ruta):
    headers = {"Authorization": "Bearer esto-no-es-un-jwt"}

    respuesta = client.request(metodo, _con_parametros(ruta), headers=headers)

    assert respuesta.status_code == 401


@pytest.mark.parametrize(("metodo", "ruta"), PROTEGIDAS, ids=map(_id, PROTEGIDAS))
def test_protegida_con_docente_da_403(client, headers_docente, metodo, ruta):
    respuesta = client.request(metodo, _con_parametros(ruta), headers=headers_docente)

    assert respuesta.status_code == 403
    assert respuesta.json()["error"] == "FORBIDDEN"


@pytest.mark.parametrize(("metodo", "ruta"), ASPIRANTE, ids=map(_id, ASPIRANTE))
def test_aspirante_con_token_invalido_da_404(client, metodo, ruta):
    respuesta = client.request(metodo, _con_parametros(ruta))

    assert respuesta.status_code == 404
    assert respuesta.json()["error"] == "NOT_FOUND"


@pytest.mark.parametrize(("metodo", "ruta"), sorted(PUBLICOS), ids=map(_id, sorted(PUBLICOS)))
def test_publica_no_pide_token(client, metodo, ruta):
    # Sin cuerpo, un POST puede dar 422: lo que importa es que no pida sesión.
    respuesta = client.request(metodo, ruta)

    assert respuesta.status_code not in (401, 403)


def test_ninguna_ruta_sirve_el_disco_de_pdfs(client):
    montajes = [r for r in app.routes if isinstance(r, Mount)]
    assert not [m for m in montajes if isinstance(m.app, StaticFiles)]
    assert not [ruta for _, ruta in RUTAS if "storage" in ruta or "static" in ruta]

    for ruta in ("/.storage/x.pdf", f"{PREFIJO}/.storage/x.pdf", f"{PREFIJO}/storage/x.pdf"):
        assert client.get(ruta).status_code == 404


def test_respuesta_json_trae_headers_de_seguridad(client):
    respuesta = client.get(f"{PREFIJO}/cohortes")

    assert respuesta.headers["content-type"].startswith("application/json")
    assert respuesta.headers["X-Content-Type-Options"] == "nosniff"
    assert respuesta.headers["X-Frame-Options"] == "DENY"
    assert respuesta.headers["Referrer-Policy"] == "no-referrer"
    assert "default-src 'none'" in respuesta.headers["Content-Security-Policy"]
