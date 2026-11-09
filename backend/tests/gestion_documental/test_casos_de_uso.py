"""Casos de uso `subir_documento` y `obtener_documento` con piezas falsas: sin base ni disco."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from src.gestion_documental.application.obtener_documento import obtener_documento
from src.gestion_documental.application.subir_documento import (
    MENSAJE_LEGAJO_NO_EDITABLE,
    subir_documento,
)
from src.gestion_documental.domain.documento import DocumentoGuardado, LegajoParaDocumentos
from src.gestion_documental.domain.pdf import (
    MENSAJE_DEMASIADO_GRANDE,
    MENSAJE_NO_ES_PDF,
    MENSAJE_TIPO_NO_CORRESPONDE,
    ArchivoInvalido,
    validar_pdf,
)
from src.gestion_documental.domain.tipos import TAMANIO_MAXIMO_BYTES
from src.gestion_documental.domain.tipos import TipoDocumento as T
from src.inscripcion.domain.errores import LegajoNoEditable
from src.legajos.domain.estados import EstadoLegajo
from src.shared.errors import NoEncontrado

PDF = b"%PDF-1.7\nun pdf de prueba"


@dataclass(frozen=True)
class ArchivoFalso:
    path_storage: str
    checksum_sha256: str = "abc"
    tamanio_bytes: int = len(PDF)


class Disco:
    """Hace de `guardar_pdf` y de `borrar_pdf`, y anota qué se escribió y qué se borró."""

    def __init__(self) -> None:
        self.escritos: list[str] = []
        self.borrados: list[str] = []

    def guardar(self, contenido: bytes, cohorte_id: UUID, legajo_id: UUID) -> ArchivoFalso:
        path = f"uploads/{cohorte_id}/{legajo_id}/{len(self.escritos) + 1}.pdf"
        self.escritos.append(path)
        return ArchivoFalso(path)

    def borrar(self, path_storage: str) -> None:
        self.borrados.append(path_storage)


class RepoEnMemoria:
    def __init__(self, legajo: LegajoParaDocumentos | None, falla_al_guardar: bool = False):
        self._legajo = legajo
        self.documentos: dict[tuple[UUID, T], DocumentoGuardado] = {}
        self.falla_al_guardar = falla_al_guardar

    def legajo(self, legajo_id: UUID) -> LegajoParaDocumentos | None:
        return self._legajo if self._legajo and self._legajo.id == legajo_id else None

    def documento(self, documento_id: UUID) -> DocumentoGuardado | None:
        return next((d for d in self.documentos.values() if d.id == documento_id), None)

    def guardar_documento(self, legajo_id, tipo, path_storage, nombre, checksum, tamanio):
        if self.falla_al_guardar:
            raise RuntimeError("se cayó la base")
        anterior = self.documentos.get((legajo_id, tipo))
        documento = DocumentoGuardado(
            id=anterior.id if anterior else uuid4(),
            legajo_id=legajo_id,
            tipo=tipo,
            path_storage=path_storage,
            nombre_original=nombre,
            checksum_sha256=checksum,
            tamanio_bytes=tamanio,
            fecha_subida=datetime.now(UTC),
        )
        self.documentos[(legajo_id, tipo)] = documento
        return documento, anterior.path_storage if anterior else None


def un_legajo(estado=EstadoLegajo.BORRADOR, beca=False, posgrado=False) -> LegajoParaDocumentos:
    return LegajoParaDocumentos(uuid4(), uuid4(), estado, beca, posgrado)


def subir(repo, disco, legajo, tipo=T.DNI, contenido=PDF, nombre="dni.pdf"):
    return subir_documento(legajo.id, tipo, nombre, contenido, repo, disco.guardar, disco.borrar)


# --- validar_pdf ---


@pytest.mark.parametrize(
    ("contenido", "mensaje"),
    [
        (b"", MENSAJE_NO_ES_PDF),
        (b"PK\x03\x04 esto es un zip", MENSAJE_NO_ES_PDF),
        (b"hola %PDF-1.7", MENSAJE_NO_ES_PDF),
        (b"%PDF-" + b"0" * TAMANIO_MAXIMO_BYTES, MENSAJE_DEMASIADO_GRANDE),
    ],
)
def test_validar_pdf_frena_lo_que_no_es_pdf_o_pasa_los_5_mb(contenido, mensaje):
    with pytest.raises(ArchivoInvalido) as error:
        validar_pdf(contenido)

    assert (error.value.status_code, error.value.codigo) == (422, "ARCHIVO_INVALIDO")
    assert (error.value.campo, error.value.mensaje) == ("archivo", mensaje)


def test_un_pdf_de_exactamente_5_mb_se_acepta():
    validar_pdf(b"%PDF-" + b"0" * (TAMANIO_MAXIMO_BYTES - 5))


# --- subir_documento ---


def test_subir_escribe_el_archivo_y_guarda_la_fila():
    legajo = un_legajo()
    repo, disco = RepoEnMemoria(legajo), Disco()

    documento = subir(repo, disco, legajo)

    assert disco.escritos == [documento.path_storage]
    assert documento.path_storage.startswith(f"uploads/{legajo.cohorte_id}/{legajo.id}/")
    assert (documento.tipo, documento.nombre_original) == (T.DNI, "dni.pdf")
    assert disco.borrados == []


def test_subir_otro_del_mismo_tipo_lo_reemplaza_y_borra_el_archivo_viejo():
    legajo = un_legajo()
    repo, disco = RepoEnMemoria(legajo), Disco()
    primero = subir(repo, disco, legajo)

    segundo = subir(repo, disco, legajo, nombre="dni-nuevo.pdf")

    assert segundo.id == primero.id
    assert segundo.nombre_original == "dni-nuevo.pdf"
    assert disco.borrados == [primero.path_storage]


def test_si_falla_la_base_se_borra_el_archivo_recien_escrito():
    legajo = un_legajo()
    repo, disco = RepoEnMemoria(legajo, falla_al_guardar=True), Disco()

    with pytest.raises(RuntimeError):
        subir(repo, disco, legajo)

    assert disco.borrados == disco.escritos != []


@pytest.mark.parametrize(
    "estado", [e for e in EstadoLegajo if e not in (EstadoLegajo.BORRADOR, EstadoLegajo.OBSERVADO)]
)
def test_fuera_de_borrador_u_observado_da_409_y_no_escribe_nada(estado):
    legajo = un_legajo(estado=estado)
    repo, disco = RepoEnMemoria(legajo), Disco()

    with pytest.raises(LegajoNoEditable) as error:
        subir(repo, disco, legajo)

    assert (error.value.status_code, error.value.codigo) == (409, "LEGAJO_NO_EDITABLE")
    assert error.value.mensaje == MENSAJE_LEGAJO_NO_EDITABLE
    assert disco.escritos == []


def test_en_observado_se_puede_subir():
    legajo = un_legajo(estado=EstadoLegajo.OBSERVADO)

    subir(RepoEnMemoria(legajo), Disco(), legajo)


@pytest.mark.parametrize(
    ("beca", "posgrado", "tipo", "corresponde"),
    [
        (False, False, T.FORM_BECA, False),
        (False, False, T.TITULO_POSGRADO, False),
        (True, False, T.FORM_BECA, True),
        (False, True, T.TITULO_POSGRADO, True),
    ],
)
def test_solo_se_aceptan_los_tipos_que_le_corresponden_al_legajo(beca, posgrado, tipo, corresponde):
    legajo = un_legajo(beca=beca, posgrado=posgrado)
    repo, disco = RepoEnMemoria(legajo), Disco()

    if corresponde:
        subir(repo, disco, legajo, tipo=tipo)
        return
    with pytest.raises(ArchivoInvalido) as error:
        subir(repo, disco, legajo, tipo=tipo)
    assert (error.value.campo, error.value.mensaje) == ("tipo", MENSAJE_TIPO_NO_CORRESPONDE)
    assert disco.escritos == []


def test_un_archivo_que_no_es_pdf_no_llega_al_disco():
    legajo = un_legajo()
    repo, disco = RepoEnMemoria(legajo), Disco()

    with pytest.raises(ArchivoInvalido):
        subir(repo, disco, legajo, contenido=b"no soy un pdf")

    assert disco.escritos == []


def test_un_legajo_que_no_existe_da_404():
    repo, disco = RepoEnMemoria(None), Disco()

    with pytest.raises(NoEncontrado):
        subir(repo, disco, un_legajo())


@pytest.mark.parametrize(
    ("nombre", "guardado"),
    [
        (None, "documento.pdf"),
        ("   ", "documento.pdf"),
        ("C:\\fakepath\\dni.pdf", "dni.pdf"),
        ("../../etc/passwd", "passwd"),
        ("a" * 300 + ".pdf", "a" * 251 + ".pdf"),
    ],
)
def test_el_nombre_original_queda_sin_ruta_y_con_su_largo_maximo(nombre, guardado):
    legajo = un_legajo()

    documento = subir(RepoEnMemoria(legajo), Disco(), legajo, nombre=nombre)

    assert documento.nombre_original == guardado


# --- obtener_documento ---


def test_el_aspirante_obtiene_un_documento_de_su_legajo_y_el_coordinador_cualquiera():
    legajo = un_legajo()
    repo = RepoEnMemoria(legajo)
    documento = subir(repo, Disco(), legajo)

    assert obtener_documento(documento.id, repo, legajo.id) == documento
    assert obtener_documento(documento.id, repo) == documento


def test_un_documento_de_otro_legajo_da_el_mismo_404_que_uno_que_no_existe():
    legajo = un_legajo()
    repo = RepoEnMemoria(legajo)
    documento = subir(repo, Disco(), legajo)

    with pytest.raises(NoEncontrado) as de_otro:
        obtener_documento(documento.id, repo, uuid4())
    with pytest.raises(NoEncontrado) as inexistente:
        obtener_documento(uuid4(), repo)

    assert de_otro.value.mensaje == inexistente.value.mensaje
