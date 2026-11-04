"""Datos de prueba para desarrollo y la demo: `uv run python -m scripts.seed` (desde backend/).

Lo corre start.sh en cada `docker compose up`. Es idempotente: cada cosa se crea solo si no
existe, buscándola por su clave natural (nombre de la carrera, nombre de la cohorte, email del
usuario, cohorte + DNI del legajo). Correrlo dos veces no duplica nada y no pisa lo que cambió
después: si la tarea de vencimiento pasó el legajo COMPLETADO a VENCIDO, sigue VENCIDO. Para
volver a tenerlo COMPLETADO: `docker compose down -v` y `docker compose up --build`.

Los datos salen de scripts/datos_seed.json, una copia recortada de docs/SEED_DATA.json (dentro
del contenedor no existe docs/). La clave del coordinador sale de la configuración, nunca del
código.
"""

import itertools
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any, NamedTuple

from sqlmodel import Session, SQLModel, select

from src.autenticacion.infrastructure.hashing import hashear_password
from src.autenticacion.infrastructure.orm_models import UsuarioORM
from src.cohortes.infrastructure.orm_models import CarreraORM, CohorteORM
from src.legajos.domain.estados import (
    Accion,
    EstadoLegajo,
    validar_comentario,
    validar_transicion,
)
from src.legajos.domain.numero_legajo import generar_numero_legajo
from src.legajos.infrastructure.orm_models import (
    AuditoriaLegajoORM,
    LegajoCarreraORM,
    LegajoORM,
)
from src.shared.config import settings
from src.shared.database import engine, importar_modelos
from src.shared.roles import Rol

DATOS = Path(__file__).with_name("datos_seed.json")
NOMBRE_COORDINADOR = "María González"

# Hace 31 días que se aprobó el legajo COMPLETADO: con 30 o más vence (BR-005), así la tarea
# de vencimiento lo agarra el día de la demo, sea cuando sea.
DIAS_DESDE_LA_APROBACION = 31

# Las fechas del JSON son días sueltos: los guardamos a las 13:00 UTC (10:00 en Argentina).
HORA_UTC = time(13, 0, tzinfo=UTC)

# Columnas que pasan del JSON al legajo tal cual.
CAMPOS_DEL_JSON = (
    "apellido",
    "nombre",
    "dni",
    "email",
    "telefono_movil",
    "domicilio",
    "ciudad",
    "provincia",
    "pais",
    "titulo_grado",
    "como_conocio",
    "motivacion",
    "solicita_beca",
    "tipo_beca",
)


@dataclass(frozen=True)
class Paso:
    """Una acción del historial, quién la hizo y `dias` después de la inscripción.

    Desde qué estado sale y a cuál llega no se escribe acá: lo dice la máquina de estados del
    legajo cuando `_historial` recorre el camino.
    """

    accion: Accion
    rol: Rol
    dias: int
    comentario: str | None = None


class CambioDeEstado(NamedTuple):
    """Un paso ya validado por la máquina de estados: una fila de la auditoría del legajo."""

    paso: Paso
    desde: EstadoLegajo
    hacia: EstadoLegajo
    fecha: datetime


ENVIAR = Paso(Accion.ENVIAR, Rol.ASPIRANTE, 0)
REVISAR = Paso(Accion.REVISAR, Rol.COORDINADOR, 2)
OBSERVAR = Paso(
    Accion.OBSERVAR, Rol.COORDINADOR, 5, "Falta la copia del título de grado legalizada"
)
APROBAR = Paso(Accion.APROBAR, Rol.COORDINADOR, 5)
MATRICULAR = Paso(Accion.MATRICULAR, Rol.COORDINADOR, 12)

