"""Las restricciones de la base de datos: lo que la base garantiza aunque el código se equivoque.

Cada test provoca la violación y comprueba que salte *esa* restricción (por su nombre), no otra.
"""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import func, select

from src.autenticacion.infrastructure.orm_models import ROLES_CON_USUARIO
from src.gestion_documental.domain.tipos import TAMANIO_MAXIMO_BYTES, TipoDocumento
from src.gestion_documental.infrastructure.orm_models import DocumentoORM
from src.inscripcion.infrastructure.orm_models import TokenSeguimientoORM
from src.legajos.domain.estados import EstadoLegajo
from src.legajos.infrastructure.orm_models import (
    AuditoriaLegajoORM,
    LegajoCarreraORM,
    LegajoORM,
)
from src.shared.orm import ahora_utc
from src.shared.roles import Rol
from tests.fabricas import (
    crear_carrera,
    crear_cohorte,
    crear_legajo,
    crear_usuario,
)


def _documento(legajo, tipo=TipoDocumento.DNI, tamanio=1000) -> DocumentoORM:
    return DocumentoORM(
        legajo_id=legajo.id,
        tipo=str(tipo),
        path_storage=f"uploads/{uuid.uuid4()}.pdf",
        nombre_original="documento.pdf",
        checksum_sha256="0" * 64,
        tamanio_bytes=tamanio,
    )


def _contar(session, modelo, **filtros) -> int:
    consulta = select(func.count()).select_from(modelo)
    for columna, valor in filtros.items():
        consulta = consulta.where(getattr(modelo, columna) == valor)
    return session.exec(consulta).one()


# --- legajos: únicos --------------------------------------------------------------------------


def test_un_legajo_con_los_valores_por_defecto_de_la_fabrica_es_valido(session):
    legajo = crear_legajo(session, crear_cohorte(session), [crear_carrera(session)])

    assert legajo.estado == EstadoLegajo.BORRADOR
    assert len(legajo.codigo_seguimiento) == 8
    assert legajo.numero_legajo is None
    assert legajo.created_at is not None


def test_el_dni_repetido_en_la_misma_cohorte_falla(session):
    cohorte, carrera = crear_cohorte(session), crear_carrera(session)
    crear_legajo(session, cohorte, [carrera], dni="30456789")

    with pytest.raises(IntegrityError, match="uq_legajos_cohorte_dni"):
        crear_legajo(session, cohorte, [carrera], dni="30456789")


def test_el_mismo_dni_en_otra_cohorte_se_permite(session):
    carrera = crear_carrera(session)
    crear_legajo(session, crear_cohorte(session, anio=2026), [carrera], dni="30456789")

    otro = crear_legajo(session, crear_cohorte(session, anio=2027), [carrera], dni="30456789")

    assert otro.dni == "30456789"


def test_el_email_repetido_en_la_misma_cohorte_falla(session):
    cohorte, carrera = crear_cohorte(session), crear_carrera(session)
    crear_legajo(session, cohorte, [carrera], email="ana@example.com")

    with pytest.raises(IntegrityError, match="uq_legajos_cohorte_email"):
        crear_legajo(session, cohorte, [carrera], email="ana@example.com")


def test_el_mismo_email_en_otra_cohorte_se_permite(session):
    carrera = crear_carrera(session)
    crear_legajo(session, crear_cohorte(session, anio=2026), [carrera], email="ana@example.com")

    otro = crear_legajo(
        session, crear_cohorte(session, anio=2027), [carrera], email="ana@example.com"
    )

    assert otro.email == "ana@example.com"


def test_el_codigo_de_seguimiento_repetido_falla(session):
    cohorte, carrera = crear_cohorte(session), crear_carrera(session)
    crear_legajo(session, cohorte, [carrera], codigo_seguimiento="7F3A9C21")

    with pytest.raises(IntegrityError, match="uq_legajos_codigo_seguimiento"):
        crear_legajo(session, cohorte, [carrera], codigo_seguimiento="7F3A9C21")


