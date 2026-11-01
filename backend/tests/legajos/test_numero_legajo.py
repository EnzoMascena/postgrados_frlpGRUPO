"""Número de legajo `AA-CCC-SSS` (plan §9), sin base."""

import pytest

from src.legajos.domain.numero_legajo import generar_numero_legajo


@pytest.mark.parametrize(
    ("anio", "cohorte", "secuencial", "esperado"),
    [
        (2026, 1, 45, "26-001-045"),
        (2026, 1, 1, "26-001-001"),
        (2026, 1, 2, "26-001-002"),
        (2027, 12, 999, "27-012-999"),
        (2030, 999, 100, "30-999-100"),
        (2100, 3, 7, "00-003-007"),
    ],
)
def test_arma_el_numero_con_ceros_a_la_izquierda(anio, cohorte, secuencial, esperado):
    assert generar_numero_legajo(anio, cohorte, secuencial) == esperado


@pytest.mark.parametrize("secuencial", [0, -1, 1000])
def test_un_secuencial_fuera_de_1_a_999_falla(secuencial):
    with pytest.raises(ValueError, match="secuencial"):
        generar_numero_legajo(2026, 1, secuencial)


@pytest.mark.parametrize("cohorte", [0, -1, 1000])
def test_un_numero_de_cohorte_fuera_de_1_a_999_falla(cohorte):
    with pytest.raises(ValueError, match="cohorte"):
        generar_numero_legajo(2026, cohorte, 1)
