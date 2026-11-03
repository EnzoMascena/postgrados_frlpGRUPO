"""`PgLegajoRepository` contra la base de test (con rollback por test, ver conftest)."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import event
from sqlmodel import select

from src.cohortes.domain.tipos import TipoCarrera
from src.gestion_documental.domain.tipos import TipoDocumento
from src.gestion_documental.infrastructure.orm_models import DocumentoORM
from src.inscripcion.domain.tipos import ComoConocio, TipoBeca
from src.legajos.application.obtener_detalle import (
    CarreraResumen,
    CohorteResumen,
    DocumentoCargado,
)
from src.legajos.domain.entidades import DatosCohorte, Legajo, RegistroAuditoria
from src.legajos.domain.estados import Accion, EstadoLegajo
from src.legajos.infrastructure.orm_models import AuditoriaLegajoORM, LegajoORM
from src.legajos.infrastructure.pg_repository import PgLegajoRepository
from src.shared.errors import NoEncontrado
from src.shared.roles import Rol
from tests.fabricas import crear_carrera, crear_cohorte, crear_legajo

AHORA = datetime(2026, 11, 3, 15, 30, tzinfo=UTC)


@pytest.fixture
def repo(session) -> PgLegajoRepository:
    return PgLegajoRepository(session)


@pytest.fixture
def cohorte(session):
    return crear_cohorte(session, anio=2026, numero=1, nombre="Cohorte 2026")


@pytest.fixture
def carrera(session):
    return crear_carrera(session, nombre="Maestría en Tecnología Informática")


# --- obtener ---


def test_obtener_devuelve_el_legajo_del_dominio(repo, session, cohorte, carrera):
    fila = crear_legajo(
        session,
        cohorte,
        [carrera],
        estado=EstadoLegajo.COMPLETADO,
        numero_legajo="26-001-004",
        nombre="Ana Laura",
        apellido="Rodríguez",
        email="ana@example.com",
        fecha_aprobacion=AHORA,
    )

    legajo = repo.obtener(fila.id)

    assert legajo == Legajo(
        id=fila.id,
        cohorte_id=cohorte.id,
        estado=EstadoLegajo.COMPLETADO,
        numero_legajo="26-001-004",
        codigo_seguimiento=fila.codigo_seguimiento,
        nombre="Ana Laura",
        apellido="Rodríguez",
        email="ana@example.com",
        fecha_aprobacion=AHORA,
    )
    assert isinstance(legajo.estado, EstadoLegajo)


def test_obtener_un_legajo_inexistente_devuelve_none(repo):
    assert repo.obtener(uuid4()) is None


# --- siguiente_secuencial ---


def test_el_primer_secuencial_de_la_cohorte_es_1(repo, session, cohorte, carrera):
    crear_legajo(session, cohorte, [carrera], estado=EstadoLegajo.PENDIENTE)

    assert repo.siguiente_secuencial(cohorte.id) == 1


def test_el_secuencial_es_el_mayor_usado_mas_1_y_no_la_cantidad(repo, session, cohorte, carrera):
    crear_legajo(
        session, cohorte, [carrera], estado=EstadoLegajo.ACTIVO, numero_legajo="26-001-001"
    )
    # Un vencido conserva su número, y puede haber huecos (el 002 al 006 no existen).
    crear_legajo(
        session, cohorte, [carrera], estado=EstadoLegajo.VENCIDO, numero_legajo="26-001-007"
    )
    crear_legajo(session, cohorte, [carrera], estado=EstadoLegajo.EN_REVISION)

    assert repo.siguiente_secuencial(cohorte.id) == 8


def test_el_secuencial_no_mira_los_numeros_de_otra_cohorte(repo, session, cohorte, carrera):
    otra = crear_cohorte(session, anio=2026, numero=2)
    crear_legajo(session, otra, [carrera], estado=EstadoLegajo.ACTIVO, numero_legajo="26-002-030")

    assert repo.siguiente_secuencial(cohorte.id) == 1


def test_siguiente_secuencial_bloquea_la_fila_de_la_cohorte(repo, session, cohorte):
    # Dos transacciones a la vez no se pueden simular con el rollback por test: se mira que la
    # consulta a `cohortes` salga con FOR UPDATE.
    consultas: list[str] = []

    def anotar(conn, cursor, sql, parametros, contexto, executemany):
        consultas.append(sql)

    conexion = session.connection()
    event.listen(conexion, "before_cursor_execute", anotar)
    try:
        repo.siguiente_secuencial(cohorte.id)
    finally:
        event.remove(conexion, "before_cursor_execute", anotar)

    assert any("FROM cohortes" in sql and "FOR UPDATE" in sql for sql in consultas)


# --- datos_cohorte y nombres_carreras ---


def test_datos_cohorte(repo, cohorte):
    assert repo.datos_cohorte(cohorte.id) == DatosCohorte(
        anio=2026, numero=1, nombre="Cohorte 2026"
    )


def test_datos_de_una_cohorte_inexistente_da_no_encontrado(repo):
    with pytest.raises(NoEncontrado):
        repo.datos_cohorte(uuid4())


def test_nombres_carreras_en_el_orden_que_las_eligio(repo, session, cohorte, carrera):
    segunda = crear_carrera(session, nombre="Especialización en Ingeniería Gerencial")
    legajo = crear_legajo(session, cohorte, [segunda, carrera])

    assert repo.nombres_carreras(legajo.id) == [
        "Especialización en Ingeniería Gerencial",
        "Maestría en Tecnología Informática",
    ]


# --- guardar_cambio ---


def test_guardar_cambio_guarda_el_legajo_y_su_auditoria(repo, session, cohorte, carrera):
    fila = crear_legajo(session, cohorte, [carrera], estado=EstadoLegajo.EN_REVISION)
    legajo = repo.obtener(fila.id)
    legajo.estado = EstadoLegajo.COMPLETADO
    legajo.numero_legajo = "26-001-001"
    legajo.fecha_aprobacion = AHORA
    registro = RegistroAuditoria(
        legajo_id=fila.id,
        accion=Accion.APROBAR,
        estado_anterior=EstadoLegajo.EN_REVISION,
        estado_nuevo=EstadoLegajo.COMPLETADO,
        comentario=None,
        rol=Rol.COORDINADOR,
        usuario_email="coordinador@example.com",
        fecha=AHORA,
    )

    repo.guardar_cambio(legajo, registro)

    session.expire_all()  # que lo que sigue se lea de la base y no de la memoria de la sesión
    guardado = session.get(LegajoORM, fila.id)
    assert (guardado.estado, guardado.numero_legajo, guardado.fecha_aprobacion) == (
        "COMPLETADO",
        "26-001-001",
        AHORA,
    )
    auditoria = session.exec(
        select(AuditoriaLegajoORM).where(AuditoriaLegajoORM.legajo_id == fila.id)
    ).one()
    assert (
        auditoria.accion,
        auditoria.estado_anterior,
        auditoria.estado_nuevo,
        auditoria.comentario,
        auditoria.rol,
        auditoria.usuario_email,
        auditoria.created_at,
    ) == (
        "APROBAR",
        "EN_REVISION",
        "COMPLETADO",
        None,
        "COORDINADOR",
        "coordinador@example.com",
        AHORA,
    )


def test_guardar_cambio_de_un_legajo_inexistente_da_no_encontrado(repo):
    legajo = Legajo(
        id=uuid4(),
        cohorte_id=uuid4(),
        estado=EstadoLegajo.PENDIENTE,
        numero_legajo=None,
        codigo_seguimiento="AAAAAAAA",
        nombre="X",
        apellido="Y",
        email="x@example.com",
    )
    registro = RegistroAuditoria(
        legajo_id=legajo.id,
        accion=Accion.REVISAR,
        estado_anterior=EstadoLegajo.PENDIENTE,
        estado_nuevo=EstadoLegajo.EN_REVISION,
        comentario=None,
        rol=Rol.COORDINADOR,
        usuario_email=None,
        fecha=AHORA,
    )

    with pytest.raises(NoEncontrado):
        repo.guardar_cambio(legajo, registro)


# --- Consultas del detalle ---


def _subir_documento(session, legajo, tipo: TipoDocumento, nombre: str) -> DocumentoORM:
    # No hay fábrica de documentos todavía (las fábricas son de Enzo): se crea la fila acá.
    fila = DocumentoORM(
        legajo_id=legajo.id,
        tipo=tipo.value,
        path_storage=f"uploads/{legajo.cohorte_id}/{legajo.id}/{uuid4()}.pdf",
        nombre_original=nombre,
        checksum_sha256="0" * 64,
        tamanio_bytes=183_412,
        fecha_subida=AHORA,
    )
    session.add(fila)
    session.commit()
    session.refresh(fila)
    return fila


def _auditar(
    session, legajo, accion: Accion, desde, hacia, fecha, comentario=None, rol=Rol.COORDINADOR
):
    session.add(
        AuditoriaLegajoORM(
            legajo_id=legajo.id,
            accion=accion.value,
            estado_anterior=desde.value,
            estado_nuevo=hacia.value,
            comentario=comentario,
            rol=rol.value,
            usuario_email="coordinador@example.com" if rol == Rol.COORDINADOR else None,
            created_at=fecha,
        )
    )
    session.commit()


def test_ficha_trae_los_datos_con_la_cohorte_y_las_carreras_en_orden(
    repo, session, cohorte, carrera
):
    segunda = crear_carrera(
        session, nombre="Especialización en Ingeniería Gerencial", tipo=TipoCarrera.ESPECIALIZACION
    )
    fila = crear_legajo(
        session,
        cohorte,
        [segunda, carrera],
        estado=EstadoLegajo.PENDIENTE,
        dni="28456789",
        email="ana@example.com",
        solicita_beca=True,
        tipo_beca=TipoBeca.TREINTA.value,
        titulo_posgrado="Especialista en Redes",
        fecha_inscripcion=AHORA,
    )

    ficha = repo.ficha(fila.id)

    assert ficha.cohorte == CohorteResumen(id=cohorte.id, nombre="Cohorte 2026", anio=2026)
    assert ficha.carreras == [
        CarreraResumen(
            id=segunda.id,
            nombre="Especialización en Ingeniería Gerencial",
            tipo=TipoCarrera.ESPECIALIZACION,
        ),
        CarreraResumen(
            id=carrera.id, nombre="Maestría en Tecnología Informática", tipo=TipoCarrera.MAESTRIA
        ),
    ]
    assert (ficha.estado, ficha.dni, ficha.email, ficha.fecha_inscripcion) == (
        EstadoLegajo.PENDIENTE,
        "28456789",
        "ana@example.com",
        AHORA,
    )
    assert (ficha.solicita_beca, ficha.tipo_beca, ficha.titulo_posgrado) == (
        True,
        TipoBeca.TREINTA,
        "Especialista en Redes",
    )
    assert ficha.como_conocio == ComoConocio.EGRESADOS
    assert ficha.created_at == fila.created_at
    # Los enums vuelven como enums, no como texto.
    assert isinstance(ficha.estado, EstadoLegajo)
    assert isinstance(ficha.tipo_beca, TipoBeca)


def test_ficha_sin_beca_trae_tipo_beca_nulo(repo, session, cohorte, carrera):
    fila = crear_legajo(session, cohorte, [carrera])

    assert repo.ficha(fila.id).tipo_beca is None


def test_ficha_de_un_legajo_inexistente_es_none(repo):
    assert repo.ficha(uuid4()) is None


def test_documentos_cargados_trae_solo_los_del_legajo(repo, session, cohorte, carrera):
    legajo = crear_legajo(session, cohorte, [carrera])
    otro = crear_legajo(session, cohorte, [carrera])
    dni = _subir_documento(session, legajo, TipoDocumento.DNI, "dni.pdf")
    _subir_documento(session, otro, TipoDocumento.DNI, "dni-de-otro.pdf")

    assert repo.documentos_cargados(legajo.id) == [
        DocumentoCargado(
            id=dni.id,
            tipo=TipoDocumento.DNI,
            nombre_original="dni.pdf",
            tamanio_bytes=183_412,
            fecha_subida=AHORA,
        )
    ]


def test_documentos_cargados_sin_ninguno_es_lista_vacia(repo, session, cohorte, carrera):
    legajo = crear_legajo(session, cohorte, [carrera])

    assert repo.documentos_cargados(legajo.id) == []


def test_historial_va_de_la_fila_mas_vieja_a_la_mas_nueva(repo, session, cohorte, carrera):
    legajo = crear_legajo(session, cohorte, [carrera], estado=EstadoLegajo.OBSERVADO)
    # Se cargan desordenadas a propósito.
    _auditar(
        session,
        legajo,
        Accion.OBSERVAR,
        EstadoLegajo.EN_REVISION,
        EstadoLegajo.OBSERVADO,
        AHORA + timedelta(hours=2),
        comentario="Falta el DNI",
    )
    _auditar(
        session,
        legajo,
        Accion.ENVIAR,
        EstadoLegajo.BORRADOR,
        EstadoLegajo.PENDIENTE,
        AHORA,
        rol=Rol.ASPIRANTE,
    )
    _auditar(
        session,
        legajo,
        Accion.REVISAR,
        EstadoLegajo.PENDIENTE,
        EstadoLegajo.EN_REVISION,
        AHORA + timedelta(hours=1),
    )

    historial = repo.historial(legajo.id)

    assert [registro.accion for registro in historial] == [
        Accion.ENVIAR,
        Accion.REVISAR,
        Accion.OBSERVAR,
    ]
    assert historial[0] == RegistroAuditoria(
        legajo_id=legajo.id,
        accion=Accion.ENVIAR,
        estado_anterior=EstadoLegajo.BORRADOR,
        estado_nuevo=EstadoLegajo.PENDIENTE,
        comentario=None,
        rol=Rol.ASPIRANTE,
        usuario_email=None,
        fecha=AHORA,
    )
    assert historial[2].comentario == "Falta el DNI"


def test_historial_sin_cambios_es_lista_vacia(repo, session, cohorte, carrera):
    legajo = crear_legajo(session, cohorte, [carrera])

    assert repo.historial(legajo.id) == []