def test_el_numero_de_legajo_repetido_falla_pero_varios_sin_numero_se_permiten(session):
    cohorte, carrera = crear_cohorte(session), crear_carrera(session)
    # Los legajos que todavía no se aprobaron no tienen número (NULL), y NULL no cuenta como repetido.
    crear_legajo(session, cohorte, [carrera])
    crear_legajo(session, cohorte, [carrera])
    crear_legajo(session, cohorte, [carrera], numero_legajo="26-001-001")

    with pytest.raises(IntegrityError, match="uq_legajos_numero_legajo"):
        crear_legajo(session, cohorte, [carrera], numero_legajo="26-001-001")


def test_un_legajo_con_una_cohorte_inexistente_falla(session):
    with pytest.raises(IntegrityError, match="foreign key"):
        crear_legajo(
            session, crear_cohorte(session), [crear_carrera(session)], cohorte_id=uuid.uuid4()
        )


# --- legajos: CHECK ---------------------------------------------------------------------------


@pytest.mark.parametrize("estado", list(EstadoLegajo))
def test_los_diez_estados_son_validos(session, estado):
    legajo = crear_legajo(session, crear_cohorte(session), [crear_carrera(session)], estado=estado)

    assert legajo.estado == estado


def test_un_estado_inventado_falla(session):
    with pytest.raises(IntegrityError, match="ck_legajos_estado"):
        crear_legajo(
            session, crear_cohorte(session), [crear_carrera(session)], estado="INEXISTENTE"
        )


def test_un_como_conocio_inventado_falla(session):
    with pytest.raises(IntegrityError, match="ck_legajos_como_conocio"):
        crear_legajo(
            session, crear_cohorte(session), [crear_carrera(session)], como_conocio="INEXISTENTE"
        )


def test_la_motivacion_de_49_caracteres_falla_y_la_de_50_se_acepta(session):
    cohorte, carrera = crear_cohorte(session), crear_carrera(session)

    legajo = crear_legajo(session, cohorte, [carrera], motivacion="x" * 50)
    assert len(legajo.motivacion) == 50

    with pytest.raises(IntegrityError, match="ck_legajos_motivacion"):
        crear_legajo(session, cohorte, [carrera], motivacion="x" * 49)


@pytest.mark.parametrize("tipo_beca", ["30", "100"])
def test_una_beca_con_su_tipo_es_valida(session, tipo_beca):
    legajo = crear_legajo(
        session,
        crear_cohorte(session),
        [crear_carrera(session)],
        solicita_beca=True,
        tipo_beca=tipo_beca,
    )

    assert legajo.tipo_beca == tipo_beca


def test_un_tipo_de_beca_sin_pedir_beca_falla(session):
    with pytest.raises(IntegrityError, match="ck_legajos_beca_coherente"):
        crear_legajo(
            session,
            crear_cohorte(session),
            [crear_carrera(session)],
            solicita_beca=False,
            tipo_beca="30",
        )


def test_pedir_beca_sin_indicar_el_tipo_falla(session):
    with pytest.raises(IntegrityError, match="ck_legajos_beca_coherente"):
        crear_legajo(
            session,
            crear_cohorte(session),
            [crear_carrera(session)],
            solicita_beca=True,
            tipo_beca=None,
        )


def test_un_tipo_de_beca_que_no_es_30_ni_100_falla(session):
    with pytest.raises(IntegrityError, match="ck_legajos_tipo_beca"):
        crear_legajo(
            session,
            crear_cohorte(session),
            [crear_carrera(session)],
            solicita_beca=True,
            tipo_beca="50",
        )


# --- legajo_carreras: BR-001 ------------------------------------------------------------------


def test_un_legajo_puede_tener_una_o_dos_carreras_en_orden(session):
    cohorte = crear_cohorte(session)
    primera, segunda = crear_carrera(session), crear_carrera(session)

    legajo = crear_legajo(session, cohorte, [primera, segunda])

    filas = session.exec(
        select(LegajoCarreraORM)
        .where(LegajoCarreraORM.legajo_id == legajo.id)
        .order_by(LegajoCarreraORM.orden)
    ).all()
    assert [(f.orden, f.carrera_id) for f in filas] == [(1, primera.id), (2, segunda.id)]


