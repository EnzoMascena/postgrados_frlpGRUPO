import pytest
from pydantic import ValidationError

from src.shared.config import Settings

SECRETO_VALIDO = "s" * 32


def test_sin_jwt_secret_la_configuracion_no_arranca(monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)

    with pytest.raises(ValidationError, match="jwt_secret"):
        Settings(_env_file=None)


def test_un_jwt_secret_de_menos_de_32_caracteres_se_rechaza():
    with pytest.raises(ValidationError, match="32 caracteres o más"):
        Settings(_env_file=None, jwt_secret="s" * 31)


def test_un_jwt_secret_de_32_caracteres_se_acepta():
    assert Settings(_env_file=None, jwt_secret=SECRETO_VALIDO).jwt_secret == SECRETO_VALIDO


def test_los_origenes_cors_se_separan_por_comas_y_se_limpian():
    settings = Settings(
        _env_file=None, jwt_secret=SECRETO_VALIDO, cors_origins="http://a.com, http://b.com ,,"
    )

    assert settings.cors_origins_lista == ["http://a.com", "http://b.com"]


def test_los_valores_por_defecto_son_los_del_plan(monkeypatch):
    for variable in ("JWT_EXPIRA_MINUTOS", "TOKEN_SEGUIMIENTO_DIAS", "ZONA_HORARIA"):
        monkeypatch.delenv(variable, raising=False)

    settings = Settings(_env_file=None, jwt_secret=SECRETO_VALIDO)

    assert settings.jwt_expira_minutos == 480
    assert settings.token_seguimiento_dias == 60
    assert settings.zona_horaria == "America/Argentina/Buenos_Aires"
    assert settings.seed_coordinador_password is None
