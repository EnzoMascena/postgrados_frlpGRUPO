"""Tabla de transiciones del legajo (plan §9), sin base ni HTTP."""

import pytest

from src.legajos.domain.estados import (
    MENSAJE_COMENTARIO_OBLIGATORIO,
    MENSAJE_SIN_PERMISO,
    Accion,
    EstadoLegajo,
    TransicionInvalida,
    acciones_permitidas,
    validar_comentario,
    validar_transicion,
)
from src.shared.errors import ErrorDeValidacion, SinPermiso
from src.shared.roles import Rol

E = EstadoLegajo

# Copia a mano de la tabla del plan §9: (acción, desde, hacia, rol que la puede hacer).
TABLA_DEL_PLAN = [
    (Accion.ENVIAR, E.BORRADOR, E.PENDIENTE, Rol.ASPIRANTE),
    (Accion.REVISAR, E.PENDIENTE, E.EN_REVISION, Rol.COORDINADOR),
    (Accion.OBSERVAR, E.EN_REVISION, E.OBSERVADO, Rol.COORDINADOR),
    (Accion.CORREGIR, E.OBSERVADO, E.PENDIENTE, Rol.ASPIRANTE),
    (Accion.APROBAR, E.EN_REVISION, E.COMPLETADO, Rol.COORDINADOR),
    (Accion.RECHAZAR, E.EN_REVISION, E.RECHAZADO, Rol.COORDINADOR),
    (Accion.MATRICULAR, E.COMPLETADO, E.ACTIVO, Rol.COORDINADOR),
    (Accion.VENCER, E.COMPLETADO, E.VENCIDO, Rol.SISTEMA),
    (Accion.GRADUAR, E.ACTIVO, E.GRADUADO, Rol.SISTEMA),
    (Accion.DAR_DE_BAJA, E.ACTIVO, E.BAJA, Rol.COORDINADOR),
]
DESDE = {accion: desde for accion, desde, _, _ in TABLA_DEL_PLAN}
ROL = {accion: rol for accion, _, _, rol in TABLA_DEL_PLAN}

ESTADOS_QUE_NO_CORRESPONDEN = [
    (accion, estado) for accion in Accion for estado in EstadoLegajo if estado != DESDE[accion]
]
ROLES_QUE_NO_CORRESPONDEN = [
    (accion, rol) for accion in Accion for rol in Rol if rol != ROL[accion]
]


def test_la_tabla_del_test_cubre_todas_las_acciones():
    assert set(DESDE) == set(Accion)


@pytest.mark.parametrize(("accion", "desde", "hacia", "rol"), TABLA_DEL_PLAN)
def test_cada_transicion_valida_con_su_rol_devuelve_el_estado_nuevo(accion, desde, hacia, rol):
    assert validar_transicion(desde, accion, rol) == hacia


@pytest.mark.parametrize(("accion", "estado"), ESTADOS_QUE_NO_CORRESPONDEN)
def test_una_accion_desde_un_estado_que_no_corresponde_da_409(accion, estado):
    with pytest.raises(TransicionInvalida) as error:
        validar_transicion(estado, accion, ROL[accion])

    assert error.value.status_code == 409
    assert error.value.codigo == "TRANSICION_INVALIDA"
    assert error.value.mensaje == f"No se puede {accion} un legajo en estado {estado}"


@pytest.mark.parametrize(("accion", "rol"), ROLES_QUE_NO_CORRESPONDEN)
def test_un_rol_que_no_corresponde_da_403(accion, rol):
    with pytest.raises(SinPermiso) as error:
        validar_transicion(DESDE[accion], accion, rol)

    assert error.value.status_code == 403
    assert error.value.mensaje == MENSAJE_SIN_PERMISO


def test_el_rol_se_valida_antes_que_el_estado():
    # El coordinador intenta ENVIAR un legajo que ni siquiera está en BORRADOR: 403, no 409.
    with pytest.raises(SinPermiso):
        validar_transicion(E.ACTIVO, Accion.ENVIAR, Rol.COORDINADOR)


@pytest.mark.parametrize(
    ("estado", "esperadas"),
    [
        (E.BORRADOR, []),
        (E.PENDIENTE, [Accion.REVISAR]),
        (E.EN_REVISION, [Accion.OBSERVAR, Accion.APROBAR, Accion.RECHAZAR]),
        (E.OBSERVADO, []),
        (E.COMPLETADO, [Accion.MATRICULAR]),
        (E.ACTIVO, [Accion.DAR_DE_BAJA]),
        (E.VENCIDO, []),
        (E.RECHAZADO, []),
        (E.BAJA, []),
        (E.GRADUADO, []),
    ],
)
def test_acciones_permitidas_del_coordinador_en_cada_estado(estado, esperadas):
    assert acciones_permitidas(estado, Rol.COORDINADOR) == esperadas


@pytest.mark.parametrize(
    ("estado", "rol", "esperadas"),
    [
        (E.BORRADOR, Rol.ASPIRANTE, [Accion.ENVIAR]),
        (E.OBSERVADO, Rol.ASPIRANTE, [Accion.CORREGIR]),
        (E.COMPLETADO, Rol.SISTEMA, [Accion.VENCER]),
        (E.EN_REVISION, Rol.DOCENTE, []),
    ],
)
def test_acciones_permitidas_de_otros_roles(estado, rol, esperadas):
    assert acciones_permitidas(estado, rol) == esperadas


@pytest.mark.parametrize("comentario", [None, "", "    ", "Ok", "Falt", "  ab  "])
def test_observar_sin_un_comentario_de_5_caracteres_da_422(comentario):
    with pytest.raises(ErrorDeValidacion) as error:
        validar_comentario(Accion.OBSERVAR, comentario)

    assert error.value.status_code == 422
    assert error.value.campo == "comentario"
    assert error.value.mensaje == MENSAJE_COMENTARIO_OBLIGATORIO


def test_observar_con_comentario_de_5_caracteres_o_mas_pasa():
    validar_comentario(Accion.OBSERVAR, "Falta")
    validar_comentario(Accion.OBSERVAR, "Falta la copia del título de grado legalizada")


@pytest.mark.parametrize("accion", [a for a in Accion if a != Accion.OBSERVAR])
def test_las_demas_acciones_no_exigen_comentario(accion):
    validar_comentario(accion, None)