def test_una_tercera_carrera_falla_por_el_orden(session):
    cohorte = crear_cohorte(session)
    legajo = crear_legajo(session, cohorte, [crear_carrera(session), crear_carrera(session)])

    session.add(
        LegajoCarreraORM(legajo_id=legajo.id, orden=3, carrera_id=crear_carrera(session).id)
    )

    with pytest.raises(IntegrityError, match="ck_legajo_carreras_orden"):
        session.commit()


def test_dos_carreras_con_el_mismo_orden_fallan(session):
    legajo = crear_legajo(session, crear_cohorte(session), [crear_carrera(session)])

    session.add(
        LegajoCarreraORM(legajo_id=legajo.id, orden=1, carrera_id=crear_carrera(session).id)
    )

    with pytest.raises(IntegrityError, match="legajo_carreras_pkey"):
        session.commit()


def test_la_misma_carrera_dos_veces_en_un_legajo_falla(session):
    carrera = crear_carrera(session)
    legajo = crear_legajo(session, crear_cohorte(session), [carrera])

    session.add(LegajoCarreraORM(legajo_id=legajo.id, orden=2, carrera_id=carrera.id))

    with pytest.raises(IntegrityError, match="uq_legajo_carreras_legajo_carrera"):
        session.commit()


# --- documentos -------------------------------------------------------------------------------


def test_dos_documentos_del_mismo_tipo_en_un_legajo_fallan(session):
    legajo = crear_legajo(session, crear_cohorte(session), [crear_carrera(session)])
    session.add(_documento(legajo, TipoDocumento.DNI))
    session.commit()

    session.add(_documento(legajo, TipoDocumento.DNI))

    with pytest.raises(IntegrityError, match="uq_documentos_legajo_tipo"):
        session.commit()


def test_el_mismo_tipo_de_documento_en_otro_legajo_se_permite(session):
    cohorte, carrera = crear_cohorte(session), crear_carrera(session)
    uno = crear_legajo(session, cohorte, [carrera])
    otro = crear_legajo(session, cohorte, [carrera])

    session.add(_documento(uno, TipoDocumento.DNI))
    session.add(_documento(otro, TipoDocumento.DNI))
    session.commit()

    assert _contar(session, DocumentoORM) == 2


def test_un_tipo_de_documento_inventado_falla(session):
    legajo = crear_legajo(session, crear_cohorte(session), [crear_carrera(session)])

    session.add(_documento(legajo, tipo="INEXISTENTE"))

    with pytest.raises(IntegrityError, match="ck_documentos_tipo"):
        session.commit()


@pytest.mark.parametrize("tamanio", [0, TAMANIO_MAXIMO_BYTES + 1])
def test_un_documento_vacio_o_de_mas_de_5_mb_falla(session, tamanio):
    legajo = crear_legajo(session, crear_cohorte(session), [crear_carrera(session)])

    session.add(_documento(legajo, tamanio=tamanio))

    with pytest.raises(IntegrityError, match="ck_documentos_tamanio"):
        session.commit()


@pytest.mark.parametrize("tamanio", [1, TAMANIO_MAXIMO_BYTES])
def test_un_documento_de_1_byte_o_de_exactamente_5_mb_se_acepta(session, tamanio):
    legajo = crear_legajo(session, crear_cohorte(session), [crear_carrera(session)])

    session.add(_documento(legajo, tamanio=tamanio))
    session.commit()

    assert _contar(session, DocumentoORM, legajo_id=legajo.id) == 1


# --- qué pasa al borrar un legajo -------------------------------------------------------------


def test_borrar_un_legajo_borra_sus_documentos_carreras_y_tokens(session):
    legajo = crear_legajo(session, crear_cohorte(session), [crear_carrera(session)])
    legajo_id = legajo.id
    session.add(_documento(legajo))
    session.add(
        TokenSeguimientoORM(legajo_id=legajo_id, token_hash="a" * 64, expira_en=ahora_utc())
    )
    session.commit()

    session.delete(legajo)
    session.commit()

    assert _contar(session, LegajoORM, id=legajo_id) == 0
    assert _contar(session, DocumentoORM, legajo_id=legajo_id) == 0
    assert _contar(session, LegajoCarreraORM, legajo_id=legajo_id) == 0
    assert _contar(session, TokenSeguimientoORM, legajo_id=legajo_id) == 0


