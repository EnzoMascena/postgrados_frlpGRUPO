"""`CohorteRepository` con SQLModel: lee y guarda las tablas `cohortes` y `carreras`."""

from uuid import UUID

from sqlmodel import Session, select

from src.cohortes.domain.cohorte import Carrera, Cohorte
from src.cohortes.domain.tipos import TipoCarrera
from src.cohortes.infrastructure.orm_models import CarreraORM, CohorteORM


class PgCohorteRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def listar_cohortes(self) -> list[Cohorte]:
        consulta = select(CohorteORM).order_by(CohorteORM.anio.desc(), CohorteORM.numero.desc())
        return [_cohorte_a_dominio(fila) for fila in self.session.exec(consulta)]

    def listar_carreras_activas(self) -> list[Carrera]:
        consulta = select(CarreraORM).where(CarreraORM.activa).order_by(CarreraORM.nombre)
        return [_carrera_a_dominio(fila) for fila in self.session.exec(consulta)]

    def obtener_cohorte(self, cohorte_id: UUID) -> Cohorte | None:
        fila = self.session.get(CohorteORM, cohorte_id)
        return _cohorte_a_dominio(fila) if fila else None

    def guardar_periodo(self, cohorte: Cohorte) -> None:
        # Solo los dos campos del período: el resto de la cohorte no se toca desde acá.
        fila = self.session.get_one(CohorteORM, cohorte.id)
        fila.inscripcion_abierta = cohorte.inscripcion_abierta
        fila.proxima_apertura = cohorte.proxima_apertura
        self.session.add(fila)
        self.session.commit()


def _cohorte_a_dominio(fila: CohorteORM) -> Cohorte:
    return Cohorte(
        id=fila.id,
        anio=fila.anio,
        numero=fila.numero,
        nombre=fila.nombre,
        inscripcion_abierta=fila.inscripcion_abierta,
        fecha_inicio=fila.fecha_inicio,
        proxima_apertura=fila.proxima_apertura,
    )


def _carrera_a_dominio(fila: CarreraORM) -> Carrera:
    return Carrera(id=fila.id, nombre=fila.nombre, tipo=TipoCarrera(fila.tipo))
