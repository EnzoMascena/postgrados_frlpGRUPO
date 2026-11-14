"""El seed (scripts/seed.py) contra la base de test.

`cargar_datos` no hace commit: acá se commitea después de cada corrida, como hace `main()`. Igual
todo queda dentro de la transacción del test y se deshace al terminar (ver conftest).
"""

import hashlib
from dataclasses import replace
from datetime import UTC, datetime

import pytest
from sqlalchemy import func
from sqlmodel import select

from scripts import seed
from scripts.seed import cargar_datos
from src.autenticacion.infrastructure.hashing import verificar_password
from src.autenticacion.infrastructure.orm_models import UsuarioORM
from src.cohortes.infrastructure.orm_models import CarreraORM, CohorteORM
from src.gestion_documental.domain.pdf import validar_pdf
from src.gestion_documental.domain.requisitos import documentos_requeridos
from src.gestion_documental.domain.tipos import TipoDocumento
from src.gestion_documental.infrastructure.almacenamiento import ruta_del_pdf
from src.gestion_documental.infrastructure.orm_models import DocumentoORM
from src.legajos.domain.estados import EstadoLegajo, TransicionInvalida
from src.legajos.infrastructure.orm_models import (
    AuditoriaLegajoORM,
    LegajoCarreraORM,
    LegajoORM,
)
from src.shared.config import settings
from src.shared.errors import ErrorDeValidacion
from src.shared.roles import Rol

EMAIL_COORDINADOR = "coordinador.seed@example.com"
CLAVE_COORDINADOR = "ClaveDelSeed1234!"

TABLAS = (
    CarreraORM,
    CohorteORM,
    UsuarioORM,
    LegajoORM,
    LegajoCarreraORM,
    AuditoriaLegajoORM,
    DocumentoORM,
)
DOCUMENTOS_DEL_SEED = 53  # 10 legajos enviados × 5, 4 formularios de beca, 1 que falta


@pytest.fixture(autouse=True)
def coordinador_configurado(monkeypatch):
    # En el CI no hay .env: el email y la clave del coordinador se ponen acá.
    monkeypatch.setattr(settings, "seed_coordinador_email", EMAIL_COORDINADOR)
    monkeypatch.setattr(settings, "seed_coordinador_password", CLAVE_COORDINADOR)


def _contar_filas(session) -> dict[str, int]:
    return {
        tabla.__tablename__: session.exec(select(func.count()).select_from(tabla)).one()
        for tabla in TABLAS
    }


def _legajo(session, apellido: str) -> LegajoORM:
    return session.exec(select(LegajoORM).where(LegajoORM.apellido == apellido)).one()


def test_correrlo_dos_veces_no_duplica_nada(session):
    primera = cargar_datos(session)
    session.commit()
    filas = _contar_filas(session)

    segunda = cargar_datos(session)
    session.commit()

    resumen = {
        "carreras": 3,
        "cohortes": 3,
        "coordinadores": 1,
        "legajos": 11,
        "documentos": DOCUMENTOS_DEL_SEED,
    }
    assert primera == {**resumen, "nuevos": 18 + DOCUMENTOS_DEL_SEED}
    assert segunda == {**resumen, "nuevos": 0}
    assert _contar_filas(session) == filas
    assert filas["legajos"] == 11
    assert filas["legajo_carreras"] == 11
    assert filas["documentos"] == DOCUMENTOS_DEL_SEED


def test_el_coordinador_entra_con_la_clave_de_la_configuracion(session):
    cargar_datos(session)
    session.commit()

    coordinador = session.exec(
        select(UsuarioORM).where(UsuarioORM.email == EMAIL_COORDINADOR)
    ).one()
    assert coordinador.rol == Rol.COORDINADOR
    assert coordinador.nombre == "María González"
    assert verificar_password(CLAVE_COORDINADOR, coordinador.password_hash)
    assert not verificar_password("otra-clave", coordinador.password_hash)


def test_el_completado_se_aprobo_hace_31_dias_para_vencer_en_la_demo(session):
    cargar_datos(session)
    session.commit()

    completado = _legajo(session, "Paz")
    assert completado.estado == EstadoLegajo.COMPLETADO
    assert completado.numero_legajo == "26-001-004"
    assert (datetime.now(UTC) - completado.fecha_aprobacion).days == 31
    assert completado.fecha_activacion is None


