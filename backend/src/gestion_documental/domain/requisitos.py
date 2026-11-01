"""Qué documentos tiene que presentar cada aspirante (US-CORE-002 y US-CORE-004). Python puro."""

from collections.abc import Iterable
from dataclasses import dataclass

from src.gestion_documental.domain.tipos import NOMBRE_DOCUMENTO, TipoDocumento
from src.shared.errors import ErrorDeValidacion

# Los que presenta todo aspirante, en el orden en que se muestran.
DOCUMENTOS_OBLIGATORIOS = (
    TipoDocumento.FORM_INSCRIPCION,
    TipoDocumento.DNI,
    TipoDocumento.TITULO_GRADO,
    TipoDocumento.PARTIDA,
    TipoDocumento.CUIT_CUIL,
)


class DocumentosFaltantes(ErrorDeValidacion):
    codigo = "DOCUMENTOS_FALTANTES"


@dataclass(frozen=True)
class ItemChecklist:
    """Una fila del "Cargado ✓ / Pendiente ✗" que ven el aspirante y el coordinador."""

    tipo: TipoDocumento
    nombre: str
    cargado: bool


def documentos_requeridos(solicita_beca: bool, tiene_titulo_posgrado: bool) -> list[TipoDocumento]:
    """Los 5 obligatorios, más el título de posgrado si declaró uno y el formulario de beca si la pidió."""
    requeridos = list(DOCUMENTOS_OBLIGATORIOS)
    if tiene_titulo_posgrado:
        requeridos.append(TipoDocumento.TITULO_POSGRADO)
    if solicita_beca:
        requeridos.append(TipoDocumento.FORM_BECA)
    return requeridos


def documentos_faltantes(
    solicita_beca: bool, tiene_titulo_posgrado: bool, cargados: Iterable[TipoDocumento]
) -> list[TipoDocumento]:
    """Los requeridos que todavía no subió. Uno subido que ya no corresponde no cuenta."""
    subidos = set(cargados)
    return [
        tipo
        for tipo in documentos_requeridos(solicita_beca, tiene_titulo_posgrado)
        if tipo not in subidos
    ]


def armar_checklist(
    solicita_beca: bool, tiene_titulo_posgrado: bool, cargados: Iterable[TipoDocumento]
) -> list[ItemChecklist]:
    subidos = set(cargados)
    return [
        ItemChecklist(tipo=tipo, nombre=NOMBRE_DOCUMENTO[tipo], cargado=tipo in subidos)
        for tipo in documentos_requeridos(solicita_beca, tiene_titulo_posgrado)
    ]


def controlar_documentos_completos(
    solicita_beca: bool, tiene_titulo_posgrado: bool, cargados: Iterable[TipoDocumento]
) -> None:
    """Frena ENVIAR y CORREGIR si falta algún documento (US-CORE-004)."""
    faltantes = documentos_faltantes(solicita_beca, tiene_titulo_posgrado, cargados)
    if faltantes:
        nombres = ", ".join(NOMBRE_DOCUMENTO[tipo] for tipo in faltantes)
        raise DocumentosFaltantes(f"Faltan documentos obligatorios: {nombres}")
