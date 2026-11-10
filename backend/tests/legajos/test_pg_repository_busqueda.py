"""La búsqueda y el resumen de `PgLegajoRepository` contra la base de test (rollback por test).

Van aparte de `test_pg_repository.py` (estados y detalle) para que cada archivo se lea solo.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.gestion_documental.domain.tipos import TipoDocumento
from src.gestion_documental.infrastructure.orm_models import DocumentoORM
from src.inscripcion.domain.tipos import TipoBeca
from src.legajos.application.buscar_legajos import CriteriosBusqueda
from src.legajos.domain.estados import EstadoLegajo
from src.legajos.infrastructure.pg_repository import PgLegajoRepository
from tests.fabricas import crear_carrera, crear_cohorte, crear_legajo

AHORA = datetime(2026, 11, 4, 12, 0, tzinfo=UTC)
TODOS = CriteriosBusqueda()


@pytest.fixture
def repo(session) -> PgLegajoRepository:
    return PgLegajoRepository(session)


@pytest.fixture
def cohorte(session):
    return crear_cohorte(session, anio=2026, numero=1, nombre="Cohorte 2026")


@pytest.fixture
def carrera(session):
    return crear_carrera(session, nombre="Maestría en Tecnología Informática")


def _legajo(session, cohorte, carreras, minutos: int = 0, **campos):
    """Un legajo creado hace `minutos` minutos: así el orden de los tests no depende del reloj."""
    return crear_legajo(
        session, cohorte, carreras, created_at=AHORA - timedelta(minutes=minutos), **campos
    )


def _subir_documento(session, legajo, tipo: TipoDocumento) -> None:
    session.add(
        DocumentoORM(
            legajo_id=legajo.id,
            tipo=tipo.value,
            path_storage=f"uploads/{legajo.cohorte_id}/{legajo.id}/{uuid4()}.pdf",
            nombre_original=f"{tipo.value.lower()}.pdf",
            checksum_sha256="0" * 64,
            tamanio_bytes=183_412,
        )
    )
    session.commit()


def _ids(filas) -> list:
    return [fila.id for fila in filas]


# --- buscar: la fila ---


def test_buscar_trae_la_fila_con_cohorte_carreras_y_documentos(repo, session, cohorte, carrera):
    otra = crear_carrera(session, nombre="Especialización en Ingeniería Gerencial")
    legajo = _legajo(
        session,
        cohorte,
        [carrera, otra],
        apellido="Rodríguez",
        nombre="Ana Laura",
        dni="28456789",
        estado=EstadoLegajo.PENDIENTE,
        solicita_beca=True,
        tipo_beca=TipoBeca.TREINTA.value,
        titulo_posgrado="Especialista en Redes",
        fecha_inscripcion=AHORA,
    )
    _subir_documento(session, legajo, TipoDocumento.DNI)
    _subir_documento(session, legajo, TipoDocumento.FORM_BECA)

    [fila] = repo.buscar(TODOS, 0, 20)

    assert fila.id == legajo.id
    assert fila.codigo_seguimiento == legajo.codigo_seguimiento
    assert (fila.apellido, fila.nombre, fila.dni) == ("Rodríguez", "Ana Laura", "28456789")
    assert fila.estado == EstadoLegajo.PENDIENTE
    assert fila.cohorte == "Cohorte 2026"
    assert fila.carreras == [
        "Maestría en Tecnología Informática",
        "Especialización en Ingeniería Gerencial",
    ]
    assert (fila.solicita_beca, fila.tipo_beca) == (True, TipoBeca.TREINTA)
    assert fila.titulo_posgrado == "Especialista en Redes"
    assert fila.tipos_cargados == {TipoDocumento.DNI, TipoDocumento.FORM_BECA}
    assert fila.fecha_inscripcion == AHORA


def test_buscar_sin_documentos_trae_el_conjunto_vacio(repo, session, cohorte, carrera):
    _legajo(session, cohorte, [carrera])

    [fila] = repo.buscar(TODOS, 0, 20)

    assert fila.tipos_cargados == frozenset()
    assert fila.tipo_beca is None


def test_buscar_sin_resultados_es_lista_vacia(repo):
    assert repo.buscar(TODOS, 0, 20) == []
    assert repo.contar(TODOS) == 0


# --- buscar: orden y páginas ---


def test_buscar_trae_los_mas_nuevos_primero(repo, session, cohorte, carrera):
    viejo = _legajo(session, cohorte, [carrera], minutos=30)
    nuevo = _legajo(session, cohorte, [carrera], minutos=1)
    medio = _legajo(session, cohorte, [carrera], minutos=10)

    assert _ids(repo.buscar(TODOS, 0, 20)) == [nuevo.id, medio.id, viejo.id]


def test_buscar_pagina_con_offset_y_limite(repo, session, cohorte, carrera):
    legajos = [_legajo(session, cohorte, [carrera], minutos=m) for m in range(5)]

    assert _ids(repo.buscar(TODOS, 0, 2)) == [legajos[0].id, legajos[1].id]
    assert _ids(repo.buscar(TODOS, 2, 2)) == [legajos[2].id, legajos[3].id]
    assert _ids(repo.buscar(TODOS, 4, 2)) == [legajos[4].id]
    assert repo.buscar(TODOS, 6, 2) == []
    assert repo.contar(TODOS) == 5


def test_con_la_misma_fecha_las_paginas_no_se_pisan(repo, session, cohorte, carrera):
    # Sin desempate por id, Postgres puede devolver el mismo legajo en dos páginas.
    legajos = [_legajo(session, cohorte, [carrera]) for _ in range(4)]

    paginas = _ids(repo.buscar(TODOS, 0, 2)) + _ids(repo.buscar(TODOS, 2, 2))

    assert sorted(paginas) == sorted(legajo.id for legajo in legajos)


# --- buscar y contar: cada filtro ---


def test_filtro_por_dni_exacto(repo, session, cohorte, carrera):
    buscado = _legajo(session, cohorte, [carrera], dni="28456789")
    _legajo(session, cohorte, [carrera], dni="284567890")
    _legajo(session, cohorte, [carrera], dni="128456789")
    criterios = CriteriosBusqueda(dni="28456789")

    assert _ids(repo.buscar(criterios, 0, 20)) == [buscado.id]
    assert repo.contar(criterios) == 1


@pytest.mark.parametrize("texto", ["rod", "RODR", "ríguez", "Rodríguez", "DRÍG"])
def test_filtro_por_apellido_parcial_sin_distinguir_mayusculas(
    repo, session, cohorte, carrera, texto
):
    buscado = _legajo(session, cohorte, [carrera], apellido="Rodríguez")
    _legajo(session, cohorte, [carrera], apellido="González")

    assert _ids(repo.buscar(CriteriosBusqueda(apellido=texto), 0, 20)) == [buscado.id]


@pytest.mark.parametrize(
    ("apellido", "texto"),
    [
        ("García", "garcia"),
        ("García", "GARCIA"),
        ("García", "GARCÍA"),
        ("García", "arci"),
        ("Garcia", "garcía"),
        ("Muñoz", "munoz"),
        ("Muñoz", "MUÑOZ"),
        ("Güemes", "guemes"),
    ],
)
def test_filtro_por_apellido_sin_distinguir_tildes(
    repo, session, cohorte, carrera, apellido, texto
):
    buscado = _legajo(session, cohorte, [carrera], apellido=apellido)
    _legajo(session, cohorte, [carrera], apellido="Romero")
    criterios = CriteriosBusqueda(apellido=texto)

    assert _ids(repo.buscar(criterios, 0, 20)) == [buscado.id]
    assert repo.contar(criterios) == 1


@pytest.mark.parametrize("texto", ["%%%", "___", "%_%", "\\\\\\"])
def test_los_comodines_del_usuario_se_buscan_literales(repo, session, cohorte, carrera, texto):
    _legajo(session, cohorte, [carrera], apellido="Rodríguez")
    _legajo(session, cohorte, [carrera], apellido="González")
    criterios = CriteriosBusqueda(apellido=texto)

    assert repo.buscar(criterios, 0, 20) == []
    assert repo.contar(criterios) == 0


def test_un_apellido_con_guion_bajo_se_encuentra_tal_cual(repo, session, cohorte, carrera):
    buscado = _legajo(session, cohorte, [carrera], apellido="Pérez_Gómez")
    _legajo(session, cohorte, [carrera], apellido="PérezXGómez")

    assert _ids(repo.buscar(CriteriosBusqueda(apellido="z_g"), 0, 20)) == [buscado.id]


def test_filtro_por_estado(repo, session, cohorte, carrera):
    buscado = _legajo(session, cohorte, [carrera], estado=EstadoLegajo.EN_REVISION)
    _legajo(session, cohorte, [carrera], estado=EstadoLegajo.PENDIENTE)
    criterios = CriteriosBusqueda(estado=EstadoLegajo.EN_REVISION)

    assert _ids(repo.buscar(criterios, 0, 20)) == [buscado.id]
    assert repo.contar(criterios) == 1


def test_filtro_por_cohorte(repo, session, cohorte, carrera):
    otra = crear_cohorte(session, anio=2025, numero=1, nombre="Cohorte 2025")
    buscado = _legajo(session, cohorte, [carrera])
    _legajo(session, otra, [carrera])
    criterios = CriteriosBusqueda(cohorte_id=cohorte.id)

    assert _ids(repo.buscar(criterios, 0, 20)) == [buscado.id]
    assert repo.contar(criterios) == 1


def test_filtro_por_carrera_en_primera_o_segunda_opcion(repo, session, cohorte, carrera):
    otra = crear_carrera(session, nombre="Doctorado en Ingeniería")
    primera = _legajo(session, cohorte, [carrera], minutos=2)
    segunda = _legajo(session, cohorte, [otra, carrera], minutos=1)
    _legajo(session, cohorte, [otra])
    criterios = CriteriosBusqueda(carrera_id=carrera.id)

    assert _ids(repo.buscar(criterios, 0, 20)) == [segunda.id, primera.id]
    assert repo.contar(criterios) == 2


def test_filtro_por_carrera_no_repite_el_legajo(repo, session, cohorte, carrera):
    otra = crear_carrera(session, nombre="Doctorado en Ingeniería")
    _legajo(session, cohorte, [carrera, otra])

    assert len(repo.buscar(CriteriosBusqueda(carrera_id=carrera.id), 0, 20)) == 1
    assert len(repo.buscar(TODOS, 0, 20)) == 1


@pytest.mark.parametrize("beca", [True, False])
def test_filtro_por_beca(repo, session, cohorte, carrera, beca):
    con_beca = _legajo(session, cohorte, [carrera], solicita_beca=True, tipo_beca="100")
    sin_beca = _legajo(session, cohorte, [carrera])
    criterios = CriteriosBusqueda(beca=beca)

    assert _ids(repo.buscar(criterios, 0, 20)) == [con_beca.id if beca else sin_beca.id]
    assert repo.contar(criterios) == 1


def test_filtros_combinados(repo, session, cohorte, carrera):
    otra_cohorte = crear_cohorte(session, anio=2025, numero=1, nombre="Cohorte 2025")
    datos = {"apellido": "González", "estado": EstadoLegajo.PENDIENTE}
    beca = {"solicita_beca": True, "tipo_beca": "30"}
    buscado = _legajo(session, cohorte, [carrera], **datos, **beca)
    # Cada uno falla en un solo filtro.
    _legajo(session, cohorte, [carrera], **datos)
    _legajo(session, cohorte, [carrera], **{**datos, "estado": EstadoLegajo.OBSERVADO}, **beca)
    _legajo(session, cohorte, [carrera], **{**datos, "apellido": "Pérez"}, **beca)
    _legajo(session, otra_cohorte, [carrera], **datos, **beca)
    criterios = CriteriosBusqueda(
        apellido="gonz", estado=EstadoLegajo.PENDIENTE, cohorte_id=cohorte.id, beca=True
    )

    assert _ids(repo.buscar(criterios, 0, 20)) == [buscado.id]
    assert repo.contar(criterios) == 1


# --- resumen ---


def test_contar_por_estado_trae_solo_los_que_tienen_legajos(repo, session, cohorte, carrera):
    for estado in [EstadoLegajo.PENDIENTE, EstadoLegajo.PENDIENTE, EstadoLegajo.ACTIVO]:
        _legajo(session, cohorte, [carrera], estado=estado)

    assert repo.contar_por_estado(None) == {EstadoLegajo.PENDIENTE: 2, EstadoLegajo.ACTIVO: 1}


def test_contar_por_beca_trae_cada_tipo(repo, session, cohorte, carrera):
    _legajo(session, cohorte, [carrera], solicita_beca=True, tipo_beca="30")
    _legajo(session, cohorte, [carrera], solicita_beca=True, tipo_beca="30")
    _legajo(session, cohorte, [carrera], solicita_beca=True, tipo_beca="100")
    _legajo(session, cohorte, [carrera])

    assert repo.contar_por_beca(None) == {TipoBeca.TREINTA: 2, TipoBeca.CIEN: 1}


def test_los_conteos_filtran_por_cohorte(repo, session, cohorte, carrera):
    otra = crear_cohorte(session, anio=2025, numero=1, nombre="Cohorte 2025")
    _legajo(session, cohorte, [carrera], estado=EstadoLegajo.PENDIENTE)
    _legajo(
        session, otra, [carrera], estado=EstadoLegajo.ACTIVO, solicita_beca=True, tipo_beca="30"
    )

    assert repo.contar_por_estado(cohorte.id) == {EstadoLegajo.PENDIENTE: 1}
    assert repo.contar_por_beca(cohorte.id) == {}
    assert repo.contar_por_estado(otra.id) == {EstadoLegajo.ACTIVO: 1}
    assert repo.contar_por_beca(otra.id) == {TipoBeca.TREINTA: 1}


def test_los_conteos_sin_legajos_son_vacios(repo):
    assert repo.contar_por_estado(None) == {}
    assert repo.contar_por_beca(None) == {}