# El camino que hizo cada legajo hasta su estado actual: una fila de auditoría por paso, así el
# historial del detalle no queda vacío. El BORRADOR no tiene pasos: todavía no lo envió.
CAMINOS: dict[EstadoLegajo, list[Paso]] = {
    EstadoLegajo.BORRADOR: [],
    EstadoLegajo.PENDIENTE: [ENVIAR],
    EstadoLegajo.EN_REVISION: [ENVIAR, REVISAR],
    EstadoLegajo.OBSERVADO: [ENVIAR, REVISAR, OBSERVAR],
    EstadoLegajo.COMPLETADO: [ENVIAR, REVISAR, APROBAR],
    EstadoLegajo.ACTIVO: [ENVIAR, REVISAR, APROBAR, MATRICULAR],
}

# La fecha que guarda el legajo cuando pasa por cada acción.
FECHA_DE_LA_ACCION = {
    Accion.ENVIAR: "fecha_inscripcion",
    Accion.APROBAR: "fecha_aprobacion",
    Accion.MATRICULAR: "fecha_activacion",
}


def _obtener_o_crear[T: SQLModel](
    session: Session, modelo: type[T], clave: dict[str, Any], **resto: Any
) -> tuple[T, bool]:
    """Busca la fila por su clave natural; si no está, la crea. Devuelve (fila, si es nueva)."""
    existente = session.exec(select(modelo).filter_by(**clave)).first()
    if existente:
        return existente, False
    fila = modelo(**clave, **resto)
    session.add(fila)
    session.flush()
    return fila, True


def _historial(estado: EstadoLegajo, comienzo: datetime) -> list[CambioDeEstado]:
    """Recorre el camino de `estado` desde BORRADOR con la máquina de estados del legajo.

    Cada paso pasa por `validar_comentario` y `validar_transicion`, como en la API, y el estado
    al que llega es el desde del siguiente. Si el camino tiene una transición que la máquina no
    permite, o no termina en `estado`, el seed falla y `main()` no llega a commitear nada.
    """
    historial = []
    actual = EstadoLegajo.BORRADOR
    for paso in CAMINOS[estado]:
        validar_comentario(paso.accion, paso.comentario)
        siguiente = validar_transicion(actual, paso.accion, paso.rol)
        historial.append(
            CambioDeEstado(paso, actual, siguiente, comienzo + timedelta(days=paso.dias))
        )
        actual = siguiente
    if actual != estado:
        raise RuntimeError(f"El camino del seed para {estado} termina en {actual}")
    return historial


def _crear_legajo(
    session: Session,
    cohorte: CohorteORM,
    carrera: CarreraORM,
    fila: dict[str, Any],
    comienzo: datetime,
    numero_legajo: str | None,
    email_coordinador: str,
) -> None:
    """Crea el legajo, su carrera y una fila de auditoría por cada paso de su camino.

    `comienzo` es la fecha de inscripción; para el BORRADOR, la fecha en que empezó el
    formulario (todavía no tiene inscripción).
    """
    estado = EstadoLegajo(fila["estado"])
    historial = _historial(estado, comienzo)
    fechas = {
        FECHA_DE_LA_ACCION[cambio.paso.accion]: cambio.fecha
        for cambio in historial
        if cambio.paso.accion in FECHA_DE_LA_ACCION
    }

    usuario_del_email = fila["email"].split("@")[0]
    legajo = LegajoORM(
        cohorte_id=cohorte.id,
        codigo_seguimiento=secrets.token_hex(4).upper(),
        numero_legajo=numero_legajo,
        estado=estado.value,
        nacionalidad="Argentina",
        email_alternativo=f"{usuario_del_email}.alternativo@example.com",
        created_at=comienzo - timedelta(hours=1),
        updated_at=historial[-1].fecha if historial else comienzo,
        **{campo: fila[campo] for campo in CAMPOS_DEL_JSON},
        **fechas,
    )
    session.add(legajo)
    session.flush()  # el legajo tiene que existir antes que sus carreras y su auditoría

    session.add(LegajoCarreraORM(legajo_id=legajo.id, orden=1, carrera_id=carrera.id))
    for paso, desde, hacia, fecha in historial:
        session.add(
            AuditoriaLegajoORM(
                legajo_id=legajo.id,
                accion=paso.accion.value,
                estado_anterior=desde.value,
                estado_nuevo=hacia.value,
                comentario=paso.comentario,
                rol=paso.rol.value,
                usuario_email=email_coordinador if paso.rol == Rol.COORDINADOR else None,
                created_at=fecha,
            )
        )


