"""Lo que `ServicioEstados` necesita para avisar de un cambio, sin decir cómo.

La implementación con emails (`EmailNotificadorLegajos`) vive en `infrastructure/`; en los tests
unitarios se usa una falsa que anota cada aviso.
"""

from typing import Protocol

from src.legajos.domain.entidades import Legajo
from src.legajos.domain.estados import Accion


class NotificadorLegajos(Protocol):
    def notificar(self, legajo: Legajo, accion: Accion, comentario: str | None) -> None:
        """Avisa del cambio que ya quedó guardado. Decide a quién y si corresponde avisar."""
        ...
