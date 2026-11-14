"""Caso de uso: el aspirante corrige los datos de su legajo desde su link (`PUT /seguimiento`).

Aplica las mismas reglas que la inscripción (plan §10), incluido el período abierto, y solo
deja editar en BORRADOR u OBSERVADO.
"""

from collections.abc import Callable
from uuid import UUID

from src.inscripcion.application.inscribir import controlar_formulario
from src.inscripcion.domain.errores import LegajoNoEditable
from src.inscripcion.domain.inscripcion import DatosInscripcion
from src.inscripcion.domain.repo import InscripcionRepository
from src.legajos.application.obtener_detalle import ESTADOS_EDITABLES
from src.shared.errors import NoEncontrado

MENSAJE_LEGAJO_NO_ENCONTRADO = "No encontramos el legajo"
MENSAJE_LEGAJO_NO_EDITABLE = (
    "Tu legajo ya fue enviado: solo podés modificarlo en borrador o si te lo observaron"
)

# El cuerpo del PUT no trae la cohorte (no se puede cambiar): se completa con la del legajo.
ArmarDatos = Callable[[UUID], DatosInscripcion]  # cohorte_id -> datos


def editar_legajo(legajo_id: UUID, armar_datos: ArmarDatos, repo: InscripcionRepository) -> None:
    legajo = repo.legajo_en_edicion(legajo_id)
    if legajo is None:
        raise NoEncontrado(MENSAJE_LEGAJO_NO_ENCONTRADO)
    # El mismo criterio que `puedeEditar` del detalle y que la subida de PDFs.
    if legajo.estado not in ESTADOS_EDITABLES:
        raise LegajoNoEditable(MENSAJE_LEGAJO_NO_EDITABLE)

    datos = armar_datos(legajo.cohorte_id)
    controlar_formulario(datos, repo, excepto=legajo.id)
    repo.actualizar_legajo(legajo.id, datos)
