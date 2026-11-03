"""`LegajoRepository` y `DetalleRepository` con SQLModel: lee y escribe `legajos` y
`auditoria_legajos`, y lee lo que el detalle necesita de `cohortes`, `carreras` y `documentos`.

Devuelve las entidades del dominio y los datos del caso de uso (`Legajo`, `FichaLegajo`, …),
nunca las filas ORM: así `ServicioEstados` y `obtener_detalle` no se enteran de que hay una base.
"""

from uuid import UUID

from sqlmodel import Session, select

from src.cohortes.domain.tipos import TipoCarrera
from src.cohortes.infrastructure.orm_models import CarreraORM, CohorteORM
from src.gestion_documental.domain.tipos import TipoDocumento
from src.gestion_documental.infrastructure.orm_models import DocumentoORM
from src.inscripcion.domain.tipos import ComoConocio, TipoBeca
from src.legajos.application.obtener_detalle import (
    CarreraResumen,
    CohorteResumen,
    DocumentoCargado,
    FichaLegajo,
)
from src.legajos.domain.entidades import DatosCohorte, Legajo, RegistroAuditoria
from src.legajos.domain.estados import Accion, EstadoLegajo
from src.legajos.infrastructure.orm_models import AuditoriaLegajoORM, LegajoCarreraORM, LegajoORM
from src.shared.errors import NoEncontrado
from src.shared.roles import Rol


class PgLegajoRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def obtener(self, legajo_id: UUID) -> Legajo | None:
        fila = self.session.get(LegajoORM, legajo_id)
        return _a_dominio(fila) if fila else None

    def siguiente_secuencial(self, cohorte_id: UUID) -> int:
        # SELECT … FOR UPDATE sobre la cohorte: otra aprobación de la misma cohorte espera acá
        # hasta que esta transacción haga commit (en `guardar_cambio`), y recién ahí lee el máximo.
        self.session.exec(
            select(CohorteORM.id).where(CohorteORM.id == cohorte_id).with_for_update()
        ).one()

        numeros = self.session.exec(
            select(LegajoORM.numero_legajo).where(
                LegajoORM.cohorte_id == cohorte_id, LegajoORM.numero_legajo.is_not(None)
            )
        ).all()
        # `AA-CCC-SSS`: el secuencial son los últimos tres dígitos. Se toma el mayor usado, no la
        # cantidad: los vencidos conservan su número y el seed puede haber dejado huecos.
        usados = [int(numero.rsplit("-", 1)[1]) for numero in numeros]
        return max(usados, default=0) + 1

    def datos_cohorte(self, cohorte_id: UUID) -> DatosCohorte:
        cohorte = self.session.get(CohorteORM, cohorte_id)
        if cohorte is None:
            raise NoEncontrado("No encontramos la cohorte del legajo")
        return DatosCohorte(anio=cohorte.anio, numero=cohorte.numero, nombre=cohorte.nombre)

    def nombres_carreras(self, legajo_id: UUID) -> list[str]:
        return list(
            self.session.exec(
                select(CarreraORM.nombre)
                .join(LegajoCarreraORM, LegajoCarreraORM.carrera_id == CarreraORM.id)
                .where(LegajoCarreraORM.legajo_id == legajo_id)
                .order_by(LegajoCarreraORM.orden)
            ).all()
        )

    def guardar_cambio(self, legajo: Legajo, registro: RegistroAuditoria) -> None:
        fila = self.session.get(LegajoORM, legajo.id)
        if fila is None:
            raise NoEncontrado("No encontramos el legajo")
        fila.estado = legajo.estado.value
        fila.numero_legajo = legajo.numero_legajo
        fila.fecha_inscripcion = legajo.fecha_inscripcion
        fila.fecha_aprobacion = legajo.fecha_aprobacion
        fila.fecha_activacion = legajo.fecha_activacion

        self.session.add(fila)
        self.session.add(
            AuditoriaLegajoORM(
                legajo_id=registro.legajo_id,
                accion=registro.accion.value,
                estado_anterior=registro.estado_anterior.value,
                estado_nuevo=registro.estado_nuevo.value,
                comentario=registro.comentario,
                rol=registro.rol.value,
                usuario_email=registro.usuario_email,
                created_at=registro.fecha,
            )
        )
        # Un solo commit: el estado y su auditoría quedan los dos o ninguno. También libera el
        # bloqueo de la cohorte que tomó `siguiente_secuencial`.
        self.session.commit()

    # --- Lo que lee el detalle (`obtener_detalle`) ---

    def ficha(self, legajo_id: UUID) -> FichaLegajo | None:
        fila = self.session.get(LegajoORM, legajo_id)
        if fila is None:
            return None
        cohorte = self.session.get(CohorteORM, fila.cohorte_id)
        carreras = self.session.exec(
            select(CarreraORM)
            .join(LegajoCarreraORM, LegajoCarreraORM.carrera_id == CarreraORM.id)
            .where(LegajoCarreraORM.legajo_id == legajo_id)
            .order_by(LegajoCarreraORM.orden)
        ).all()
        return FichaLegajo(
            id=fila.id,
            codigo_seguimiento=fila.codigo_seguimiento,
            numero_legajo=fila.numero_legajo,
            estado=EstadoLegajo(fila.estado),
            cohorte=CohorteResumen(id=cohorte.id, nombre=cohorte.nombre, anio=cohorte.anio),
            carreras=[
                CarreraResumen(id=carrera.id, nombre=carrera.nombre, tipo=TipoCarrera(carrera.tipo))
                for carrera in carreras
            ],
            apellido=fila.apellido,
            nombre=fila.nombre,
            nacionalidad=fila.nacionalidad,
            dni=fila.dni,
            telefono_movil=fila.telefono_movil,
            telefono_fijo=fila.telefono_fijo,
            email=fila.email,
            email_alternativo=fila.email_alternativo,
            domicilio=fila.domicilio,
            ciudad=fila.ciudad,
            provincia=fila.provincia,
            pais=fila.pais,
            titulo_grado=fila.titulo_grado,
            titulo_posgrado=fila.titulo_posgrado,
            como_conocio=ComoConocio(fila.como_conocio),
            motivacion=fila.motivacion,
            solicita_beca=fila.solicita_beca,
            tipo_beca=TipoBeca(fila.tipo_beca) if fila.tipo_beca else None,
            fecha_inscripcion=fila.fecha_inscripcion,
            fecha_aprobacion=fila.fecha_aprobacion,
            fecha_activacion=fila.fecha_activacion,
            created_at=fila.created_at,
        )

    def documentos_cargados(self, legajo_id: UUID) -> list[DocumentoCargado]:
        # Solo los datos del archivo: el path en disco y el checksum no salen de acá.
        filas = self.session.exec(
            select(DocumentoORM).where(DocumentoORM.legajo_id == legajo_id)
        ).all()
        return [
            DocumentoCargado(
                id=fila.id,
                tipo=TipoDocumento(fila.tipo),
                nombre_original=fila.nombre_original,
                tamanio_bytes=fila.tamanio_bytes,
                fecha_subida=fila.fecha_subida,
            )
            for fila in filas
        ]

    def historial(self, legajo_id: UUID) -> list[RegistroAuditoria]:
        filas = self.session.exec(
            select(AuditoriaLegajoORM)
            .where(AuditoriaLegajoORM.legajo_id == legajo_id)
            .order_by(AuditoriaLegajoORM.created_at)
        ).all()
        return [
            RegistroAuditoria(
                legajo_id=fila.legajo_id,
                accion=Accion(fila.accion),
                estado_anterior=EstadoLegajo(fila.estado_anterior),
                estado_nuevo=EstadoLegajo(fila.estado_nuevo),
                comentario=fila.comentario,
                rol=Rol(fila.rol),
                usuario_email=fila.usuario_email,
                fecha=fila.created_at,
            )
            for fila in filas
        ]


def _a_dominio(fila: LegajoORM) -> Legajo:
    return Legajo(
        id=fila.id,
        cohorte_id=fila.cohorte_id,
        estado=EstadoLegajo(fila.estado),
        numero_legajo=fila.numero_legajo,
        codigo_seguimiento=fila.codigo_seguimiento,
        nombre=fila.nombre,
        apellido=fila.apellido,
        email=fila.email,
        fecha_inscripcion=fila.fecha_inscripcion,
        fecha_aprobacion=fila.fecha_aprobacion,
        fecha_activacion=fila.fecha_activacion,
    )
