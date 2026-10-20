"""Tests del seed: idempotente y fiel a lo que muestran los mocks del front.

Sembrar tarda unos segundos (bcrypt y 829 PDFs), así que el módulo siembra
UNA sola vez, dentro de una transacción propia que se deshace al final, y
cada test lee de ahí o vuelve a correr el seed para probar que no duplica.
"""

import hashlib
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlmodel import Session, func, select

from app.core.database import get_session
from app.core.security import hash_token_opaco
from app.core.storage import ruta_del_pdf
from app.main import app
from app.models import AccesoDocente, Asistencia, Clase, Cohorte, Cursada, Documento, Legajo
from app.models.enums import EstadoLegajo
from app.seed import HISTORICO, ID_ACCESO_DEMO, _id, sembrar, token_acceso_demo

HOY = date(2026, 10, 19)


@pytest.fixture(scope="module")
def sembrado(engine: Engine) -> Iterator[tuple[Session, dict[str, int]]]:
    """La base de test sembrada una vez para todo el módulo, y su resumen."""
    conexion = engine.connect()
    transaccion = conexion.begin()
    session = Session(bind=conexion, join_transaction_mode="create_savepoint")
    resumen = sembrar(session, hoy=HOY)
    yield session, resumen
    session.close()
    transaccion.rollback()
    conexion.close()


def _contar(session: Session, modelo) -> int:
    return session.exec(select(func.count()).select_from(modelo)).one()


def _por_estado(session: Session, anio: int) -> dict[EstadoLegajo, int]:
    filas = session.exec(
        select(Legajo.estado, func.count())
        .join(Cohorte, Cohorte.id == Legajo.cohorte_id)
        .where(Cohorte.anio == anio)
        .group_by(Legajo.estado)
    ).all()
    return dict(filas)


def test_la_primera_corrida_carga_el_dataset_completo(sembrado):
    _, resumen = sembrado
    assert resumen["usuarios"] == 2
    assert resumen["cohortes"] == 5
    assert resumen["legajos"] == 157
    assert resumen["seminarios"] == 5
    assert resumen["accesos_docente"] == 1


def test_la_segunda_corrida_no_agrega_nada(sembrado):
    session, _ = sembrado
    antes = {modelo: _contar(session, modelo) for modelo in (Legajo, Documento, Clase)}
    segunda = sembrar(session, hoy=HOY)
    assert {tabla: cantidad for tabla, cantidad in segunda.items() if cantidad} == {}
    assert {modelo: _contar(session, modelo) for modelo in antes} == antes


def test_vuelve_a_escribir_un_pdf_borrado_del_disco(sembrado):
    session, _ = sembrado
    documento = session.exec(select(Documento)).first()
    ruta_del_pdf(documento.path_storage).unlink()
    assert sembrar(session, hoy=HOY)["pdfs_en_disco"] == 1
    assert ruta_del_pdf(documento.path_storage).exists()


@pytest.mark.parametrize("anio", sorted(HISTORICO))
def test_cada_cohorte_pasada_tiene_los_totales_de_estadisticas(sembrado, anio):
    session, _ = sembrado
    inscriptos, graduados, desgranados, activos, _ralentizados = HISTORICO[anio]
    estados = _por_estado(session, anio)
    assert sum(estados.values()) == inscriptos
    assert estados[EstadoLegajo.GRADUADO] == graduados
    assert estados[EstadoLegajo.BAJA] == desgranados
    assert estados[EstadoLegajo.ACTIVO] == activos


def test_2026_tiene_todos_los_estados_del_workflow(sembrado):
    session, _ = sembrado
    estados = _por_estado(session, 2026)
    assert sum(estados.values()) == 20
    # Graduados y bajas solo hay en las cohortes pasadas.
    assert set(estados) == set(EstadoLegajo) - {EstadoLegajo.GRADUADO, EstadoLegajo.BAJA}


def test_hay_completados_de_menos_y_de_mas_de_30_dias(sembrado):
    # Para probar el vencimiento automático de la reserva (BR-005).
    session, _ = sembrado
    lucia = session.get(Legajo, _id("legajo", "dash-i4"))
    diego = session.get(Legajo, _id("legajo", "dash-i5"))
    ahora = datetime.combine(HOY, datetime.min.time(), tzinfo=UTC)
    assert ahora - lucia.fecha_completado < timedelta(days=30)
    assert ahora - diego.fecha_completado > timedelta(days=30)


def test_la_grilla_de_gps_es_la_de_la_planilla(sembrado):
    session, _ = sembrado
    cursada_enzo = session.get(Cursada, _id("cursada", "GPS", "dash-i1"))
    asistencias = session.exec(
        select(Clase.fecha, Asistencia.presente)
        .join(Clase, Clase.id == Asistencia.clase_id)
        .where(Asistencia.cursada_id == cursada_enzo.id)
        .order_by(Clase.fecha)
    ).all()
    dictadas = "".join("P" if presente else "A" for fecha, presente in asistencias if fecha <= HOY)
    assert dictadas == "PPAPPP"
    assert asistencias[-1][0] > HOY  # y una clase futura


def test_los_usuarios_del_seed_inician_sesion(sembrado):
    session, _ = sembrado
    app.dependency_overrides[get_session] = lambda: session
    try:
        with TestClient(app) as cliente:
            for email, clave, rol in (
                ("admin@fenix.test", "Admin1234!", "COORDINADOR"),
                ("cpr@fenix.test", "Cpr1234!", "CPR"),
            ):
                login = cliente.post("/api/v1/auth/login", json={"email": email, "password": clave})
                assert login.status_code == 200
                token = login.json()["accessToken"]
                me = cliente.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
                assert me.json()["rol"] == rol
    finally:
        app.dependency_overrides.clear()


def test_el_link_docente_impreso_es_vigente(sembrado):
    session, _ = sembrado
    acceso = session.get(AccesoDocente, ID_ACCESO_DEMO)
    assert acceso.token_hash == hash_token_opaco(token_acceso_demo())
    assert acceso.expira_en > datetime.now(UTC)


def test_cada_documento_tiene_su_pdf_con_el_checksum_guardado(sembrado):
    session, _ = sembrado
    for documento in session.exec(select(Documento)).all():
        contenido = ruta_del_pdf(documento.path_storage).read_bytes()
        assert contenido.startswith(b"%PDF")
        assert hashlib.sha256(contenido).hexdigest() == documento.checksum_sha256
