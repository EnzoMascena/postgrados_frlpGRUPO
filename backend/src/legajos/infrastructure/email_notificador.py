"""`NotificadorLegajos` con emails: qué plantilla manda cada acción y con qué datos (plan §11).

Usa `enviar_email` de Enzo y las plantillas de Gero. Los nombres de plantilla y de variables son
los del plan: si cambian, se avisa antes en el grupo. Las acciones que no tienen email (REVISAR,
MATRICULAR, DAR_DE_BAJA y GRADUAR) no mandan nada.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from src.autenticacion.infrastructure.pg_repository import PgUsuarioRepository
from src.legajos.domain.entidades import Legajo
from src.legajos.domain.estados import Accion
from src.legajos.domain.repo import LegajoRepository
from src.legajos.domain.vencimiento import fecha_limite
from src.shared.config import settings
from src.shared.email.sender import enviar_email
from src.shared.roles import Rol

ASUNTO_CONFIRMACION = "Recibimos tu preinscripción"
ASUNTO_OBSERVACION = "Tu legajo tiene observaciones"
ASUNTO_APROBACION = "Tu legajo fue aprobado"
ASUNTO_RECHAZO = "Resultado de tu preinscripción"
ASUNTO_VENCIMIENTO = "Venció una reserva de vacante"


def fecha_para_email(fecha: datetime) -> str:
    """`dd/mm/aaaa` en la hora de Argentina: en la base está en UTC, y a las 23:00 de acá allá
    ya es el día siguiente."""
    return fecha.astimezone(ZoneInfo(settings.zona_horaria)).strftime("%d/%m/%Y")


class EmailNotificadorLegajos:
    def __init__(self, repo: LegajoRepository, usuarios: PgUsuarioRepository) -> None:
        self.repo = repo
        self.usuarios = usuarios

    def notificar(self, legajo: Legajo, accion: Accion, comentario: str | None) -> None:
        if accion in (Accion.ENVIAR, Accion.CORREGIR):
            self._confirmacion_envio(legajo, es_correccion=accion == Accion.CORREGIR)
        elif accion == Accion.OBSERVAR:
            self._al_aspirante(
                legajo,
                ASUNTO_OBSERVACION,
                "observacion.html",
                comentario=comentario,
                # El token del link de seguimiento se guarda hasheado: no se puede volver a armar
                # el link, así que se manda a recuperar el acceso (plan §11).
                link_recuperar=f"{settings.frontend_url.rstrip('/')}/inscripcion?recuperar=1",
            )
        elif accion == Accion.APROBAR:
            self._al_aspirante(
                legajo,
                ASUNTO_APROBACION,
                "aprobacion.html",
                numero_legajo=legajo.numero_legajo,
                carreras=self.repo.nombres_carreras(legajo.id),
                fecha_limite=fecha_para_email(fecha_limite(_fecha(legajo.fecha_aprobacion))),
            )
        elif accion == Accion.RECHAZAR:
            # La plantilla muestra el recuadro del comentario solo si viene con texto.
            self._al_aspirante(legajo, ASUNTO_RECHAZO, "rechazo.html", comentario=comentario or "")
        elif accion == Accion.VENCER:
            self._vencimiento_a_coordinadores(legajo)

    def _al_aspirante(self, legajo: Legajo, asunto: str, plantilla: str, **contexto) -> None:
        enviar_email(legajo.email, asunto, plantilla, {"nombre": legajo.nombre, **contexto})

    def _confirmacion_envio(self, legajo: Legajo, es_correccion: bool) -> None:
        self._al_aspirante(
            legajo,
            ASUNTO_CONFIRMACION,
            "confirmacion_envio.html",
            codigo_seguimiento=legajo.codigo_seguimiento,
            carreras=self.repo.nombres_carreras(legajo.id),
            cohorte=self.repo.datos_cohorte(legajo.cohorte_id).nombre,
            es_correccion=es_correccion,
        )

    def _vencimiento_a_coordinadores(self, legajo: Legajo) -> None:
        contexto = {
            "apellido": legajo.apellido,
            "nombre": legajo.nombre,
            "numero_legajo": legajo.numero_legajo,
            "fecha_aprobacion": fecha_para_email(_fecha(legajo.fecha_aprobacion)),
        }
        for coordinador in self.usuarios.activos_con_rol(Rol.COORDINADOR):
            enviar_email(
                coordinador.email, ASUNTO_VENCIMIENTO, "vencimiento_coordinador.html", contexto
            )


def _fecha(fecha: datetime | None) -> datetime:
    # APROBAR y VENCER siempre llegan con `fecha_aprobacion`: la pone el servicio al aprobar.
    if fecha is None:
        raise ValueError("El legajo no tiene fecha de aprobación")
    return fecha