def test_no_se_puede_borrar_un_legajo_que_tiene_auditoria(session):
    legajo = crear_legajo(session, crear_cohorte(session), [crear_carrera(session)])
    session.add(
        AuditoriaLegajoORM(
            legajo_id=legajo.id,
            accion="ENVIAR",
            estado_anterior="BORRADOR",
            estado_nuevo="PENDIENTE",
            rol=str(Rol.ASPIRANTE),
        )
    )
    session.commit()

    session.delete(legajo)

    with pytest.raises(IntegrityError, match="auditoria_legajos"):
        session.commit()


def test_la_auditoria_de_una_accion_del_sistema_no_lleva_email(session):
    legajo = crear_legajo(session, crear_cohorte(session), [crear_carrera(session)])

    session.add(
        AuditoriaLegajoORM(
            legajo_id=legajo.id,
            accion="VENCER",
            estado_anterior="COMPLETADO",
            estado_nuevo="VENCIDO",
            rol=str(Rol.SISTEMA),
        )
    )
    session.commit()

    fila = session.exec(select(AuditoriaLegajoORM)).one()
    assert fila.usuario_email is None


# --- tokens de seguimiento --------------------------------------------------------------------


def test_el_hash_de_un_token_repetido_falla(session):
    legajo = crear_legajo(session, crear_cohorte(session), [crear_carrera(session)])
    session.add(
        TokenSeguimientoORM(legajo_id=legajo.id, token_hash="a" * 64, expira_en=ahora_utc())
    )
    session.commit()

    session.add(
        TokenSeguimientoORM(legajo_id=legajo.id, token_hash="a" * 64, expira_en=ahora_utc())
    )

    with pytest.raises(IntegrityError, match="uq_tokens_seguimiento_token_hash"):
        session.commit()


# --- cohortes y carreras ----------------------------------------------------------------------


@pytest.mark.parametrize("numero", [0, 1000])
def test_un_numero_de_cohorte_fuera_de_1_a_999_falla(session, numero):
    with pytest.raises(IntegrityError, match="ck_cohortes_numero"):
        crear_cohorte(session, numero=numero)


def test_la_misma_cohorte_anio_y_numero_dos_veces_falla(session):
    crear_cohorte(session, anio=2026, numero=1)

    with pytest.raises(IntegrityError, match="uq_cohortes_anio_numero"):
        crear_cohorte(session, anio=2026, numero=1, nombre="Otro nombre")


def test_el_nombre_de_cohorte_repetido_falla(session):
    crear_cohorte(session, anio=2026, nombre="Cohorte 2026")

    with pytest.raises(IntegrityError, match="uq_cohortes_nombre"):
        crear_cohorte(session, anio=2027, nombre="Cohorte 2026")


def test_el_nombre_de_carrera_repetido_falla(session):
    crear_carrera(session, nombre="Maestría en Tecnología Informática")

    with pytest.raises(IntegrityError, match="uq_carreras_nombre"):
        crear_carrera(session, nombre="Maestría en Tecnología Informática")


def test_un_tipo_de_carrera_inventado_falla(session):
    with pytest.raises(IntegrityError, match="ck_carreras_tipo"):
        crear_carrera(session, tipo="Licenciatura")


# --- usuarios ---------------------------------------------------------------------------------


@pytest.mark.parametrize("rol", ROLES_CON_USUARIO)
def test_los_roles_que_inician_sesion_son_validos(session, rol):
    assert crear_usuario(session, rol=rol).rol == rol


@pytest.mark.parametrize("rol", [Rol.ASPIRANTE, Rol.SISTEMA])
def test_el_aspirante_y_el_sistema_no_tienen_usuario(session, rol):
    with pytest.raises(IntegrityError, match="ck_usuarios_rol"):
        crear_usuario(session, rol=rol)


def test_el_email_de_usuario_repetido_falla(session):
    crear_usuario(session, email="admin@fenix.test")

    with pytest.raises(IntegrityError, match="uq_usuarios_email"):
        crear_usuario(session, email="admin@fenix.test")
