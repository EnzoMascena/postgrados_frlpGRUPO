"""Fábricas de datos de prueba: crean filas válidas, con un valor por defecto para todo.

Cada una guarda con `commit()` (como hacen los repositorios) y devuelve el objeto ya cargado.
Para armar un caso puntual se pisa solo lo que importa:

    cohorte = crear_cohorte(session)
    carrera = crear_carrera(session)
    legajo = crear_legajo(session, cohorte, [carrera], estado=EstadoLegajo.PENDIENTE, dni="30456789")
"""

import functools
import itertools
import secrets
from datetime import date
from typing import Any

from sqlmodel import Session, SQLModel

from src.autenticacion.infrastructure.hashing import hashear_password
from src.autenticacion.infrastructure.jwt_tokens import crear_token
from src.autenticacion.infrastructure.orm_models import UsuarioORM
from src.autenticacion.infrastructure.pg_repository import PgUsuarioRepository
from src.cohortes.domain.tipos import TipoCarrera
from src.cohortes.infrastructure.orm_models import CarreraORM, CohorteORM
from src.inscripcion.domain.tipos import ComoConocio
from src.legajos.domain.estados import EstadoLegajo
from src.legajos.infrastructure.orm_models import LegajoCarreraORM, LegajoORM
from src.shared.roles import Rol

# Contraseña de todos los usuarios de prueba: con ella se puede hacer login en los tests.
CLAVE_DE_PRUEBA = "Clave1234!"

# Un número distinto por cada fila creada: los DNI, los emails y los nombres tienen que ser únicos.
_secuencia = itertools.count(1)


def _verificar_campos(modelo: type[SQLModel], campos: dict[str, Any]) -> None:
    # Un campo mal escrito en un test se ignoraría en silencio; mejor que falle a la vista.
    desconocidos = sorted(set(campos) - set(modelo.model_fields))
    if desconocidos:
        raise TypeError(f"{modelo.__name__} no tiene los campos {desconocidos}")


def _guardar(session: Session, fila: SQLModel) -> None:
    session.add(fila)
    session.commit()
    session.refresh(fila)


@functools.cache
def _hash_de_la_clave_de_prueba() -> str:
    # bcrypt tarda unos 250 ms por hash: se calcula una sola vez por corrida y se reutiliza.
    return hashear_password(CLAVE_DE_PRUEBA)


def crear_carrera(
    session: Session,
    nombre: str | None = None,
    tipo: TipoCarrera | str = TipoCarrera.MAESTRIA,
    activa: bool = True,
) -> CarreraORM:
    carrera = CarreraORM(
        nombre=nombre or f"Carrera de prueba {next(_secuencia)}", tipo=str(tipo), activa=activa
    )
    _guardar(session, carrera)
    return carrera


def crear_cohorte(
    session: Session,
    anio: int = 2026,
    numero: int = 1,
    abierta: bool = True,
    nombre: str | None = None,
    fecha_inicio: date | None = None,
    proxima_apertura: date | None = None,
) -> CohorteORM:
    if nombre is None:
        nombre = f"Cohorte {anio}" if numero == 1 else f"Cohorte {anio}-{numero}"
    cohorte = CohorteORM(
        anio=anio,
        numero=numero,
        nombre=nombre,
        inscripcion_abierta=abierta,
        fecha_inicio=fecha_inicio,
        proxima_apertura=proxima_apertura,
    )
    _guardar(session, cohorte)
    return cohorte


def crear_usuario(
    session: Session,
    email: str | None = None,
    rol: Rol | str = Rol.COORDINADOR,
    activo: bool = True,
    nombre: str = "Coordinador de prueba",
) -> UsuarioORM:
    usuario = UsuarioORM(
        email=email or f"usuario{next(_secuencia)}@example.com",
        nombre=nombre,
        password_hash=_hash_de_la_clave_de_prueba(),
        rol=str(rol),
        activo=activo,
    )
    _guardar(session, usuario)
    return usuario


def headers_de(session: Session, usuario: UsuarioORM) -> dict[str, str]:
    """El header `Authorization: Bearer …` con un token válido para ese usuario."""
    token, _ = crear_token(PgUsuarioRepository(session).obtener(usuario.id))
    return {"Authorization": f"Bearer {token}"}


def crear_legajo(
    session: Session,
    cohorte: CohorteORM,
    carreras: list[CarreraORM],
    estado: EstadoLegajo | str = EstadoLegajo.BORRADOR,
    dni: str | None = None,
    email: str | None = None,
    **campos: Any,
) -> LegajoORM:
    """Un legajo válido de la cohorte, con sus carreras en `orden` 1, 2, ...

    `campos` pisa cualquier otra columna de `LegajoORM` (`tipo_beca`, `fecha_aprobacion`, etc.).
    """
    _verificar_campos(LegajoORM, campos)
    numero = next(_secuencia)
    datos: dict[str, Any] = {
        "cohorte_id": cohorte.id,
        "codigo_seguimiento": secrets.token_hex(4).upper(),
        "estado": str(estado),
        "apellido": "Rodríguez",
        "nombre": "Ana Laura",
        "nacionalidad": "Argentina",
        "dni": dni or str(20_000_000 + numero),
        "telefono_movil": "+54 221 4567890",
        "email": email or f"aspirante{numero}@example.com",
        "domicilio": "Av. 7 Nro. 1234",
        "ciudad": "La Plata",
        "provincia": "Buenos Aires",
        "pais": "Argentina",
        "titulo_grado": "Ingeniería en Sistemas de Información",
        "como_conocio": str(ComoConocio.EGRESADOS),
        "motivacion": "Quiero profundizar en gestión de sistemas para aplicarlo en mi trabajo.",
        "solicita_beca": False,
    }
    datos.update(campos)

    legajo = LegajoORM(**datos)
    session.add(legajo)
    session.flush()  # el legajo tiene que existir antes que sus filas de legajo_carreras
    for orden, carrera in enumerate(carreras, start=1):
        session.add(LegajoCarreraORM(legajo_id=legajo.id, orden=orden, carrera_id=carrera.id))
    session.commit()
    session.refresh(legajo)
    return legajo
