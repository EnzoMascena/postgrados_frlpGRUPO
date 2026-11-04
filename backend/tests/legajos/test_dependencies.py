"""`get_servicio_estados` arma el servicio con las piezas de verdad, sobre la sesión del request."""

from src.legajos.application.cambiar_estado import ServicioEstados
from src.legajos.infrastructure.email_notificador import EmailNotificadorLegajos
from src.legajos.infrastructure.pg_repository import PgLegajoRepository
from src.legajos.presentation.dependencies import get_servicio_estados


def test_get_servicio_estados_usa_la_base_y_los_emails_con_la_misma_sesion(session):
    servicio = get_servicio_estados(session)

    assert isinstance(servicio, ServicioEstados)
    assert isinstance(servicio.repo, PgLegajoRepository)
    assert isinstance(servicio.notificador, EmailNotificadorLegajos)
    # Todo sobre la misma sesión: el cambio y lo que lee el email ven los mismos datos.
    assert servicio.repo.session is session
    assert servicio.notificador.repo is servicio.repo
    assert servicio.notificador.usuarios.session is session
