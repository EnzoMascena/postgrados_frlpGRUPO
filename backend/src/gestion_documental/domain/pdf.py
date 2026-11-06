"""Qué se acepta como PDF del aspirante (US-CORE-003, ADR-002). Python puro.

El tipo real se mira en los primeros bytes del archivo: la extensión y el Content-Type los
elige quien sube el archivo, así que no prueban nada.
"""

from src.gestion_documental.domain.tipos import TAMANIO_MAXIMO_BYTES
from src.shared.errors import ErrorDeValidacion

# Todo PDF empieza con estos bytes ("magic bytes").
FIRMA_PDF = b"%PDF-"

# Mensajes del SRS.
MENSAJE_NO_ES_PDF = "Solo se aceptan archivos en formato PDF"
MENSAJE_DEMASIADO_GRANDE = "El archivo es demasiado grande. Máximo permitido: 5MB"
MENSAJE_TIPO_NO_CORRESPONDE = "Este documento no corresponde a tu inscripción"


class ArchivoInvalido(ErrorDeValidacion):
    codigo = "ARCHIVO_INVALIDO"


def validar_pdf(contenido: bytes) -> None:
    """Frena un archivo de más de 5 MB o que no es un PDF de verdad (uno vacío tampoco lo es)."""
    if len(contenido) > TAMANIO_MAXIMO_BYTES:
        raise ArchivoInvalido(MENSAJE_DEMASIADO_GRANDE, campo="archivo")
    if not contenido.startswith(FIRMA_PDF):
        raise ArchivoInvalido(MENSAJE_NO_ES_PDF, campo="archivo")
