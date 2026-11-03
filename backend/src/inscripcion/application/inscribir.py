"""Caso de uso: el aspirante completa el formulario y queda su legajo en BORRADOR (US-CORE-001).

Recibe por parámetro el repositorio y las funciones que crean el link y lo mandan por email: no
sabe nada de la base ni del SMTP, y se testea con piezas falsas.
"""

import secrets
from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

from src.inscripcion.domain.errores import PeriodoCerrado
from src.inscripcion.domain.inscripcion import (
    MENSAJE_DNI_REPETIDO,
    MENSAJE_EMAIL_REPETIDO,
    DatosInscripcion,
    mensaje_periodo_cerrado,
)
from src.inscripcion.domain.repo import InscripcionRepository
from src.legajos.domain.estados import EstadoLegajo
from src.shared.errors import Conflicto, ErrorDeValidacion

MENSAJE_COHORTE_INEXISTENTE = "La cohorte elegida no existe"
MENSAJE_CARRERA_NO_DISPONIBLE = "Alguna de las carreras elegidas no está disponible"

CrearLink = Callable[[UUID], str]  # legajo_id -> token
EnviarLink = Callable[[str, str, str, str], bool]  # email, nombre, código, token -> ¿salió?


@dataclass(frozen=True)
class LegajoCreado:
    legajo_id: UUID
    codigo_seguimiento: str
    token: str
    estado: EstadoLegajo


def inscribir(
    datos: DatosInscripcion,
    repo: InscripcionRepository,
    crear_link: CrearLink,
    enviar_link: EnviarLink,
) -> LegajoCreado:
    cohorte = repo.obtener_cohorte(datos.cohorte_id)
    if cohorte is None:
        raise ErrorDeValidacion(MENSAJE_COHORTE_INEXISTENTE, campo="cohorteId")
    if not cohorte.inscripcion_abierta:
        raise PeriodoCerrado(mensaje_periodo_cerrado(cohorte.proxima_apertura))

    if repo.carreras_activas(datos.carrera_ids) != set(datos.carrera_ids):
        raise ErrorDeValidacion(MENSAJE_CARRERA_NO_DISPONIBLE, campo="carreraIds")

    if repo.existe_dni(datos.cohorte_id, datos.dni):
        raise Conflicto(MENSAJE_DNI_REPETIDO, campo="dni")
    if repo.existe_email(datos.cohorte_id, datos.email):
        raise Conflicto(MENSAJE_EMAIL_REPETIDO, campo="email")

    # 8 caracteres hexadecimales: lo que el aspirante dicta por teléfono si llama a consultar.
    codigo = secrets.token_hex(4).upper()
    legajo_id = repo.crear_legajo(datos, codigo)

    # Si el email no sale, la inscripción no se deshace: el token también vuelve en la respuesta.
    token = crear_link(legajo_id)
    enviar_link(datos.email, datos.nombre, codigo, token)
    return LegajoCreado(legajo_id, codigo, token, EstadoLegajo.BORRADOR)
