"""Los datos de la inscripción del aspirante y sus mensajes (US-CORE-001). Python puro."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from src.inscripcion.domain.tipos import ComoConocio, TipoBeca

MENSAJE_DNI_REPETIDO = "Ya existe una preinscripción con este DNI para la cohorte actual"
MENSAJE_EMAIL_REPETIDO = (
    "Ya hay una preinscripción con este email. Si ya empezaste, pedí el link para continuar"
)


@dataclass(frozen=True)
class DatosInscripcion:
    """Lo que manda el formulario, ya validado y normalizado (DNI sin puntos, email en minúsculas)."""

    cohorte_id: UUID
    carrera_ids: tuple[UUID, ...]  # 1 o 2, en el orden en que las eligió (BR-001)
    apellido: str
    nombre: str
    nacionalidad: str
    dni: str
    telefono_movil: str
    telefono_fijo: str | None
    email: str
    email_alternativo: str | None
    domicilio: str
    ciudad: str
    provincia: str
    pais: str
    titulo_grado: str
    titulo_posgrado: str | None
    como_conocio: ComoConocio
    motivacion: str
    solicita_beca: bool
    tipo_beca: TipoBeca | None


@dataclass(frozen=True)
class LegajoDelAspirante:
    """Lo que hace falta para mandarle un link nuevo a quien recupera el acceso."""

    id: UUID
    nombre: str
    email: str
    codigo_seguimiento: str


def mensaje_periodo_cerrado(proxima_apertura: date | None) -> str:
    if proxima_apertura is None:
        return "La inscripción está cerrada"
    return f"La inscripción está cerrada. Próxima apertura: {proxima_apertura:%d/%m/%Y}"