def cargar_datos(session: Session) -> dict[str, int]:
    """Crea lo que falte de los datos de prueba y devuelve cuántos hay de cada cosa.

    No hace commit: lo hace `main()`, así una corrida que falla a la mitad no deja nada a medias.
    """
    email = settings.seed_coordinador_email
    clave = settings.seed_coordinador_password
    if not email or not clave:
        raise RuntimeError("Faltan SEED_COORDINADOR_EMAIL y SEED_COORDINADOR_PASSWORD en el .env")

    datos = json.loads(DATOS.read_text(encoding="utf-8"))
    nuevos = 0

    carreras: dict[str, CarreraORM] = {}
    for fila in datos["carreras"]:
        carrera, es_nueva = _obtener_o_crear(
            session, CarreraORM, {"nombre": fila["nombre"]}, tipo=fila["tipo"]
        )
        carreras[carrera.nombre] = carrera
        nuevos += es_nueva

    cohortes: dict[str, CohorteORM] = {}
    for fila in datos["cohortes"]:
        cohorte, es_nueva = _obtener_o_crear(
            session,
            CohorteORM,
            {"nombre": fila["nombre"]},
            anio=fila["anio"],
            numero=1,
            inscripcion_abierta=fila["inscripcion_abierta"],
            fecha_inicio=date.fromisoformat(fila["fecha_inicio"]),
        )
        cohortes[cohorte.nombre] = cohorte
        nuevos += es_nueva

    # El coordinador se busca aparte: bcrypt tarda, y si ya existe no hace falta hashear nada.
    if not session.exec(select(UsuarioORM).where(UsuarioORM.email == email)).first():
        session.add(
            UsuarioORM(
                email=email,
                nombre=NOMBRE_COORDINADOR,
                password_hash=hashear_password(clave),
                rol=Rol.COORDINADOR.value,
            )
        )
        nuevos += 1

    cohorte = cohortes["Cohorte 2026"]
    ahora = datetime.now(UTC)
    # El secuencial sale del orden del JSON, no de lo que ya hay en la base: así cada legajo
    # tiene siempre el mismo número, se cree en esta corrida o en una anterior.
    secuenciales = itertools.count(1)
    aspirantes = [*datos["aspirantes_cohorte_2026"], datos["aspirante_que_vence"]]
    for fila in aspirantes:
        estado = EstadoLegajo(fila["estado"])
        numero = None
        if APROBAR in CAMINOS[estado]:  # el número se asigna al aprobar (plan §9)
            numero = generar_numero_legajo(cohorte.anio, cohorte.numero, next(secuenciales))

        existe = session.exec(
            select(LegajoORM).where(
                LegajoORM.cohorte_id == cohorte.id, LegajoORM.dni == fila["dni"]
            )
        ).first()
        if existe:
            continue

        if fila["fecha_inscripcion"]:
            comienzo = datetime.combine(date.fromisoformat(fila["fecha_inscripcion"]), HORA_UTC)
        else:
            # El que vence: se inscribió de modo que la aprobación caiga hace 31 días.
            comienzo = ahora - timedelta(days=DIAS_DESDE_LA_APROBACION + APROBAR.dias)
        _crear_legajo(session, cohorte, carreras[fila["carrera"]], fila, comienzo, numero, email)
        nuevos += 1

    return {
        "carreras": len(carreras),
        "cohortes": len(cohortes),
        "coordinadores": 1,
        "legajos": len(aspirantes),
        "nuevos": nuevos,
    }


def main() -> None:
    importar_modelos()
    with Session(engine) as session:
        resumen = cargar_datos(session)
        session.commit()
    print(
        f"Seed: {resumen['carreras']} carreras, {resumen['cohortes']} cohortes, "
        f"{resumen['coordinadores']} coordinador, {resumen['legajos']} legajos; "
        f"{resumen['nuevos']} nuevos"
    )


if __name__ == "__main__":
    main()
