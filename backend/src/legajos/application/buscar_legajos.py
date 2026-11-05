"""Caso de uso: la búsqueda de legajos del coordinador (US-CORE-007, plan §10).

Lo usa `GET /legajos` (paginado) y lo va a usar `GET /legajos/exportar` (L5, sin paginar), con
los mismos filtros. Acá vive la regla de qué significa `q`; el repositorio recibe los criterios
ya resueltos (`CriteriosBusqueda`) y solo sabe armar la consulta.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from src.gestion_documental.domain.requisitos import documentos_faltantes, documentos_requeridos
from src.gestion_documental.domain.tipos import TipoDocumento
from src.inscripcion.domain.tipos import TipoBeca
from src.legajos.domain.estados import EstadoLegajo
from src.shared.errors import ErrorDeValidacion

MINIMO_LETRAS_APELLIDO = 3
MENSAJE_APELLIDO_CORTO = "Ingresá al menos 3 letras del apellido"


# --- Lo que entra ---


@dataclass(frozen=True)
class FiltrosBusqueda:
    """Los query params de `GET /legajos`, tal como llegan. Todos se combinan."""

    q: str | None = None
    estado: EstadoLegajo | None = None
    cohorte_id: UUID | None = None
    carrera_id: UUID | None = None
    beca: bool | None = None
    page: int = 1
    size: int = 20


@dataclass(frozen=True)
class CriteriosBusqueda:
    """Los filtros con `q` ya interpretado: es lo que recibe el repositorio."""

    dni: str | None = None
    apellido: str | None = None
    estado: EstadoLegajo | None = None
    cohorte_id: UUID | None = None
    carrera_id: UUID | None = None
    beca: bool | None = None


# --- Lo que trae el repositorio ---


@dataclass(frozen=True)
class FilaBusqueda:
    """Un legajo del listado, con lo que hace falta para contar sus documentos."""

    id: UUID
    codigo_seguimiento: str
    numero_legajo: str | None
    apellido: str
    nombre: str
    dni: str
    email: str
    estado: EstadoLegajo
    cohorte: str
    carreras: list[str]
    solicita_beca: bool
    tipo_beca: TipoBeca | None
    titulo_posgrado: str | None
    tipos_cargados: frozenset[TipoDocumento]
    fecha_inscripcion: datetime | None


class BusquedaRepository(Protocol):
    def buscar(self, criterios: CriteriosBusqueda, offset: int, limite: int) -> list[FilaBusqueda]:
        """Los legajos que cumplen todos los criterios, los más nuevos primero (`created_at`)."""
        ...

    def contar(self, criterios: CriteriosBusqueda) -> int:
        """Cuántos legajos cumplen los criterios, sin paginar."""
        ...


# --- Lo que devuelve el caso de uso ---


@dataclass(frozen=True)
class LegajoListado:
    """Una fila del listado del dashboard (los `items` del plan §10)."""

    id: UUID
    codigo_seguimiento: str
    numero_legajo: str | None
    apellido: str
    nombre: str
    dni: str
    email: str
    estado: EstadoLegajo
    cohorte: str
    carreras: list[str]
    solicita_beca: bool
    tipo_beca: TipoBeca | None
    documentos_cargados: int
    documentos_requeridos: int
    fecha_inscripcion: datetime | None


@dataclass(frozen=True)
class PaginaLegajos:
    items: list[LegajoListado]
    total: int
    page: int
    size: int


def criterios_desde(filtros: FiltrosBusqueda) -> CriteriosBusqueda:
    """Interpreta `q`: solo dígitos es un DNI exacto; si no, una parte del apellido.

    El apellido pide 3 letras como mínimo: con menos traería medio padrón y no le sirve a nadie.
    Un `q` vacío o con solo espacios es lo mismo que no mandarlo.
    """
    q = (filtros.q or "").strip()
    dni = apellido = None
    if q.isdigit():
        dni = q
    elif q:
        if len(q) < MINIMO_LETRAS_APELLIDO:
            raise ErrorDeValidacion(MENSAJE_APELLIDO_CORTO, campo="q")
        apellido = q
    return CriteriosBusqueda(
        dni=dni,
        apellido=apellido,
        estado=filtros.estado,
        cohorte_id=filtros.cohorte_id,
        carrera_id=filtros.carrera_id,
        beca=filtros.beca,
    )


def buscar_legajos(filtros: FiltrosBusqueda, repo: BusquedaRepository) -> PaginaLegajos:
    criterios = criterios_desde(filtros)
    offset = (filtros.page - 1) * filtros.size
    filas = repo.buscar(criterios, offset, filtros.size)
    return PaginaLegajos(
        items=[a_listado(fila) for fila in filas],
        total=repo.contar(criterios),
        page=filtros.page,
        size=filtros.size,
    )


def a_listado(fila: FilaBusqueda) -> LegajoListado:
    """Cuenta los documentos con las reglas de Fran (F3), igual que el detalle.

    Los cargados son los requeridos menos los faltantes, no las filas de `documentos`: un PDF que
    ya no corresponde (el formulario de beca de alguien que después sacó la beca) no suma, y así
    nunca se ve "6 de 5".
    """
    tiene_titulo_posgrado = fila.titulo_posgrado is not None
    requeridos = documentos_requeridos(fila.solicita_beca, tiene_titulo_posgrado)
    faltantes = documentos_faltantes(fila.solicita_beca, tiene_titulo_posgrado, fila.tipos_cargados)
    return LegajoListado(
        id=fila.id,
        codigo_seguimiento=fila.codigo_seguimiento,
        numero_legajo=fila.numero_legajo,
        apellido=fila.apellido,
        nombre=fila.nombre,
        dni=fila.dni,
        email=fila.email,
        estado=fila.estado,
        cohorte=fila.cohorte,
        carreras=fila.carreras,
        solicita_beca=fila.solicita_beca,
        tipo_beca=fila.tipo_beca,
        documentos_cargados=len(requeridos) - len(faltantes),
        documentos_requeridos=len(requeridos),
        fecha_inscripcion=fila.fecha_inscripcion,
    )
