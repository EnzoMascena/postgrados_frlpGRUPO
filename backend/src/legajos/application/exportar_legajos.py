"""Caso de uso: exportar a Excel la búsqueda del coordinador (US-CORE-008, plan §10).

Los mismos filtros que `GET /legajos` (`criterios_desde` interpreta `q` igual), pero sin paginar:
trae hasta `MAXIMO_FILAS` legajos, los más nuevos primero. Arma también el nombre del archivo;
generar el `.xlsx` es cosa de la infraestructura (`excel_exporter.py`).
"""

from dataclasses import dataclass
from datetime import date
from typing import Protocol
from uuid import UUID

from src.legajos.application.buscar_legajos import (
    CriteriosBusqueda,
    FilaBusqueda,
    FiltrosBusqueda,
    LegajoListado,
    a_listado,
    criterios_desde,
)
from src.legajos.domain.entidades import DatosCohorte

# Una cohorte tiene unos 500 aspirantes: 5000 alcanza para todas juntas y frena una consulta
# que se vaya de las manos.
MAXIMO_FILAS = 5000


class ExportacionRepository(Protocol):
    def buscar(self, criterios: CriteriosBusqueda, offset: int, limite: int) -> list[FilaBusqueda]:
        """Los legajos que cumplen todos los criterios, los más nuevos primero."""
        ...

    def datos_cohorte(self, cohorte_id: UUID) -> DatosCohorte:
        """Año, número y nombre de la cohorte (`NoEncontrado` si no existe)."""
        ...


@dataclass(frozen=True)
class Exportacion:
    nombre_archivo: str
    filas: list[LegajoListado]


def exportar_legajos(
    filtros: FiltrosBusqueda, repo: ExportacionRepository, hoy: date
) -> Exportacion:
    """`hoy` es la fecha de Argentina: la pasa el router para que los tests la puedan fijar."""
    criterios = criterios_desde(filtros)
    filas = repo.buscar(criterios, 0, MAXIMO_FILAS)
    anio_cohorte = repo.datos_cohorte(filtros.cohorte_id).anio if filtros.cohorte_id else None
    return Exportacion(
        nombre_archivo=nombre_archivo(anio_cohorte, hoy),
        filas=[a_listado(fila) for fila in filas],
    )


def nombre_archivo(anio_cohorte: int | None, hoy: date) -> str:
    """`inscriptos-cohorte2026-2026-11-08.xlsx`, o `inscriptos-todas-…` sin filtro de cohorte."""
    cohorte = f"cohorte{anio_cohorte}" if anio_cohorte is not None else "todas"
    return f"inscriptos-{cohorte}-{hoy.isoformat()}.xlsx"
