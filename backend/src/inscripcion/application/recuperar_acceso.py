"""Caso de uso: el aspirante perdió el link y pide uno nuevo con su email (US-CORE-001)."""

from src.inscripcion.application.inscribir import CrearLink, EnviarLink
from src.inscripcion.domain.repo import InscripcionRepository

# La misma respuesta exista o no el email: así no se puede averiguar quién se inscribió.
MENSAJE_RECUPERAR_ACCESO = (
    "Si hay una preinscripción con ese email, te enviamos un link para continuar."
)


def recuperar_acceso(
    email: str, repo: InscripcionRepository, crear_link: CrearLink, enviar_link: EnviarLink
) -> None:
    legajo = repo.buscar_ultimo_por_email(email)
    if legajo is None:
        return
    token = crear_link(legajo.id)
    enviar_link(legajo.email, legajo.nombre, legajo.codigo_seguimiento, token)
