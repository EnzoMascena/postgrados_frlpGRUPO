"""Regla del período de inscripción y caso de uso `cambiar_periodo_de_inscripcion`, sin base."""

from dataclasses import replace
from datetime import date
from uuid import UUID, uuid4

import pytest

from src.cohortes.application.cambiar_periodo import (
    MENSAJE_COHORTE_INEXISTENTE,
    cambiar_periodo_de_inscripcion,
)
from src.cohortes.domain.cohorte import Carrera, Cohorte
from src.shared.errors import ErrorDeValidacion, NoEncontrado

HOY = date(2026, 11, 1)


class RepoEnMemoria:
    def __init__(self, *cohortes: Cohorte) -> None:
        self.cohortes = {cohorte.id: cohorte for cohorte in cohortes}
        self.guardadas: list[Cohorte] = []

    def listar_cohortes(self) -> list[Cohorte]:
        return list(self.cohortes.values())

    def listar_carreras_activas(self) -> list[Carrera]:
        return []

    def obtener_cohorte(self, cohorte_id: UUID) -> Cohorte | None:
        return self.cohortes.get(cohorte_id)

    def guardar_periodo(self, cohorte: Cohorte) -> None:
        self.cohortes[cohorte.id] = cohorte
        self.guardadas.append(cohorte)


def una_cohorte(abierta: bool = True, proxima_apertura: date | None = None) -> Cohorte:
    return Cohorte(
        id=uuid4(),
        anio=2026,
        numero=1,
        nombre="Cohorte 2026",
        inscripcion_abierta=abierta,
        fecha_inicio=date(2026, 4, 1),
        proxima_apertura=proxima_apertura,
    )


def cambiar(repo: RepoEnMemoria, cohorte: Cohorte, abierta: bool, proxima: date | None = None):
    return cambiar_periodo_de_inscripcion(cohorte.id, abierta, proxima, repo, HOY)


def test_cerrar_con_proxima_apertura_cambia_solo_el_periodo_y_lo_guarda():
    cohorte = una_cohorte(abierta=True)
    repo = RepoEnMemoria(cohorte)

    resultado = cambiar(repo, cohorte, abierta=False, proxima=date(2027, 3, 1))

    esperada = replace(cohorte, inscripcion_abierta=False, proxima_apertura=date(2027, 3, 1))
    assert resultado == esperada
    assert repo.guardadas == [esperada]


def test_cerrar_sin_proxima_apertura_borra_la_que_habia():
    cohorte = una_cohorte(abierta=False, proxima_apertura=date(2027, 3, 1))
    repo = RepoEnMemoria(cohorte)

    resultado = cambiar(repo, cohorte, abierta=False)

    assert resultado.proxima_apertura is None


def test_la_proxima_apertura_puede_ser_hoy():
    cohorte = una_cohorte()
    repo = RepoEnMemoria(cohorte)

    resultado = cambiar(repo, cohorte, abierta=False, proxima=HOY)

    assert resultado.proxima_apertura == HOY


def test_una_proxima_apertura_pasada_da_422_y_no_guarda_nada():
    cohorte = una_cohorte()
    repo = RepoEnMemoria(cohorte)

    with pytest.raises(ErrorDeValidacion) as error:
        cambiar(repo, cohorte, abierta=False, proxima=date(2026, 10, 31))

    assert error.value.status_code == 422
    assert error.value.campo == "proximaApertura"
    assert error.value.mensaje == "La próxima apertura no puede ser una fecha pasada"
    assert repo.guardadas == []


@pytest.mark.parametrize("proxima", [None, date(2027, 3, 1), date(2020, 1, 1)])
def test_abrir_borra_la_proxima_apertura_venga_la_que_venga(proxima):
    cohorte = una_cohorte(abierta=False, proxima_apertura=date(2027, 3, 1))
    repo = RepoEnMemoria(cohorte)

    resultado = cambiar(repo, cohorte, abierta=True, proxima=proxima)

    assert resultado.inscripcion_abierta is True
    assert resultado.proxima_apertura is None


def test_una_cohorte_que_no_existe_da_404():
    repo = RepoEnMemoria()

    with pytest.raises(NoEncontrado) as error:
        cambiar(repo, una_cohorte(), abierta=False)

    assert error.value.status_code == 404
    assert error.value.mensaje == MENSAJE_COHORTE_INEXISTENTE
    assert repo.guardadas == []