def test_cada_legajo_tiene_el_historial_que_lo_llevo_a_su_estado(session):
    cargar_datos(session)
    session.commit()

    for legajo in session.exec(select(LegajoORM)).all():
        historial = session.exec(
            select(AuditoriaLegajoORM)
            .where(AuditoriaLegajoORM.legajo_id == legajo.id)
            .order_by(AuditoriaLegajoORM.created_at)
        ).all()
        if legajo.estado == EstadoLegajo.BORRADOR:
            assert historial == []
            assert legajo.fecha_inscripcion is None
            continue
        # Empieza cuando el aspirante lo envió y termina en el estado que tiene hoy.
        assert historial[0].accion == "ENVIAR"
        assert historial[0].estado_anterior == EstadoLegajo.BORRADOR
        assert historial[0].created_at == legajo.fecha_inscripcion
        assert historial[-1].estado_nuevo == legajo.estado
        for fila in historial:
            esperado = EMAIL_COORDINADOR if fila.rol == Rol.COORDINADOR else None
            assert fila.usuario_email == esperado


def test_los_matriculados_tienen_numero_y_las_tres_fechas(session):
    cargar_datos(session)
    session.commit()

    activos = session.exec(
        select(LegajoORM)
        .where(LegajoORM.estado == EstadoLegajo.ACTIVO)
        .order_by(LegajoORM.numero_legajo)
    ).all()
    assert [legajo.numero_legajo for legajo in activos] == [
        "26-001-001",
        "26-001-002",
        "26-001-003",
    ]
    for legajo in activos:
        assert legajo.fecha_inscripcion < legajo.fecha_aprobacion < legajo.fecha_activacion
    assert _legajo(session, "López").numero_legajo is None  # PENDIENTE: sin número todavía


def test_los_legajos_enviados_tienen_sus_pdfs_y_al_observado_le_falta_uno(session):
    cargar_datos(session)
    session.commit()

    for legajo in session.exec(select(LegajoORM)).all():
        documentos = session.exec(
            select(DocumentoORM).where(DocumentoORM.legajo_id == legajo.id)
        ).all()
        tipos = {TipoDocumento(d.tipo) for d in documentos}
        requeridos = set(documentos_requeridos(legajo.solicita_beca, tiene_titulo_posgrado=False))
        if legajo.estado == EstadoLegajo.BORRADOR:
            assert tipos == set()
        elif legajo.estado == EstadoLegajo.OBSERVADO:
            assert tipos == requeridos - {TipoDocumento.TITULO_GRADO}
        else:
            assert tipos == requeridos

        for documento in documentos:
            contenido = ruta_del_pdf(documento.path_storage).read_bytes()
            validar_pdf(contenido)  # el mismo control que una subida de verdad
            assert len(contenido) == documento.tamanio_bytes
            assert hashlib.sha256(contenido).hexdigest() == documento.checksum_sha256
            assert documento.fecha_subida < legajo.fecha_inscripcion


def test_el_pdf_de_prueba_tiene_la_tabla_xref_bien_armada():
    pdf = seed._pdf_de_prueba("Copia del título de grado")

    assert pdf.startswith(b"%PDF-1.4") and pdf.endswith(b"%%EOF\n")
    assert "Documento de prueba · Copia del título de grado".encode("cp1252") in pdf
    # Cada posición de la tabla xref apunta al comienzo de su objeto.
    inicio_xref = int(pdf.rsplit(b"startxref\n", 1)[1].split(b"\n")[0])
    filas = pdf[inicio_xref:].split(b"\n")[3:8]
    for numero, fila in enumerate(filas, start=1):
        assert pdf[int(fila[:10]) :].startswith(b"%d 0 obj" % numero)


def test_una_base_con_el_seed_viejo_recibe_los_pdfs_sin_duplicar_legajos(session):
    cargar_datos(session)
    session.commit()
    # Así quedaba una base cargada antes de que el seed subiera documentos.
    for documento in session.exec(select(DocumentoORM)).all():
        session.delete(documento)
    session.commit()

    resumen = cargar_datos(session)
    session.commit()

    assert resumen["nuevos"] == DOCUMENTOS_DEL_SEED
    assert _contar_filas(session)["legajos"] == 11


@pytest.mark.parametrize(
    ("estado", "camino", "error"),
    [
        # Aprobar sin revisar: la máquina de estados no lo permite (PENDIENTE → COMPLETADO).
        (EstadoLegajo.COMPLETADO, [seed.ENVIAR, seed.APROBAR], TransicionInvalida),
        # Observar sin comentario: la máquina pide 5 caracteres o más.
        (
            EstadoLegajo.OBSERVADO,
            [seed.ENVIAR, seed.REVISAR, replace(seed.OBSERVAR, comentario=None)],
            ErrorDeValidacion,
        ),
    ],
)
def test_un_camino_que_la_maquina_de_estados_no_permite_frena_el_seed(
    session, monkeypatch, estado, camino, error
):
    monkeypatch.setitem(seed.CAMINOS, estado, camino)

    with pytest.raises(error):
        cargar_datos(session)
