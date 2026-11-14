"""Caso de uso: el aspirante envía su legajo a revisión (`POST /seguimiento/{token}/enviar`).

En BORRADOR es ENVIAR y en OBSERVADO es CORREGIR (plan §10). El cambio de estado, la auditoría
y el email los hace `ServicioEstados.cambiar` de Luca; acá se decide la acción y se controla,
antes, que estén todos los documentos.
"""

from collections.abc import Callable
from typing import Any
from uuid import UUID

from src.gestion_documental.domain.repo import DocumentoRepository
from src.gestion_documental.domain.requisitos import controlar_documentos_completos
from src.legajos.domain.estados import Accion, EstadoLegajo, validar_transicion
from src.shared.errors import NoEncontrado
from src.shared.roles import Actor, Rol

MENSAJE_LEGAJO_NO_ENCONTRADO = "No encontramos el legajo"

CambiarEstado = Callable[[UUID, Accion, Actor], Any]  # ServicioEstados.cambiar


def enviar_legajo(legajo_id: UUID, repo: DocumentoRepository, cambiar: CambiarEstado) -> Accion:
    legajo = repo.legajo(legajo_id)
    if legajo is None:
        raise NoEncontrado(MENSAJE_LEGAJO_NO_ENCONTRADO)

    accion = Accion.CORREGIR if legajo.estado == EstadoLegajo.OBSERVADO else Accion.ENVIAR
    # La transición va antes que los documentos: un legajo ya enviado tiene que dar 409
    # TRANSICION_INVALIDA, no un 422 por documentos que confunde al aspirante.
    validar_transicion(legajo.estado, accion, Rol.ASPIRANTE)
    controlar_documentos_completos(
        legajo.solicita_beca, legajo.tiene_titulo_posgrado, repo.tipos_cargados(legajo.id)
    )
    # El aspirante no tiene usuario: en la auditoría queda con rol ASPIRANTE y sin email.
    cambiar(legajo.id, accion, Actor(Rol.ASPIRANTE))
    return accion
