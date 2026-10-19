"""Tests del guardado seguro de PDFs (ASR-001, RF-CORE-002).

Cada test usa su propia carpeta temporal como STORAGE_PATH: no hace falta
base de datos y no queda basura entre tests.
"""

import hashlib
import io
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from app.core import config
from app.core.excepciones import ArchivoInvalido
from app.core.storage import (
    MENSAJE_MUY_GRANDE,
    MENSAJE_NO_ES_PDF,
    borrar_pdf,
    guardar_pdf,
    ruta_del_pdf,
)

PDF_MINIMO = b"%PDF-1.4\n1 0 obj << >> endobj\ntrailer << >>\n%%EOF\n"
CINCO_MB = 5 * 1024 * 1024


@pytest.fixture(autouse=True)
def storage_temporal(tmp_path, monkeypatch) -> Path:
    monkeypatch.setattr(config, "STORAGE_PATH", tmp_path)
    return tmp_path


def _archivos(carpeta: Path) -> list[Path]:
    return [p for p in carpeta.rglob("*") if p.is_file()]


def test_guarda_el_pdf_con_nombre_uuid_y_su_sha256(storage_temporal):
    # Arrange
    cohorte_id, legajo_id = uuid4(), uuid4()
    # Act
    guardado = guardar_pdf(io.BytesIO(PDF_MINIMO), cohorte_id, legajo_id)
    # Assert
    ruta = Path(guardado.path_storage)
    assert ruta.parts[:3] == ("uploads", str(cohorte_id), str(legajo_id))
    assert UUID(ruta.stem)  # el nombre en disco es un UUID, no el original
    assert ruta.suffix == ".pdf"
    assert guardado.checksum_sha256 == hashlib.sha256(PDF_MINIMO).hexdigest()
    assert guardado.tamanio_bytes == len(PDF_MINIMO)
    assert (storage_temporal / ruta).read_bytes() == PDF_MINIMO


@pytest.mark.parametrize(
    "contenido",
    [
        b"\xff\xd8\xff\xe0 un JPG renombrado a .pdf",
        b"MZ un ejecutable",
        b"",
        b" %PDF con un espacio adelante",
    ],
)
def test_rechaza_lo_que_no_empieza_con_los_magic_bytes_de_pdf(storage_temporal, contenido):
    with pytest.raises(ArchivoInvalido) as error:
        guardar_pdf(io.BytesIO(contenido), uuid4(), uuid4(), campo="dni")
    assert error.value.mensaje == MENSAJE_NO_ES_PDF
    assert error.value.campo == "dni"
    assert _archivos(storage_temporal) == []  # no quedó nada a medias


def test_acepta_un_pdf_de_exactamente_5_mb(storage_temporal):
    contenido = PDF_MINIMO + b"0" * (CINCO_MB - len(PDF_MINIMO))
    guardado = guardar_pdf(io.BytesIO(contenido), uuid4(), uuid4())
    assert guardado.tamanio_bytes == CINCO_MB


def test_rechaza_un_pdf_de_mas_de_5_mb_sin_dejar_el_parcial(storage_temporal):
    contenido = PDF_MINIMO + b"0" * CINCO_MB
    with pytest.raises(ArchivoInvalido, match="Máximo permitido: 5MB") as error:
        guardar_pdf(io.BytesIO(contenido), uuid4(), uuid4())
    assert error.value.mensaje == MENSAJE_MUY_GRANDE
    assert _archivos(storage_temporal) == []


def test_ruta_del_pdf_no_sale_del_almacenamiento(storage_temporal):
    with pytest.raises(ValueError, match="fuera del almacenamiento"):
        ruta_del_pdf("../../etc/passwd")


def test_borrar_pdf_lo_saca_del_disco(storage_temporal):
    guardado = guardar_pdf(io.BytesIO(PDF_MINIMO), uuid4(), uuid4())
    borrar_pdf(guardado.path_storage)
    assert not ruta_del_pdf(guardado.path_storage).exists()
    borrar_pdf(guardado.path_storage)  # borrar dos veces no falla
