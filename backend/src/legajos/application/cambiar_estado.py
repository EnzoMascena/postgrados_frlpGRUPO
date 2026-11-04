"""Caso de uso: cambiar el estado de un legajo (US-CORE-005, plan §9).

`ServicioEstados.cambiar` es el único lugar del sistema que cambia `legajos.estado`. Lo usan el
coordinador (`PATCH /legajos/{id}/estado`), el aspirante al enviar o corregir (Fran) y la tarea
diaria de vencimiento (Enzo, con `Actor(Rol.SISTEMA)`). Así, cualquier cambio pasa por la misma
validación, deja su fila de auditoría y manda su email.
"""

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from src.legajos.application.puertos import NotificadorLegajos
from src.legajos.domain.entidades import Legajo, RegistroAuditoria
from src.legajos.domain.estados import Accion, validar_comentario, validar_transicion
from src.legajos.domain.numero_legajo import generar_numero_legajo
from src.legajos.domain.repo import LegajoRepository
from src.shared.errors import NoEncontrado
from src.shared.roles import Actor

logger = logging.getLogger(__name__)

MENSAJE_LEGAJO_NO_ENCONTRADO = "No encontramos el legajo"

Reloj = Callable[[], datetime]


def _ahora_utc() -> datetime:
    return datetime.now(UTC)


class ServicioEstados:
    def __init__(
        self,
        repo: LegajoRepository,
        notificador: NotificadorLegajos,
        reloj: Reloj | None = None,
    ) -> None:
        self.repo = repo
        self.notificador = notificador
        # En los tests se pasa un reloj fijo para poder comparar las fechas exactas.
        self.reloj = reloj or _ahora_utc

    def cambiar(
        self, legajo_id: UUID, accion: Accion, actor: Actor, comentario: str | None = None
    ) -> Legajo:
        """Aplica `accion` al legajo, la audita, la guarda y recién después avisa.

        Errores, en este orden: 404 si el legajo no existe, 403 si el rol no puede hacer la
        acción, 409 si el estado no lo permite y 422 si OBSERVAR viene sin comentario. En todos
        los casos no se guarda ni se avisa nada.
        """
        legajo = self.repo.obtener(legajo_id)
        if legajo is None:
            raise NoEncontrado(MENSAJE_LEGAJO_NO_ENCONTRADO)

        estado_nuevo = validar_transicion(legajo.estado, accion, actor.rol)
        validar_comentario(accion, comentario)
        comentario = (comentario or "").strip() or None

        ahora = self.reloj()
        estado_anterior = legajo.estado
        self._aplicar_efectos(legajo, accion, ahora)
        legajo.estado = estado_nuevo

        registro = RegistroAuditoria(
            legajo_id=legajo.id,
            accion=accion,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            comentario=comentario,
            rol=actor.rol,
            usuario_email=actor.email,
            fecha=ahora,
        )
        self.repo.guardar_cambio(legajo, registro)

        # El aviso va después del commit: si el email falla, el cambio ya quedó guardado.
        self._notificar(legajo, accion, comentario)
        return legajo

    def _aplicar_efectos(self, legajo: Legajo, accion: Accion, ahora: datetime) -> None:
        """Los efectos de la tabla del plan §9. Las demás acciones solo cambian el estado."""
        if accion == Accion.ENVIAR:
            legajo.fecha_inscripcion = ahora
        elif accion == Accion.APROBAR:
            # `siguiente_secuencial` bloquea la cohorte hasta el commit de `guardar_cambio`.
            secuencial = self.repo.siguiente_secuencial(legajo.cohorte_id)
            cohorte = self.repo.datos_cohorte(legajo.cohorte_id)
            legajo.numero_legajo = generar_numero_legajo(cohorte.anio, cohorte.numero, secuencial)
            legajo.fecha_aprobacion = ahora
        elif accion == Accion.MATRICULAR:
            legajo.fecha_activacion = ahora

    def _notificar(self, legajo: Legajo, accion: Accion, comentario: str | None) -> None:
        # `enviar_email` ya no levanta si falla el SMTP, pero un error al armar el email (una
        # plantilla rota) tampoco tiene que convertir en 500 un cambio que ya se guardó: el
        # cliente reintentaría y recibiría un 409 confuso. Queda en el log para arreglarlo.
        try:
            self.notificador.notificar(legajo, accion, comentario)
        except Exception:
            logger.exception("No se pudo avisar %s del legajo %s", accion, legajo.id)
