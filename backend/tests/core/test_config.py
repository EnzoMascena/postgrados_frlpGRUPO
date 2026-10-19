"""Tests de la configuración: defaults de desarrollo y fail-loud en producción.

config.py se lee UNA vez al importar, así que los casos que cambian el
entorno importan la config en un proceso aparte (subprocess): el proceso
de los tests no se entera y no queda "contaminado".
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from app.core.config import _env_bool

BACKEND_DIR = Path(__file__).resolve().parents[2]

# Lo que imprime el proceso hijo: entorno, scheduler y algoritmo del JWT.
_IMPRIMIR = (
    "from app.core import config; "
    "print(config.ENVIRONMENT, config.SCHEDULER_ENABLED, config.ALGORITHM, config.SECRET_KEY != '')"
)


def _importar_config(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Importa app.core.config en otro proceso, con un entorno controlado."""
    base = {
        k: v
        for k, v in os.environ.items()
        if k not in {"ENVIRONMENT", "SECRET_KEY", "SCHEDULER_ENABLED"}
    }
    return subprocess.run(
        [sys.executable, "-c", _IMPRIMIR],
        cwd=BACKEND_DIR,
        env={**base, **env},
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_produccion_sin_secret_key_no_arranca():
    # Arrange + Act
    resultado = _importar_config({"ENVIRONMENT": "production"})
    # Assert: fail-loud, con un mensaje que explica qué hacer.
    assert resultado.returncode != 0
    assert "SECRET_KEY es OBLIGATORIA en producción" in resultado.stderr


def test_produccion_con_secret_key_arranca():
    resultado = _importar_config({"ENVIRONMENT": "production", "SECRET_KEY": "x" * 64})
    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout.split() == ["production", "True", "HS256", "True"]


def test_desarrollo_arranca_sin_env_con_defaults():
    resultado = _importar_config({"ENVIRONMENT": "development"})
    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout.split() == ["development", "True", "HS256", "True"]


def test_en_testing_el_scheduler_arranca_apagado():
    resultado = _importar_config({"ENVIRONMENT": "testing"})
    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout.split()[:2] == ["testing", "False"]


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [("true", True), ("1", True), ("Sí", True), ("yes", True), ("false", False), ("0", False)],
)
def test_env_bool_interpreta_los_valores(monkeypatch, valor, esperado):
    monkeypatch.setenv("VARIABLE_DE_PRUEBA", valor)
    assert _env_bool("VARIABLE_DE_PRUEBA", default=not esperado) is esperado


def test_env_bool_sin_variable_usa_el_default(monkeypatch):
    monkeypatch.delenv("VARIABLE_DE_PRUEBA", raising=False)
    assert _env_bool("VARIABLE_DE_PRUEBA", default=True) is True
