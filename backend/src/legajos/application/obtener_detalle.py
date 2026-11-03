"""Caso de uso: el detalle de un legajo (plan §10, "Detalle del legajo").

Lo usan `GET /legajos/{id}` (vista coordinador) y `GET /seguimiento/{token}` de Fran (vista
aspirante). Los dos reciben el mismo cuerpo; el coordinador suma `historial` y
`accionesPermitidas`, y el aspirante, `puedeEditar`.
"""

from dataclasses import dataclass, fields
from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID

from src.cohortes.domain.tipos import TipoCarrera
from src.gestion_documental.domain.requisitos import armar_checklist
from src.gestion_documental.domain.tipos import TipoDocumento
from src.inscripcion.domain.tipos import ComoConocio, TipoBeca
from src.legajos.domain.entidades import RegistroAuditoria
from src.legajos.domain.estados import Accion, EstadoLegajo, acciones_permitidas
from src.shared.errors import NoEncontrado
from src.shared.roles import Rol

Vista = Literal["coordinador", "aspirante"]

MENSAJE_LEGAJO_NO_ENCONTRADO = "No encontramos el legajo"
ESTADOS_EDITABLES = frozenset({EstadoLegajo.BORRADOR, EstadoLegajo.OBSERVADO})


# --- Lo que trae el repositorio ---


@dataclass(frozen=True)
class CohorteResumen:
    id: UUID
    nombre: str
    anio: int


@dataclass(frozen=True)
class CarreraResumen:
    id: UUID
    nombre: str
    tipo: TipoCarrera


@dataclass(frozen=True)
class DocumentoCargado:
    """Los datos de un PDF que ya subió el aspirante (fila de `documentos`)."""

    id: UUID
    tipo: TipoDocumento
    nombre_original: str
    tamanio_bytes: int
    fecha_subida: datetime


@dataclass(frozen=True)
class FichaLegajo:
    """Los datos del legajo tal como están en la base, con su cohorte y sus carreras."""

    id: UUID
    codigo_seguimiento: str
    numero_legajo: str | None
    estado: EstadoLegajo
    cohorte: CohorteResumen
    carreras: list[CarreraResumen]
    apellido: str
    nombre: str
    nacionalidad: str
    dni: str
    telefono_movil: str
    telefono_fijo: str | None
    email: str
    email_alternativo: str | None
    domicilio: str
    ciudad: str
    provincia: str
    pais: str
    titulo_grado: str
    titulo_posgrado: str | None
    como_conocio: ComoConocio
    motivacion: str
    solicita_beca: bool
    tipo_beca: TipoBeca | None
    fecha_inscripcion: datetime | None
    fecha_aprobacion: datetime | None
    fecha_activacion: datetime | None
    created_at: datetime


class DetalleRepository(Protocol):
    def ficha(self, legajo_id: UUID) -> FichaLegajo | None:
        """Los datos del legajo con su cohorte y sus carreras (en su orden), o `None`."""
        ...

    def documentos_cargados(self, legajo_id: UUID) -> list[DocumentoCargado]:
        """Los PDFs que subió el aspirante (como mucho uno por tipo)."""
        ...

    def historial(self, legajo_id: UUID) -> list[RegistroAuditoria]:
        """Las filas de auditoría del legajo, de la más vieja a la más nueva."""
        ...


# --- Lo que devuelve el caso de uso ---


@dataclass(frozen=True)
class ItemDocumento:
    """Una fila del checklist con los datos del archivo, si ya está cargado."""

    tipo: TipoDocumento
    nombre: str
    obligatorio: bool
    cargado: bool
    documento_id: UUID | None = None
    nombre_original: str | None = None
    tamanio_bytes: int | None = None
    fecha_subida: datetime | None = None


@dataclass(frozen=True)
class LegajoDetalle(FichaLegajo):
    documentos: list[ItemDocumento]
    documentos_faltantes: list[TipoDocumento]
    ultima_observacion: str | None
    # Solo en la vista del coordinador:
    historial: list[RegistroAuditoria] | None
    acciones_permitidas: list[Accion] | None
    # Solo en la vista del aspirante:
    puede_editar: bool | None


def obtener_detalle(legajo_id: UUID, repo: DetalleRepository, vista: Vista) -> LegajoDetalle:
    ficha = repo.ficha(legajo_id)
    if ficha is None:
        raise NoEncontrado(MENSAJE_LEGAJO_NO_ENCONTRADO)

    documentos = _documentos(ficha, repo.documentos_cargados(legajo_id))
    historial = repo.historial(legajo_id)
    es_coordinador = vista == "coordinador"

    return LegajoDetalle(
        **{campo.name: getattr(ficha, campo.name) for campo in fields(FichaLegajo)},
        documentos=documentos,
        documentos_faltantes=[item.tipo for item in documentos if not item.cargado],
        ultima_observacion=_ultima_observacion(historial),
        historial=historial if es_coordinador else None,
        acciones_permitidas=(
            acciones_permitidas(ficha.estado, Rol.COORDINADOR) if es_coordinador else None
        ),
        puede_editar=None if es_coordinador else ficha.estado in ESTADOS_EDITABLES,
    )


def _documentos(ficha: FichaLegajo, cargados: list[DocumentoCargado]) -> list[ItemDocumento]:
    """El checklist de Fran (solo los que le corresponden) con los datos de cada archivo.

    Un documento cargado que ya no corresponde (por ejemplo, el formulario de beca de alguien que
    después sacó la beca) no aparece, igual que en `armar_checklist`.
    """
    por_tipo = {documento.tipo: documento for documento in cargados}
    # Igual que Fran en su envío (#44): un campo opcional vacío ya llega guardado como None.
    tiene_titulo_posgrado = ficha.titulo_posgrado is not None
    items = []
    for item in armar_checklist(ficha.solicita_beca, tiene_titulo_posgrado, por_tipo):
        archivo = por_tipo.get(item.tipo)
        items.append(
            ItemDocumento(
                tipo=item.tipo,
                nombre=item.nombre,
                # `ItemChecklist` de Fran no trae `obligatorio`: como `armar_checklist` lista solo
                # los documentos requeridos para este aspirante, todos son obligatorios.
                # Si algún día lista también opcionales, esto tiene que salir de su función.
                obligatorio=True,
                cargado=item.cargado,
                documento_id=archivo.id if archivo else None,
                nombre_original=archivo.nombre_original if archivo else None,
                tamanio_bytes=archivo.tamanio_bytes if archivo else None,
                fecha_subida=archivo.fecha_subida if archivo else None,
            )
        )
    return items


def _ultima_observacion(historial: list[RegistroAuditoria]) -> str | None:
    """El comentario del último OBSERVAR, aunque después haya corregido (el aspirante lo ve)."""
    for registro in reversed(historial):
        if registro.accion == Accion.OBSERVAR:
            return registro.comentario
    return None
