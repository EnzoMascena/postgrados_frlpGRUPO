"""Vocabulario del formulario de inscripción. Python puro."""

from enum import StrEnum


class ComoConocio(StrEnum):
    SITIO_WEB_UTN = "SITIO_WEB_UTN"
    OTROS_SITIOS = "OTROS_SITIOS"
    EGRESADOS = "EGRESADOS"
    COLEGAS = "COLEGAS"
    OTROS = "OTROS"


# Lo que ve el aspirante en el desplegable del formulario.
ETIQUETA_COMO_CONOCIO: dict[ComoConocio, str] = {
    ComoConocio.SITIO_WEB_UTN: "Sitio web UTN FRLP",
    ComoConocio.OTROS_SITIOS: "Otros sitios web",
    ComoConocio.EGRESADOS: "Egresados de la UTN FRLP",
    ComoConocio.COLEGAS: "Comentarios de colegas",
    ComoConocio.OTROS: "Otros",
}


class TipoBeca(StrEnum):
    TREINTA = "30"
    CIEN = "100"
