"""Tipos de documento que sube el aspirante. Python puro."""

from enum import StrEnum

TAMANIO_MAXIMO_BYTES = 5 * 1024 * 1024  # 5 MB (RF-CORE-002)


class TipoDocumento(StrEnum):
    FORM_INSCRIPCION = "FORM_INSCRIPCION"
    DNI = "DNI"
    TITULO_GRADO = "TITULO_GRADO"
    PARTIDA = "PARTIDA"
    CUIT_CUIL = "CUIT_CUIL"
    TITULO_POSGRADO = "TITULO_POSGRADO"
    FORM_BECA = "FORM_BECA"


# Lo que ve el aspirante y el coordinador: el checklist, el mensaje de "faltan documentos", etc.
NOMBRE_DOCUMENTO: dict[TipoDocumento, str] = {
    TipoDocumento.FORM_INSCRIPCION: "Formulario de preinscripción firmado",
    TipoDocumento.DNI: "Copia del DNI o pasaporte",
    TipoDocumento.TITULO_GRADO: "Copia del título de grado",
    TipoDocumento.PARTIDA: "Partida de nacimiento",
    TipoDocumento.CUIT_CUIL: "Constancia de CUIT / CUIL",
    TipoDocumento.TITULO_POSGRADO: "Copia del título de posgrado",
    TipoDocumento.FORM_BECA: "Formulario de beca firmado",
}
