"""El token del link de seguimiento no queda en los logs (ADR-005)."""

import logging

import pytest

import main
from src.shared.logs import FILTRO_DE_TOKENS, FiltroDeTokens, tapar_token

TOKEN = "Q3JxVq0yZ2l4b2w-dGVzdF9fdG9rZW4"
# El formato de la línea del log de accesos de uvicorn: la ruta va como tercer argumento.
FORMATO_DE_ACCESO = '%s - "%s %s HTTP/%s" %d'


@pytest.mark.parametrize(
    ("ruta", "esperada"),
    [
        (f"/api/v1/seguimiento/{TOKEN}", "/api/v1/seguimiento/***"),
        (f"/api/v1/seguimiento/{TOKEN}/enviar", "/api/v1/seguimiento/***/enviar"),
        (
            f"/api/v1/seguimiento/{TOKEN}/documentos/4b0e6c2a/download",
            "/api/v1/seguimiento/***/documentos/4b0e6c2a/download",
        ),
        (f"/api/v1/seguimiento/{TOKEN}?x=1", "/api/v1/seguimiento/***?x=1"),
        (f"/seguimiento/{TOKEN}", "/seguimiento/***"),
    ],
)
def test_tapar_token_cambia_el_token_de_la_ruta_por_asteriscos(ruta, esperada):
    assert tapar_token(ruta) == esperada


@pytest.mark.parametrize(
    "ruta", ["/api/v1/legajos/4b0e6c2a", "/api/v1/legajos/recuperar-acceso", "/api/v1/seguimiento/"]
)
def test_tapar_token_no_toca_las_rutas_sin_token(ruta):
    assert tapar_token(ruta) == ruta


def _linea_de_acceso(ruta: str) -> logging.LogRecord:
    """Un registro con la forma del log de accesos de uvicorn."""
    return logging.LogRecord(
        "uvicorn.access",
        logging.INFO,
        __file__,
        1,
        FORMATO_DE_ACCESO,
        ("127.0.0.1:51258", "GET", ruta, "1.1", 200),
        None,
    )


def test_el_filtro_tapa_el_token_en_la_linea_del_log_de_accesos():
    registro = _linea_de_acceso(f"/api/v1/seguimiento/{TOKEN}/documentos")

    assert FiltroDeTokens().filter(registro) is True
    assert registro.getMessage() == (
        '127.0.0.1:51258 - "GET /api/v1/seguimiento/***/documentos HTTP/1.1" 200'
    )


def test_el_filtro_tapa_el_token_si_viene_en_el_mensaje():
    registro = logging.LogRecord(
        "x", logging.INFO, __file__, 1, f"GET /seguimiento/{TOKEN}", None, None
    )

    FiltroDeTokens().filter(registro)

    assert TOKEN not in registro.getMessage()


def test_la_app_deja_el_filtro_puesto_en_el_log_de_accesos_de_uvicorn(caplog):
    # `main` ya está importado: al importarlo se instala el filtro.
    assert main.app is not None
    assert FILTRO_DE_TOKENS in logging.getLogger("uvicorn.access").filters

    with caplog.at_level(logging.INFO, logger="uvicorn.access"):
        logging.getLogger("uvicorn.access").info(
            FORMATO_DE_ACCESO, "127.0.0.1:51258", "GET", f"/api/v1/seguimiento/{TOKEN}", "1.1", 200
        )

    assert TOKEN not in caplog.text
    assert "/api/v1/seguimiento/*** HTTP/1.1" in caplog.text


def test_el_filtro_deja_pasar_un_mensaje_que_no_es_texto():
    mensaje = {"evento": "algo"}
    registro = logging.LogRecord("x", logging.INFO, __file__, 1, mensaje, None, None)

    assert FiltroDeTokens().filter(registro) is True
    assert registro.msg is mensaje
