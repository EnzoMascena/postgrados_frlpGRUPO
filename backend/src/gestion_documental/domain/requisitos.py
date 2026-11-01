"""Qué documentos tiene que presentar cada aspirante (US-CORE-002 y US-CORE-004). Python puro."""

from src.gestion_documental.domain.tipos import TipoDocumento

# Los que presenta todo aspirante, en el orden en que se muestran.
DOCUMENTOS_OBLIGATORIOS = (
    TipoDocumento.FORM_INSCRIPCION,
    TipoDocumento.DNI,
    TipoDocumento.TITULO_GRADO,
    TipoDocumento.PARTIDA,
    TipoDocumento.CUIT_CUIL,
)


def documentos_requeridos(solicita_beca: bool, tiene_titulo_posgrado: bool) -> list[TipoDocumento]:
    """Los 5 obligatorios, más el título de posgrado si declaró uno y el formulario de beca si la pidió."""
    requeridos = list(DOCUMENTOS_OBLIGATORIOS)
    if tiene_titulo_posgrado:
        requeridos.append(TipoDocumento.TITULO_POSGRADO)
    if solicita_beca:
        requeridos.append(TipoDocumento.FORM_BECA)
    return requeridos
