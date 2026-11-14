"""`exportar_legajos` con un repositorio falso: sin base.

Que use los mismos criterios que la búsqueda, que no pagine (tope de 5000) y que arme bien el
nombre del archivo. El Excel en sí se prueba en `test_excel_exporter.py`.
"""

from datetime import date
from uuid import UUID, uuid4

import pytest

from src.legajos.application.buscar_legajos import (
    MENSAJE_APELLIDO_CORTO,
    CriteriosBusqueda,
    FilaBusqueda,
    FiltrosBusqueda,
)
from src.legajos.application.exportar_legajos import (
    MAXIMO_FILAS,
    exportar_legajos,
    nombre_archivo,
)
from src.legajos.domain.entidades import DatosCohorte
from src.legajos.domain.estados import EstadoLegajo
from src.shared.errors import ErrorDeValidacion, NoEncontrado
from tests.legajos.test_buscar_legajos import nueva_fila

HOY = date(2026, 11, 8)


class RepoEnMemoria:
    def __init__(self, filas: list[FilaBusqueda] | None = None, anio: int = 2026) -> None:
        self.filas = filas or []
        self.anio = anio
        self.criterios: CriteriosBusqueda | None = None
        self.offset: int | None = None
        self.limite: int | None = None
        self.cohortes_pedidas: list[UUID] = []

    def buscar(self, criterios: CriteriosBusqueda, offset: int, limite: int) -> list[FilaBusqueda]:
        self.criterios, self.offset, self.limite = criterios, offset, limite
        return self.filas[offset : offset + limite]

    def datos_cohorte(self, cohorte_id: UUID) -> DatosCohorte:
        self.cohortes_pedidas.append(cohorte_id)
        return DatosCohorte(anio=self.anio, numero=1, nombre=f"Cohorte {self.anio}")


def test_usa_los_mismos_criterios_que_la_busqueda():
    repo = RepoEnMemoria()
    cohorte = uuid4()
    carrera = uuid4()

    exportar_legajos(
        FiltrosBusqueda(
            q="rodr",
            estado=EstadoLegajo.COMPLETADO,
            cohorte_id=cohorte,
            carrera_id=carrera,
            beca=True,
        ),
        repo,
        HOY,
    )

    assert repo.criterios == CriteriosBusqueda(
        apellido="rodr",
        estado=EstadoLegajo.COMPLETADO,
        cohorte_id=cohorte,
        carrera_id=carrera,
        beca=True,
    )


def test_q_con_solo_digitos_es_dni_exacto():
    repo = RepoEnMemoria()

    exportar_legajos(FiltrosBusqueda(q="28456789"), repo, HOY)

    assert repo.criterios == CriteriosBusqueda(dni="28456789")


def test_apellido_con_menos_de_3_letras_da_error_de_validacion():
    with pytest.raises(ErrorDeValidacion) as error:
        exportar_legajos(FiltrosBusqueda(q="ro"), RepoEnMemoria(), HOY)

    assert error.value.mensaje == MENSAJE_APELLIDO_CORTO
    assert error.value.campo == "q"


def test_no_pagina_trae_desde_el_principio_hasta_el_tope():
    repo = RepoEnMemoria()

    # `page` y `size` de la búsqueda no cuentan para el Excel.
    exportar_legajos(FiltrosBusqueda(page=3, size=10), repo, HOY)

    assert repo.offset == 0
    assert repo.limite == MAXIMO_FILAS == 5000


def test_devuelve_las_filas_con_los_documentos_contados():
    filas = [nueva_fila(apellido="Pérez"), nueva_fila(apellido="Gómez")]

    exportacion = exportar_legajos(FiltrosBusqueda(), RepoEnMemoria(filas), HOY)

    assert [fila.apellido for fila in exportacion.filas] == ["Pérez", "Gómez"]
    assert exportacion.filas[0].documentos_requeridos == 5
    assert exportacion.filas[0].documentos_cargados == 0


def test_con_cohorte_el_nombre_lleva_su_anio():
    repo = RepoEnMemoria(anio=2026)
    cohorte = uuid4()

    exportacion = exportar_legajos(FiltrosBusqueda(cohorte_id=cohorte), repo, HOY)

    assert exportacion.nombre_archivo == "inscriptos-cohorte2026-2026-11-08.xlsx"
    assert repo.cohortes_pedidas == [cohorte]


def test_sin_cohorte_el_nombre_dice_todas_y_no_busca_la_cohorte():
    repo = RepoEnMemoria()

    exportacion = exportar_legajos(FiltrosBusqueda(), repo, HOY)

    assert exportacion.nombre_archivo == "inscriptos-todas-2026-11-08.xlsx"
    assert repo.cohortes_pedidas == []


def test_una_cohorte_que_no_existe_da_no_encontrado():
    class RepoSinCohorte(RepoEnMemoria):
        def datos_cohorte(self, cohorte_id: UUID) -> DatosCohorte:
            raise NoEncontrado("No encontramos la cohorte del legajo")

    with pytest.raises(NoEncontrado):
        exportar_legajos(FiltrosBusqueda(cohorte_id=uuid4()), RepoSinCohorte(), HOY)


@pytest.mark.parametrize(
    ("anio", "hoy", "esperado"),
    [
        (2026, date(2026, 11, 8), "inscriptos-cohorte2026-2026-11-08.xlsx"),
        (2027, date(2026, 1, 5), "inscriptos-cohorte2027-2026-01-05.xlsx"),
        (None, date(2026, 11, 8), "inscriptos-todas-2026-11-08.xlsx"),
    ],
)
def test_nombre_archivo(anio, hoy, esperado):
    assert nombre_archivo(anio, hoy) == esperado
