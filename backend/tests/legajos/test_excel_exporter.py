"""`generar_excel`: se abre el archivo generado con openpyxl y se mira cómo quedó. Sin base."""

from datetime import UTC, date, datetime
from io import BytesIO
from uuid import uuid4
from zipfile import ZipFile

import pytest
from openpyxl import load_workbook

from src.legajos.application.buscar_legajos import LegajoListado
from src.legajos.domain.estados import EstadoLegajo
from src.legajos.infrastructure.excel_exporter import ENCABEZADOS, generar_excel


def nuevo_listado(**campos) -> LegajoListado:
    datos = {
        "id": uuid4(),
        "codigo_seguimiento": "7F3A9C21",
        "numero_legajo": "26-001-001",
        "apellido": "Rodríguez",
        "nombre": "Ana Laura",
        "dni": "28456789",
        "email": "ana@example.com",
        "estado": EstadoLegajo.COMPLETADO,
        "cohorte": "Cohorte 2026",
        "carreras": ["Maestría en Ingeniería", "Especialización en Software"],
        "solicita_beca": False,
        "tipo_beca": None,
        "documentos_cargados": 5,
        "documentos_requeridos": 5,
        "fecha_inscripcion": datetime(2026, 11, 3, 14, 20, tzinfo=UTC),
    }
    return LegajoListado(**{**datos, **campos})


def abrir(contenido: bytes):
    return load_workbook(BytesIO(contenido)).active


def test_encabezados_en_negrita_en_la_primera_fila():
    hoja = abrir(generar_excel([nuevo_listado()]))

    assert [celda.value for celda in hoja[1]] == ENCABEZADOS
    assert all(celda.font.bold for celda in hoja[1])


def test_una_fila_por_legajo_con_las_seis_columnas():
    hoja = abrir(generar_excel([nuevo_listado()]))

    assert hoja.max_row == 2
    assert [celda.value for celda in hoja[2]] == [
        "26-001-001",
        "Rodríguez, Ana Laura",
        "28456789",
        "COMPLETADO",
        "Maestría en Ingeniería / Especialización en Software",
        datetime(2026, 11, 3),
    ]
    assert hoja["F2"].number_format == "DD/MM/YYYY"


def test_filtro_automatico_sobre_toda_la_tabla_y_encabezado_fijo():
    hoja = abrir(generar_excel([nuevo_listado(), nuevo_listado()]))

    assert hoja.auto_filter.ref == "A1:F3"
    assert hoja.freeze_panes == "A2"


def test_ancho_de_columna_segun_el_contenido():
    hoja = abrir(generar_excel([nuevo_listado(apellido="Fernández de la Torre")]))

    largo_nombre = len("Fernández de la Torre, Ana Laura")
    assert hoja.column_dimensions["B"].width == largo_nombre + 2
    assert hoja.column_dimensions["C"].width == len("28456789") + 2


def test_sin_numero_ni_fecha_quedan_vacias():
    hoja = abrir(generar_excel([nuevo_listado(numero_legajo=None, fecha_inscripcion=None)]))

    assert hoja["A2"].value is None
    assert hoja["F2"].value is None


def test_la_fecha_es_la_de_argentina_y_no_la_de_utc():
    # 02:00 UTC del 4 es todavía el 3 a las 23:00 en Argentina.
    hoja = abrir(
        generar_excel([nuevo_listado(fecha_inscripcion=datetime(2026, 11, 4, 2, 0, tzinfo=UTC))])
    )

    assert hoja["F2"].value.date() == date(2026, 11, 3)


def test_sin_legajos_quedan_solo_los_encabezados():
    hoja = abrir(generar_excel([]))

    assert hoja.max_row == 1
    assert hoja.auto_filter.ref == "A1:F1"


@pytest.mark.parametrize("apellido", ["=1+1", "+1+1", "-1+1", "@SUMA(A1)"])
def test_lo_que_escribe_el_aspirante_queda_como_texto_y_no_como_formula(apellido):
    hoja = abrir(generar_excel([nuevo_listado(apellido=apellido, nombre="=2+2", dni="=3+3")]))

    for celda in (hoja["B2"], hoja["C2"]):
        assert celda.data_type == "s"
    assert hoja["B2"].value == f"{apellido}, =2+2"
    assert hoja["C2"].value == "=3+3"


def test_un_apellido_que_empieza_con_igual_no_se_guarda_como_formula():
    contenido = generar_excel([nuevo_listado(apellido="=1+1", nombre="Ana")])

    hoja = abrir(contenido)
    assert hoja["B2"].data_type == "s"
    assert hoja["B2"].value == "=1+1, Ana"
    # Y en el XML del archivo no hay ninguna etiqueta de fórmula.
    with ZipFile(BytesIO(contenido)) as xlsx:
        assert b"<f>" not in xlsx.read("xl/worksheets/sheet1.xml")
