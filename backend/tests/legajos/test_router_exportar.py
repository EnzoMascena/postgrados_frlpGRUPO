"""`GET /legajos/exportar` contra la app real y la base de test.

El formato fino del Excel está en `test_excel_exporter.py`; acá, el contrato de punta a punta:
tipo de contenido, nombre del archivo, que tenga las mismas filas que la búsqueda, y los errores
y permisos.
"""

from datetime import UTC, datetime, timedelta
from io import BytesIO
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from openpyxl import load_workbook

from src.legajos.application.buscar_legajos import MENSAJE_APELLIDO_CORTO
from src.legajos.domain.estados import EstadoLegajo
from src.legajos.presentation.router import MEDIA_TYPE_XLSX
from src.shared.config import settings
from tests.fabricas import crear_carrera, crear_cohorte, crear_legajo

EXPORTAR = "/api/v1/legajos/exportar"
LISTADO = "/api/v1/legajos"
AHORA = datetime(2026, 11, 4, 12, 0, tzinfo=UTC)
CON_BECA = {"solicita_beca": True, "tipo_beca": "30"}


@pytest.fixture
def cohorte(session):
    return crear_cohorte(session, anio=2026, numero=1, nombre="Cohorte 2026")


@pytest.fixture
def carrera(session):
    return crear_carrera(session, nombre="Maestría en Tecnología Informática")


def _legajo(session, cohorte, carreras, minutos: int = 0, **campos):
    return crear_legajo(
        session, cohorte, carreras, created_at=AHORA - timedelta(minutes=minutos), **campos
    )


def _hoja(respuesta):
    return load_workbook(BytesIO(respuesta.content)).active


def _hoy() -> str:
    return datetime.now(ZoneInfo(settings.zona_horaria)).date().isoformat()


# --- El archivo ---


def test_descarga_un_xlsx_con_el_nombre_de_la_cohorte(
    client, session, headers_coordinador, cohorte, carrera
):
    _legajo(session, cohorte, [carrera])

    respuesta = client.get(
        EXPORTAR, params={"cohorte": str(cohorte.id)}, headers=headers_coordinador
    )

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"] == MEDIA_TYPE_XLSX
    assert respuesta.headers["content-disposition"] == (
        f'attachment; filename="inscriptos-cohorte2026-{_hoy()}.xlsx"'
    )


def test_sin_cohorte_el_archivo_dice_todas(client, headers_coordinador):
    respuesta = client.get(EXPORTAR, headers=headers_coordinador)

    assert respuesta.status_code == 200
    assert respuesta.headers["content-disposition"] == (
        f'attachment; filename="inscriptos-todas-{_hoy()}.xlsx"'
    )


def test_encabezados_en_negrita_filtro_activo_y_una_fila_por_legajo(
    client, session, headers_coordinador, cohorte, carrera
):
    _legajo(
        session,
        cohorte,
        [carrera],
        minutos=0,
        apellido="Pérez",
        nombre="Juan",
        dni="30111222",
        estado=EstadoLegajo.COMPLETADO,
        numero_legajo="26-001-001",
        fecha_inscripcion=AHORA,
    )
    _legajo(session, cohorte, [carrera], minutos=10, apellido="Gómez")

    hoja = _hoja(client.get(EXPORTAR, headers=headers_coordinador))

    assert all(celda.font.bold for celda in hoja[1])
    assert hoja.auto_filter.ref == "A1:F3"
    assert hoja.freeze_panes == "A2"
    # Los más nuevos primero, como la búsqueda.
    assert [celda.value for celda in hoja[2]] == [
        "26-001-001",
        "Pérez, Juan",
        "30111222",
        "COMPLETADO",
        "Maestría en Tecnología Informática",
        datetime(2026, 11, 4),
    ]
    assert hoja["B3"].value.startswith("Gómez, ")


def test_tiene_las_mismas_filas_que_la_busqueda_con_los_mismos_filtros(
    client, session, headers_coordinador, cohorte, carrera
):
    otra_cohorte = crear_cohorte(session, anio=2025, numero=1, nombre="Cohorte 2025")
    for minutos in range(3):
        _legajo(session, cohorte, [carrera], minutos=minutos, apellido="Rodríguez", **CON_BECA)
    _legajo(session, cohorte, [carrera], minutos=5, apellido="Rodríguez")  # sin beca
    _legajo(session, cohorte, [carrera], minutos=6, apellido="Pérez", **CON_BECA)
    _legajo(session, otra_cohorte, [carrera], minutos=7, apellido="Rodríguez", **CON_BECA)
    filtros = {"q": "rodr", "cohorte": str(cohorte.id), "beca": "true"}

    busqueda = client.get(LISTADO, params=filtros, headers=headers_coordinador).json()
    hoja = _hoja(client.get(EXPORTAR, params=filtros, headers=headers_coordinador))

    assert busqueda["total"] == 3
    assert hoja.max_row - 1 == busqueda["total"]
    assert [celda.value for celda in hoja["C"][1:]] == [fila["dni"] for fila in busqueda["items"]]


def test_buscar_sin_tildes_tambien_filtra_el_excel(
    client, session, headers_coordinador, cohorte, carrera
):
    buscado = _legajo(session, cohorte, [carrera], apellido="García")
    _legajo(session, cohorte, [carrera], minutos=1, apellido="Romero")
    filtros = {"q": "garcia", "cohorte": str(cohorte.id)}

    hoja = _hoja(client.get(EXPORTAR, params=filtros, headers=headers_coordinador))

    assert [celda.value for celda in hoja["C"][1:]] == [buscado.dni]


def test_no_pagina_aunque_haya_mas_de_una_pagina(
    client, session, headers_coordinador, cohorte, carrera
):
    for minutos in range(25):
        _legajo(session, cohorte, [carrera], minutos=minutos)

    hoja = _hoja(client.get(EXPORTAR, headers=headers_coordinador))

    assert hoja.max_row - 1 == 25


def test_sin_legajos_quedan_solo_los_encabezados(client, headers_coordinador):
    hoja = _hoja(client.get(EXPORTAR, headers=headers_coordinador))

    assert hoja.max_row == 1


# --- Errores ---


def test_apellido_de_2_letras_da_422(client, headers_coordinador):
    respuesta = client.get(EXPORTAR, params={"q": "ro"}, headers=headers_coordinador)

    assert respuesta.status_code == 422
    assert respuesta.json()["message"] == MENSAJE_APELLIDO_CORTO
    assert respuesta.json()["field"] == "q"


def test_una_cohorte_que_no_existe_da_404(client, headers_coordinador):
    respuesta = client.get(EXPORTAR, params={"cohorte": str(uuid4())}, headers=headers_coordinador)

    assert respuesta.status_code == 404
    assert respuesta.json()["error"] == "NOT_FOUND"


def test_exportar_no_se_lee_como_un_id_de_legajo(client, headers_coordinador):
    # Si `/exportar` estuviera después de `/{legajo_id}`, "exportar" daría 422 por no ser UUID.
    respuesta = client.get(EXPORTAR, headers=headers_coordinador)

    assert respuesta.status_code == 200


# --- Permisos ---


def test_sin_token_da_401(client):
    assert client.get(EXPORTAR).status_code == 401


def test_con_un_docente_da_403(client, headers_docente):
    assert client.get(EXPORTAR, headers=headers_docente).status_code == 403
