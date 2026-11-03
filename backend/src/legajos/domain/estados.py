"""Máquina de estados del legajo (US-CORE-005, ADR-004). Python puro: sin FastAPI ni SQLModel.

La tabla `TRANSICIONES` es la del plan §9: para cada acción, desde qué estados se puede, a qué
estado lleva y qué roles la pueden hacer. `ServicioEstados` la consulta antes de cada cambio.
"""

from dataclasses import dataclass
from enum import StrEnum

from src.shared.errors import Conflicto, ErrorDeValidacion, SinPermiso
from src.shared.roles import Rol

MENSAJE_SIN_PERMISO = "No tenés permiso para esta acción"
MENSAJE_COMENTARIO_OBLIGATORIO = (
    "Escribí un comentario de al menos 5 caracteres para observar el legajo"
)
LARGO_MINIMO_OBSERVACION = 5


class EstadoLegajo(StrEnum):
    BORRADOR = "BORRADOR"
    PENDIENTE = "PENDIENTE"
    EN_REVISION = "EN_REVISION"
    OBSERVADO = "OBSERVADO"
    COMPLETADO = "COMPLETADO"
    ACTIVO = "ACTIVO"
    VENCIDO = "VENCIDO"
    RECHAZADO = "RECHAZADO"
    BAJA = "BAJA"
    GRADUADO = "GRADUADO"


class Accion(StrEnum):
    ENVIAR = "ENVIAR"
    REVISAR = "REVISAR"
    OBSERVAR = "OBSERVAR"
    CORREGIR = "CORREGIR"
    APROBAR = "APROBAR"
    RECHAZAR = "RECHAZAR"
    MATRICULAR = "MATRICULAR"
    VENCER = "VENCER"
    GRADUAR = "GRADUAR"
    DAR_DE_BAJA = "DAR_DE_BAJA"


@dataclass(frozen=True)
class Transicion:
    desde: frozenset[EstadoLegajo]
    hacia: EstadoLegajo
    roles: frozenset[Rol]


class TransicionInvalida(Conflicto):
    codigo = "TRANSICION_INVALIDA"


def _transicion(desde: EstadoLegajo, hacia: EstadoLegajo, rol: Rol) -> Transicion:
    return Transicion(desde=frozenset({desde}), hacia=hacia, roles=frozenset({rol}))


TRANSICIONES: dict[Accion, Transicion] = {
    Accion.ENVIAR: _transicion(EstadoLegajo.BORRADOR, EstadoLegajo.PENDIENTE, Rol.ASPIRANTE),
    Accion.REVISAR: _transicion(EstadoLegajo.PENDIENTE, EstadoLegajo.EN_REVISION, Rol.COORDINADOR),
    Accion.OBSERVAR: _transicion(EstadoLegajo.EN_REVISION, EstadoLegajo.OBSERVADO, Rol.COORDINADOR),
    Accion.CORREGIR: _transicion(EstadoLegajo.OBSERVADO, EstadoLegajo.PENDIENTE, Rol.ASPIRANTE),
    Accion.APROBAR: _transicion(EstadoLegajo.EN_REVISION, EstadoLegajo.COMPLETADO, Rol.COORDINADOR),
    Accion.RECHAZAR: _transicion(EstadoLegajo.EN_REVISION, EstadoLegajo.RECHAZADO, Rol.COORDINADOR),
    Accion.MATRICULAR: _transicion(EstadoLegajo.COMPLETADO, EstadoLegajo.ACTIVO, Rol.COORDINADOR),
    Accion.VENCER: _transicion(EstadoLegajo.COMPLETADO, EstadoLegajo.VENCIDO, Rol.SISTEMA),
    Accion.GRADUAR: _transicion(EstadoLegajo.ACTIVO, EstadoLegajo.GRADUADO, Rol.SISTEMA),
    Accion.DAR_DE_BAJA: _transicion(EstadoLegajo.ACTIVO, EstadoLegajo.BAJA, Rol.COORDINADOR),
}


def validar_transicion(estado: EstadoLegajo, accion: Accion, rol: Rol) -> EstadoLegajo:
    """Devuelve el estado al que lleva `accion`, o levanta el error que corresponde.

    Primero el rol (403 `SinPermiso`) y después el estado (409 `TransicionInvalida`): así a
    quien no puede hacer la acción no le contamos en qué estado está el legajo.
    """
    transicion = TRANSICIONES[accion]
    if rol not in transicion.roles:
        raise SinPermiso(MENSAJE_SIN_PERMISO)
    if estado not in transicion.desde:
        raise TransicionInvalida(f"No se puede {accion} un legajo en estado {estado}")
    return transicion.hacia


def acciones_permitidas(estado: EstadoLegajo, rol: Rol) -> list[Accion]:
    """Las acciones que `rol` puede hacer sobre un legajo en `estado`, en el orden de `Accion`."""
    return [
        accion
        for accion, transicion in TRANSICIONES.items()
        if rol in transicion.roles and estado in transicion.desde
    ]


def validar_comentario(accion: Accion, comentario: str | None) -> None:
    """OBSERVAR exige un comentario de 5 caracteres o más; en las demás acciones es opcional."""
    if accion != Accion.OBSERVAR:
        return
    if comentario is None or len(comentario.strip()) < LARGO_MINIMO_OBSERVACION:
        raise ErrorDeValidacion(MENSAJE_COMENTARIO_OBLIGATORIO, campo="comentario")
