"""`InscripcionRepository` con SQLModel: lee cohortes y carreras y guarda el legajo nuevo."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from src.cohortes.domain.cohorte import Cohorte
from src.cohortes.infrastructure.orm_models import CarreraORM
from src.cohortes.infrastructure.pg_repository import PgCohorteRepository
from src.inscripcion.domain.inscripcion import (
    MENSAJE_DNI_REPETIDO,
    MENSAJE_EMAIL_REPETIDO,
    DatosInscripcion,
    LegajoDelAspirante,
)
from src.legajos.domain.estados import EstadoLegajo
from src.legajos.infrastructure.orm_models import LegajoCarreraORM, LegajoORM
from src.shared.errors import Conflicto

# Restricción de la base que se violó → el campo y el mensaje del 409.
_REPETIDOS = {
    "uq_legajos_cohorte_dni": ("dni", MENSAJE_DNI_REPETIDO),
    "uq_legajos_cohorte_email": ("email", MENSAJE_EMAIL_REPETIDO),
}


class PgInscripcionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def obtener_cohorte(self, cohorte_id: UUID) -> Cohorte | None:
        return PgCohorteRepository(self.session).obtener_cohorte(cohorte_id)

    def carreras_activas(self, carrera_ids: Sequence[UUID]) -> set[UUID]:
        consulta = select(CarreraORM.id).where(
            col(CarreraORM.id).in_(carrera_ids), CarreraORM.activa
        )
        return set(self.session.exec(consulta))

    def existe_dni(self, cohorte_id: UUID, dni: str) -> bool:
        return self._existe(LegajoORM.cohorte_id == cohorte_id, LegajoORM.dni == dni)

    def existe_email(self, cohorte_id: UUID, email: str) -> bool:
        return self._existe(LegajoORM.cohorte_id == cohorte_id, LegajoORM.email == email)

    def _existe(self, *condiciones) -> bool:
        return self.session.exec(select(LegajoORM.id).where(*condiciones)).first() is not None

    def crear_legajo(self, datos: DatosInscripcion, codigo_seguimiento: str) -> UUID:
        legajo = LegajoORM(
            cohorte_id=datos.cohorte_id,
            codigo_seguimiento=codigo_seguimiento,
            estado=EstadoLegajo.BORRADOR.value,
            apellido=datos.apellido,
            nombre=datos.nombre,
            nacionalidad=datos.nacionalidad,
            dni=datos.dni,
            telefono_movil=datos.telefono_movil,
            telefono_fijo=datos.telefono_fijo,
            email=datos.email,
            email_alternativo=datos.email_alternativo,
            domicilio=datos.domicilio,
            ciudad=datos.ciudad,
            provincia=datos.provincia,
            pais=datos.pais,
            titulo_grado=datos.titulo_grado,
            titulo_posgrado=datos.titulo_posgrado,
            como_conocio=datos.como_conocio.value,
            motivacion=datos.motivacion,
            solicita_beca=datos.solicita_beca,
            tipo_beca=datos.tipo_beca.value if datos.tipo_beca else None,
        )
        try:
            self.session.add(legajo)
            self.session.flush()  # el legajo tiene que existir antes que sus filas de carreras
            for orden, carrera_id in enumerate(datos.carrera_ids, start=1):
                self.session.add(
                    LegajoCarreraORM(legajo_id=legajo.id, orden=orden, carrera_id=carrera_id)
                )
            self.session.commit()
        except IntegrityError as error:
            # Dos envíos del mismo DNI o email al mismo tiempo: los dos pasaron el control previo
            # y la base frena al segundo. Se responde el mismo 409 que en el caso normal.
            self.session.rollback()
            repetido = _REPETIDOS.get(getattr(error.orig.diag, "constraint_name", None))
            if repetido is None:
                raise
            campo, mensaje = repetido
            raise Conflicto(mensaje, campo=campo) from error
        return legajo.id

    def buscar_ultimo_por_email(self, email: str) -> LegajoDelAspirante | None:
        consulta = (
            select(LegajoORM)
            .where(LegajoORM.email == email)
            .order_by(col(LegajoORM.created_at).desc())
        )
        fila = self.session.exec(consulta).first()
        if fila is None:
            return None
        return LegajoDelAspirante(
            id=fila.id,
            nombre=fila.nombre,
            email=fila.email,
            codigo_seguimiento=fila.codigo_seguimiento,
        )
