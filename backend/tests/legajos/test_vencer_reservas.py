"""`vencer_reservas` con un `ServicioEstados` falso: qué legajos vence, con qué acción y quién."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from src.legajos.application.vencer_reservas import ReservaAprobada, vencer_reservas
from src.legajos.domain.entidades import Legajo
from src.legajos.domain.estados import Accion, EstadoLegajo, TransicionInvalida
from src.shared.errors import NoEncontrado
from src.shared.roles import Actor, Rol

AHORA = datetime(2026, 11, 6, 6, 0, tzinfo=UTC)  # las 3:00 en Argentina


class ServicioFalso:
    """Anota cada cambio y devuelve el legajo ya VENCIDO. `errores` dice qué legajo falla y cómo."""

    def __init__(self, errores: dict[UUID, Exception] | None = None) -> None:
        self.cambios: list[tuple[UUID, Accion, Actor]] = []
        self.errores = errores or {}

    def cambiar(
        self, legajo_id: UUID, accion: Accion, actor: Actor, comentario: str | None = None
    ) -> Legajo:
        self.cambios.append((legajo_id, accion, actor))
        if legajo_id in self.errores:
            raise self.errores[legajo_id]
        return Legajo(
            id=legajo_id,
            cohorte_id=uuid4(),
            estado=EstadoLegajo.VENCIDO,
            numero_legajo="26-001-001",
            codigo_seguimiento="7F3A9C21",
            nombre="Ana Laura",
            apellido="Rodríguez",
            email="ana.rodriguez@example.com",
        )


def aprobada_hace(tiempo: timedelta) -> ReservaAprobada:
    return ReservaAprobada(uuid4(), AHORA - tiempo)


@pytest.mark.parametrize(
    ("tiempo", "vence"),
    [
        (timedelta(days=30), True),  # justo 30 días: la regla es "30 o más" (BR-005)
        (timedelta(days=45), True),
        (timedelta(days=30) - timedelta(minutes=1), False),
        (timedelta(days=1), False),
    ],
)
def test_vence_solo_las_reservas_con_30_dias_o_mas(tiempo, vence):
    servicio = ServicioFalso()
    reserva = aprobada_hace(tiempo)

    resultado = vencer_reservas([reserva], servicio, AHORA)

    assert [legajo_id for legajo_id, _, _ in servicio.cambios] == (
        [reserva.legajo_id] if vence else []
    )
    assert len(resultado.vencidos) == (1 if vence else 0)


def test_vence_con_la_accion_vencer_y_el_sistema_como_actor():
    servicio = ServicioFalso()
    reserva = aprobada_hace(timedelta(days=31))

    vencer_reservas([reserva], servicio, AHORA)

    # Sin email: en la auditoría queda que lo hizo el sistema, no un usuario.
    assert servicio.cambios == [(reserva.legajo_id, Accion.VENCER, Actor(Rol.SISTEMA))]


def test_el_resultado_cuenta_las_revisadas_y_trae_las_vencidas():
    servicio = ServicioFalso()
    vieja, nueva = aprobada_hace(timedelta(days=40)), aprobada_hace(timedelta(days=3))

    resultado = vencer_reservas([vieja, nueva], servicio, AHORA)

    assert resultado.revisadas == 2
    assert [legajo.id for legajo in resultado.vencidos] == [vieja.legajo_id]


@pytest.mark.parametrize(
    "error",
    [
        # Lo matricularon entre la consulta y el cambio: ya no hay nada que vencer.
        TransicionInvalida("No se puede VENCER un legajo en estado ACTIVO"),
        # No debería pasar (los legajos no se borran), pero tampoco corta la corrida.
        NoEncontrado("No encontramos el legajo"),
    ],
)
def test_si_un_legajo_cambio_en_el_medio_lo_saltea_y_sigue_con_los_demas(error, caplog):
    primera, segunda = aprobada_hace(timedelta(days=35)), aprobada_hace(timedelta(days=32))
    servicio = ServicioFalso(errores={primera.legajo_id: error})

    resultado = vencer_reservas([primera, segunda], servicio, AHORA)

    assert [legajo.id for legajo in resultado.vencidos] == [segunda.legajo_id]
    assert f"No se venció el legajo {primera.legajo_id}" in caplog.text


def test_un_error_inesperado_corta_la_corrida():
    primera, segunda = aprobada_hace(timedelta(days=35)), aprobada_hace(timedelta(days=32))
    servicio = ServicioFalso(errores={primera.legajo_id: RuntimeError("se cayó la base")})

    with pytest.raises(RuntimeError):
        vencer_reservas([primera, segunda], servicio, AHORA)

    assert [legajo_id for legajo_id, _, _ in servicio.cambios] == [primera.legajo_id]


def test_sin_reservas_no_hace_nada():
    servicio = ServicioFalso()

    resultado = vencer_reservas([], servicio, AHORA)

    assert (resultado.revisadas, resultado.vencidos, servicio.cambios) == (0, [], [])
