"""Qué documentos corresponden, cuáles faltan y cuándo se frena el envío (US-CORE-004).

Son reglas del dominio: no usan la app ni la base.
"""

import pytest

from src.gestion_documental.domain.requisitos import (
    DOCUMENTOS_OBLIGATORIOS,
    DocumentosFaltantes,
    ItemChecklist,
    armar_checklist,
    controlar_documentos_completos,
    documentos_faltantes,
    documentos_requeridos,
)
from src.gestion_documental.domain.tipos import TipoDocumento as T

OBLIGATORIOS = list(DOCUMENTOS_OBLIGATORIOS)


@pytest.mark.parametrize(
    ("solicita_beca", "tiene_titulo_posgrado", "esperados"),
    [
        (False, False, OBLIGATORIOS),
        (True, False, [*OBLIGATORIOS, T.FORM_BECA]),
        (False, True, [*OBLIGATORIOS, T.TITULO_POSGRADO]),
        (True, True, [*OBLIGATORIOS, T.TITULO_POSGRADO, T.FORM_BECA]),
    ],
)
def test_los_requeridos_dependen_de_la_beca_y_del_titulo_de_posgrado(
    solicita_beca, tiene_titulo_posgrado, esperados
):
    requeridos = documentos_requeridos(solicita_beca, tiene_titulo_posgrado)

    assert requeridos == esperados


def test_los_cinco_obligatorios_van_siempre():
    assert OBLIGATORIOS == [T.FORM_INSCRIPCION, T.DNI, T.TITULO_GRADO, T.PARTIDA, T.CUIT_CUIL]


def test_sin_nada_subido_faltan_todos_los_requeridos():
    faltantes = documentos_faltantes(True, True, cargados=[])

    assert faltantes == documentos_requeridos(True, True)


def test_con_todo_subido_no_falta_nada():
    faltantes = documentos_faltantes(True, False, cargados=documentos_requeridos(True, False))

    assert faltantes == []


def test_los_faltantes_salen_en_el_orden_del_checklist():
    faltantes = documentos_faltantes(
        False, False, cargados=[T.CUIT_CUIL, T.DNI, T.FORM_INSCRIPCION]
    )

    assert faltantes == [T.TITULO_GRADO, T.PARTIDA]


def test_un_documento_subido_que_ya_no_corresponde_no_cuenta():
    # Subió el formulario de beca y después desmarcó la beca.
    cargados = [*OBLIGATORIOS, T.FORM_BECA]

    assert documentos_faltantes(False, False, cargados) == []
    assert [item.tipo for item in armar_checklist(False, False, cargados)] == OBLIGATORIOS


def test_el_checklist_marca_cargado_o_pendiente_con_el_nombre_descriptivo():
    checklist = armar_checklist(True, False, cargados=[T.DNI])

    assert checklist[1] == ItemChecklist(
        tipo=T.DNI, nombre="Copia del DNI o pasaporte", cargado=True
    )
    assert checklist[-1] == ItemChecklist(
        tipo=T.FORM_BECA, nombre="Formulario de beca firmado", cargado=False
    )
    assert [item.cargado for item in checklist] == [False, True, False, False, False, False]


def test_con_todo_subido_el_control_deja_enviar():
    controlar_documentos_completos(False, True, cargados=documentos_requeridos(False, True))


def test_si_falta_alguno_el_control_frena_con_422_y_los_nombres_de_los_faltantes():
    cargados = [T.FORM_INSCRIPCION, T.DNI, T.PARTIDA]

    with pytest.raises(DocumentosFaltantes) as error:
        controlar_documentos_completos(False, False, cargados)

    assert error.value.status_code == 422
    assert error.value.codigo == "DOCUMENTOS_FALTANTES"
    assert error.value.mensaje == (
        "Faltan documentos obligatorios: Copia del título de grado, Constancia de CUIT / CUIL"
    )
