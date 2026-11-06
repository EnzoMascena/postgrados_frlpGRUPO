"""`buscar_legajos` con un repositorio falso: sin base.

El filtrado de verdad (SQL) se prueba en `test_pg_repository.py`; acá, que el caso de uso
interprete bien `q`, pagine y cuente los documentos con las reglas de Fran.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.gestion_documental.domain.tipos import TipoDocumento
from src.inscripcion.domain.tipos import TipoBeca
from src.legajos.application.buscar_legajos import (
    MENSAJE_APELLIDO_CORTO,
    CriteriosBusqueda,
    FilaBusqueda,
    FiltrosBusqueda,
    buscar_legajos,
    criterios_desde,
)
from src.legajos.domain.estados import EstadoLegajo
from src.shared.errors import ErrorDeValidacion

OBLIGATORIOS = frozenset(
    {
        TipoDocumento.FORM_INSCRIPCION,
        TipoDocumento.DNI,
        TipoDocumento.TITULO_GRADO,
        TipoDocumento.PARTIDA,
        TipoDocumento.CUIT_CUIL,
    }
)


class RepoEnMemoria:
    """Guarda con qué lo llamaron y devuelve las filas que le dieron, paginadas."""

    def __init__(self, filas: list[FilaBusqueda] | None = None) -> None:
        self.filas = filas or []
        self.criterios: CriteriosBusqueda | None = None
        self.offset: int | None = None
        self.limite: int | None = None

    def buscar(self, criterios: CriteriosBusqueda, offset: int, limite: int) -> list[FilaBusqueda]:
        self.criterios, self.offset, self.limite = criterios, offset, limite
        return self.filas[offset : offset + limite]

    def contar(self, criterios: CriteriosBusqueda) -> int:
        return len(self.filas)


def nueva_fila(**campos) -> FilaBusqueda:
    datos = {
        "id": uuid4(),
        "codigo_seguimiento": "7F3A9C21",
        "numero_legajo": None,
        "apellido": "Rodríguez",
        "nombre": "Ana Laura",
        "dni": "28456789",
        "email": "ana@example.com",
        "estado": EstadoLegajo.PENDIENTE,
        "cohorte": "Cohorte 2026",
        "carreras": ["Maestría en Tecnología Informática"],
        "solicita_beca": False,
        "tipo_beca": None,
        "titulo_posgrado": None,
        "tipos_cargados": frozenset(),
        "fecha_inscripcion": datetime(2026, 11, 3, 14, 20, tzinfo=UTC),
    }
    datos.update(campos)
    return FilaBusqueda(**datos)


# --- Qué significa `q` ---


@pytest.mark.parametrize("q", ["28456789", "  28456789  ", "1"])
def test_q_con_solo_digitos_busca_dni_exacto(q):
    criterios = criterios_desde(FiltrosBusqueda(q=q))

    assert criterios.dni == q.strip()
    assert criterios.apellido is None


@pytest.mark.parametrize("q", ["rod", "RODRÍGUEZ", "  Pérez ", "de la"])
def test_q_con_letras_busca_por_apellido(q):
    criterios = criterios_desde(FiltrosBusqueda(q=q))

    assert criterios.apellido == q.strip()
    assert criterios.dni is None


@pytest.mark.parametrize("q", ["ro", "a", " ab ", "1a"])
def test_apellido_con_menos_de_3_letras_es_422(q):
    with pytest.raises(ErrorDeValidacion) as error:
        criterios_desde(FiltrosBusqueda(q=q))

    assert error.value.mensaje == MENSAJE_APELLIDO_CORTO
    assert error.value.campo == "q"


@pytest.mark.parametrize("q", [None, "", "   "])
def test_q_vacio_no_filtra(q):
    criterios = criterios_desde(FiltrosBusqueda(q=q))

    assert criterios.dni is None
    assert criterios.apellido is None


def test_los_demas_filtros_pasan_tal_cual_al_repositorio():
    cohorte_id, carrera_id = uuid4(), uuid4()
    repo = RepoEnMemoria()

    buscar_legajos(
        FiltrosBusqueda(
            q="gonz",
            estado=EstadoLegajo.EN_REVISION,
            cohorte_id=cohorte_id,
            carrera_id=carrera_id,
            beca=True,
        ),
        repo,
    )

    assert repo.criterios == CriteriosBusqueda(
        apellido="gonz",
        estado=EstadoLegajo.EN_REVISION,
        cohorte_id=cohorte_id,
        carrera_id=carrera_id,
        beca=True,
    )


def test_si_q_es_invalido_no_consulta_al_repositorio():
    repo = RepoEnMemoria()

    with pytest.raises(ErrorDeValidacion):
        buscar_legajos(FiltrosBusqueda(q="ro"), repo)

    assert repo.criterios is None


# --- Paginación ---


@pytest.mark.parametrize(("page", "size", "offset"), [(1, 20, 0), (2, 20, 20), (3, 5, 10)])
def test_la_pagina_se_traduce_a_offset_y_limite(page, size, offset):
    repo = RepoEnMemoria()

    buscar_legajos(FiltrosBusqueda(page=page, size=size), repo)

    assert (repo.offset, repo.limite) == (offset, size)


def test_la_pagina_trae_el_total_sin_paginar():
    repo = RepoEnMemoria([nueva_fila() for _ in range(7)])

    pagina = buscar_legajos(FiltrosBusqueda(page=2, size=5), repo)

    assert len(pagina.items) == 2
    assert (pagina.total, pagina.page, pagina.size) == (7, 2, 5)


def test_sin_resultados_es_una_pagina_vacia():
    pagina = buscar_legajos(FiltrosBusqueda(q="zzz"), RepoEnMemoria())

    assert pagina.items == []
    assert pagina.total == 0


# --- Cada fila ---


def test_la_fila_trae_los_datos_del_legajo():
    fila = nueva_fila(
        numero_legajo="26-001-003",
        estado=EstadoLegajo.COMPLETADO,
        solicita_beca=True,
        tipo_beca=TipoBeca.TREINTA,
    )

    item = buscar_legajos(FiltrosBusqueda(), RepoEnMemoria([fila])).items[0]

    assert item.id == fila.id
    assert item.numero_legajo == "26-001-003"
    assert item.estado == EstadoLegajo.COMPLETADO
    assert item.cohorte == "Cohorte 2026"
    assert item.carreras == ["Maestría en Tecnología Informática"]
    assert item.tipo_beca == TipoBeca.TREINTA
    assert item.fecha_inscripcion == fila.fecha_inscripcion


@pytest.mark.parametrize(
    ("campos", "cargados", "esperado"),
    [
        # Sin beca ni título de posgrado: los 5 obligatorios.
        ({}, frozenset(), (0, 5)),
        ({}, OBLIGATORIOS, (5, 5)),
        # Con beca suma el formulario de beca; con título de posgrado, su copia.
        ({"solicita_beca": True, "tipo_beca": TipoBeca.CIEN}, OBLIGATORIOS, (5, 6)),
        ({"titulo_posgrado": "Especialista en Redes"}, OBLIGATORIOS, (5, 6)),
        (
            {"solicita_beca": True, "tipo_beca": TipoBeca.TREINTA, "titulo_posgrado": "Esp."},
            OBLIGATORIOS | {TipoDocumento.FORM_BECA, TipoDocumento.TITULO_POSGRADO},
            (7, 7),
        ),
        # Subió el formulario de beca y después sacó la beca: no cuenta, nunca "6 de 5".
        ({}, OBLIGATORIOS | {TipoDocumento.FORM_BECA}, (5, 5)),
        ({}, frozenset({TipoDocumento.DNI, TipoDocumento.PARTIDA}), (2, 5)),
    ],
)
def test_cuenta_documentos_cargados_y_requeridos(campos, cargados, esperado):
    fila = nueva_fila(tipos_cargados=cargados, **campos)

    item = buscar_legajos(FiltrosBusqueda(), RepoEnMemoria([fila])).items[0]

    assert (item.documentos_cargados, item.documentos_requeridos) == esperado
