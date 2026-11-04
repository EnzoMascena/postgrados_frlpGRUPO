"""Caso de uso: buscar el PDF que alguien quiere descargar, y controlar que pueda verlo (NFR-S02).

El aspirante solo ve los documentos de su propio legajo; el coordinador, cualquiera. Que el
coordinador sea coordinador lo controla el router con `require_role`.
"""

from uuid import UUID

from src.gestion_documental.domain.documento import DocumentoGuardado
from src.gestion_documental.domain.repo import DocumentoRepository
from src.shared.errors import NoEncontrado

MENSAJE_DOCUMENTO_NO_ENCONTRADO = "No encontramos el documento"


def obtener_documento(
    documento_id: UUID, repo: DocumentoRepository, legajo_del_aspirante: UUID | None = None
) -> DocumentoGuardado:
    """`legajo_del_aspirante` es el legajo del link; `None` cuando lo pide el coordinador.

    Un documento de otro legajo da el mismo 404 que uno que no existe: así no se puede averiguar
    qué ids existen probando links.
    """
    documento = repo.documento(documento_id)
    if documento is None:
        raise NoEncontrado(MENSAJE_DOCUMENTO_NO_ENCONTRADO)
    if legajo_del_aspirante is not None and documento.legajo_id != legajo_del_aspirante:
        raise NoEncontrado(MENSAJE_DOCUMENTO_NO_ENCONTRADO)
    return documento
