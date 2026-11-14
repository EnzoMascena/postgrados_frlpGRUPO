"""El Excel de inscriptos del coordinador (US-CORE-008, plan §10), con openpyxl.

Encabezados en negrita, ancho de cada columna según el contenido, filtro automático sobre toda
la tabla y la fila de encabezados fija al bajar.

Lo que escribe el aspirante (apellido, nombre, DNI, carrera) va siempre como texto: openpyxl
toma como fórmula cualquier texto que empieza con "=", y alguien podría inscribirse con un
apellido "=HYPERLINK(...)" que el coordinador ejecuta al abrir el archivo (inyección de fórmulas).
"""

from collections.abc import Iterable
from datetime import date
from io import BytesIO
from typing import Any
from zoneinfo import ZoneInfo

from openpyxl import Workbook
from openpyxl.cell.cell import Cell
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from src.legajos.application.buscar_legajos import LegajoListado
from src.shared.config import settings

ENCABEZADOS = ["Nº Legajo", "Apellido y nombre", "DNI", "Estado", "Carrera", "Fecha inscripción"]
FORMATO_FECHA = "DD/MM/YYYY"
TITULO_HOJA = "Inscriptos"


def generar_excel(filas: Iterable[LegajoListado]) -> bytes:
    libro = Workbook()
    hoja = libro.active
    hoja.title = TITULO_HOJA

    hoja.append(ENCABEZADOS)
    for celda in hoja[1]:
        celda.font = Font(bold=True)

    for numero_fila, legajo in enumerate(filas, start=2):
        for numero_columna, valor in enumerate(_valores(legajo), start=1):
            _escribir(hoja.cell(row=numero_fila, column=numero_columna), valor)

    _ajustar_anchos(hoja)
    hoja.auto_filter.ref = hoja.dimensions
    hoja.freeze_panes = "A2"

    salida = BytesIO()
    libro.save(salida)
    return salida.getvalue()


def _valores(legajo: LegajoListado) -> list[Any]:
    return [
        legajo.numero_legajo or "",
        f"{legajo.apellido}, {legajo.nombre}",
        legajo.dni,
        legajo.estado.value,
        " / ".join(legajo.carreras),
        _fecha_local(legajo),
    ]


def _fecha_local(legajo: LegajoListado) -> date | None:
    """La fecha en la hora de Argentina: en la base está en UTC."""
    if legajo.fecha_inscripcion is None:
        return None
    return legajo.fecha_inscripcion.astimezone(ZoneInfo(settings.zona_horaria)).date()


def _escribir(celda: Cell, valor: Any) -> None:
    celda.value = valor
    if isinstance(valor, str):
        # Siempre texto, aunque empiece con "=", "+", "-" o "@": nunca una fórmula.
        celda.data_type = "s"
    elif isinstance(valor, date):
        celda.number_format = FORMATO_FECHA


def _ajustar_anchos(hoja: Any) -> None:
    for numero_columna, columna in enumerate(hoja.iter_cols(), start=1):
        largo = max(len(_como_texto(celda.value)) for celda in columna)
        hoja.column_dimensions[get_column_letter(numero_columna)].width = largo + 2


def _como_texto(valor: Any) -> str:
    if valor is None:
        return ""
    if isinstance(valor, date):
        return "dd/mm/aaaa"
    return str(valor)
