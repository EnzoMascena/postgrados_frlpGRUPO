"""`DocumentoRepository` con SQLModel: lee el legajo y guarda las filas de `documentos`."""

from uuid import UUID

from sqlmodel import Session, select

from src.gestion_documental.domain.documento import DocumentoGuardado, LegajoParaDocumentos
from src.gestion_documental.domain.tipos import TipoDocumento
from src.gestion_documental.infrastructure.orm_models import DocumentoORM
from src.legajos.domain.estados import EstadoLegajo
from src.legajos.infrastructure.orm_models import LegajoORM
from src.shared.orm import ahora_utc


class PgDocumentoRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def legajo(self, legajo_id: UUID) -> LegajoParaDocumentos | None:
        fila = self.session.get(LegajoORM, legajo_id)
        if fila is None:
            return None
        return LegajoParaDocumentos(
            id=fila.id,
            cohorte_id=fila.cohorte_id,
            estado=EstadoLegajo(fila.estado),
            solicita_beca=fila.solicita_beca,
            # El mismo criterio que el detalle de Luca: un opcional vacío se guarda como None.
            tiene_titulo_posgrado=fila.titulo_posgrado is not None,
        )

    def documento(self, documento_id: UUID) -> DocumentoGuardado | None:
        fila = self.session.get(DocumentoORM, documento_id)
        return _a_dominio(fila) if fila else None

    def guardar_documento(
        self,
        legajo_id: UUID,
        tipo: TipoDocumento,
        path_storage: str,
        nombre_original: str,
        checksum_sha256: str,
        tamanio_bytes: int,
    ) -> tuple[DocumentoGuardado, str | None]:
        # Hay como mucho uno por tipo (uq_documentos_legajo_tipo): si ya estaba, se pisa esa fila.
        # shortcut: dos subidas del mismo tipo al mismo tiempo darían 500 en la segunda; si pasa
        # en la práctica, atrapar el IntegrityError y reintentar como reemplazo.
        consulta = select(DocumentoORM).where(
            DocumentoORM.legajo_id == legajo_id, DocumentoORM.tipo == tipo.value
        )
        fila = self.session.exec(consulta).first()
        path_anterior = fila.path_storage if fila else None
        if fila is None:
            fila = DocumentoORM(
                legajo_id=legajo_id,
                tipo=tipo.value,
                path_storage=path_storage,
                nombre_original=nombre_original,
                checksum_sha256=checksum_sha256,
                tamanio_bytes=tamanio_bytes,
            )
        else:
            fila.path_storage = path_storage
            fila.nombre_original = nombre_original
            fila.checksum_sha256 = checksum_sha256
            fila.tamanio_bytes = tamanio_bytes
            fila.fecha_subida = ahora_utc()
        self.session.add(fila)
        self.session.commit()
        self.session.refresh(fila)
        return _a_dominio(fila), path_anterior


def _a_dominio(fila: DocumentoORM) -> DocumentoGuardado:
    return DocumentoGuardado(
        id=fila.id,
        legajo_id=fila.legajo_id,
        tipo=TipoDocumento(fila.tipo),
        path_storage=fila.path_storage,
        nombre_original=fila.nombre_original,
        checksum_sha256=fila.checksum_sha256,
        tamanio_bytes=fila.tamanio_bytes,
        fecha_subida=fila.fecha_subida,
    )
