"""Regla de vencimiento de la reserva (BR-005), sin base."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from src.legajos.domain.vencimiento import DIAS_RESERVA, fecha_limite, reserva_vencida

APROBACION = datetime(2026, 10, 1, 14, 30, tzinfo=UTC)


def test_la_reserva_dura_30_dias():
    assert DIAS_RESERVA == 30


def test_la_fecha_limite_es_la_aprobacion_mas_30_dias_corridos():
    assert fecha_limite(APROBACION) == datetime(2026, 10, 31, 14, 30, tzinfo=UTC)


@pytest.mark.parametrize(
    ("transcurrido", "vencida"),
    [
        (timedelta(0), False),
        (timedelta(days=29, hours=23), False),
        (timedelta(days=30) - timedelta(seconds=1), False),
        (timedelta(days=30), True),
        (timedelta(days=31), True),
        (timedelta(days=365), True),
    ],
)
def test_vence_a_partir_de_los_30_dias(transcurrido, vencida):
    assert reserva_vencida(APROBACION, APROBACION + transcurrido) is vencida


def test_compara_el_mismo_instante_aunque_venga_en_otra_zona_horaria():
    # 31/10 11:30 en Buenos Aires (UTC-3) es el mismo instante que 31/10 14:30 UTC.
    ahora_en_argentina = datetime(
        2026, 10, 31, 11, 30, tzinfo=ZoneInfo("America/Argentina/Buenos_Aires")
    )

    assert reserva_vencida(APROBACION, ahora_en_argentina) is True
    assert reserva_vencida(APROBACION, ahora_en_argentina - timedelta(minutes=1)) is False


def test_una_fecha_sin_zona_horaria_no_se_compara_en_silencio():
    with pytest.raises(TypeError):
        reserva_vencida(APROBACION, datetime(2026, 11, 15))
