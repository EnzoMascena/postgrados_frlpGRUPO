"""`obtener_resumen` con un repositorio falso: sin base."""

from uuid import UUID, uuid4

from src.inscripcion.domain.tipos import TipoBeca
from src.legajos.application.resumen import obtener_resumen
from src.legajos.domain.estados import EstadoLegajo


class RepoEnMemoria:
    def __init__(
        self,
        por_estado: dict[EstadoLegajo, int] | None = None,
        por_beca: dict[TipoBeca, int] | None = None,
    ) -> None:
        self.por_estado = por_estado or {}
        self.por_beca = por_beca or {}
        self.cohortes_pedidas: list[UUID | None] = []

    def contar_por_estado(self, cohorte_id: UUID | None) -> dict[EstadoLegajo, int]:
        self.cohortes_pedidas.append(cohorte_id)
        return self.por_estado

    def contar_por_beca(self, cohorte_id: UUID | None) -> dict[TipoBeca, int]:
        self.cohortes_pedidas.append(cohorte_id)
        return self.por_beca


def test_sin_legajos_trae_los_10_estados_en_cero():
    resumen = obtener_resumen(None, RepoEnMemoria())

    assert resumen.por_estado == dict.fromkeys(EstadoLegajo, 0)
    assert len(resumen.por_estado) == 10
    assert (resumen.total, resumen.con_beca, resumen.beca30, resumen.beca100) == (0, 0, 0, 0)


def test_el_ejemplo_del_plan():
    repo = RepoEnMemoria(
        por_estado={
            EstadoLegajo.BORRADOR: 1,
            EstadoLegajo.PENDIENTE: 3,
            EstadoLegajo.EN_REVISION: 2,
            EstadoLegajo.OBSERVADO: 1,
            EstadoLegajo.COMPLETADO: 2,
            EstadoLegajo.ACTIVO: 4,
        },
        por_beca={TipoBeca.TREINTA: 2, TipoBeca.CIEN: 2},
    )

    resumen = obtener_resumen(None, repo)

    assert resumen.total == 13
    assert resumen.por_estado[EstadoLegajo.ACTIVO] == 4
    assert resumen.por_estado[EstadoLegajo.VENCIDO] == 0
    assert resumen.por_estado[EstadoLegajo.GRADUADO] == 0
    assert (resumen.con_beca, resumen.beca30, resumen.beca100) == (4, 2, 2)


def test_los_estados_salen_en_el_orden_del_enum():
    # El front arma las tarjetas recorriendo `porEstado`: el orden tiene que ser siempre el mismo.
    resumen = obtener_resumen(None, RepoEnMemoria({EstadoLegajo.GRADUADO: 1}))

    assert list(resumen.por_estado) == list(EstadoLegajo)


def test_con_un_solo_tipo_de_beca():
    resumen = obtener_resumen(None, RepoEnMemoria(por_beca={TipoBeca.CIEN: 3}))

    assert (resumen.con_beca, resumen.beca30, resumen.beca100) == (3, 0, 3)


def test_pasa_la_cohorte_a_las_dos_consultas():
    cohorte_id = uuid4()
    repo = RepoEnMemoria()

    obtener_resumen(cohorte_id, repo)

    assert repo.cohortes_pedidas == [cohorte_id, cohorte_id]
