"""
Seed de desarrollo — los datos de prueba de TODAS las pantallas.

    uv run python -m app.seed        (start.sh lo corre en cada arranque)

Reproduce lo que hoy muestran los mocks del front (mismos nombres, números
parecidos), para que cada pantalla se vea igual al pasar del mock a la API:

  - Usuarios: los de docs/SEED_DATA.json, con su password_plano hasheada al
    sembrar. Sin el docente: el docente entra con el link, no con usuario.
  - Carreras: las del formulario, con el nombre corto de las tablas.
  - Cohortes 2022 a 2026: Estadísticas muestra el histórico desde 2022.
  - 2026: los 8 inscriptos del Dashboard, los 10 aspirantes de SEED_DATA y
    2 más, en TODOS los estados del workflow, con y sin beca, con la
    documentación completa e incompleta.
  - 2022 a 2025: los totales de Estadísticas (graduados, bajas y activos),
    con legajos generados de forma determinística.
  - Seminarios, clases, asistencias y notas: la grilla de la Planilla y el
    legajo académico de Enzo. Más trabajos finales y tutorías.
  - Un link de docente vigente y uno de seguimiento del aspirante, que se
    imprimen al terminar.

IDEMPOTENTE, como el seed del módulo 06: cada fila tiene un UUID fijo (un
uuid5 de una clave estable) y solo se inserta si todavía no existe. Correrlo
dos veces no duplica nada, y si falta un PDF en disco lo vuelve a escribir.

Las fechas son relativas a hoy (clases dictadas y una futura, legajos
completados hace más y menos de 30 días). Como el seed no pisa las filas que
ya existen, quedan fijas desde la primera corrida: para regenerarlas, borrar
la base y volver a migrar.

Los datos de docs/SEED_DATA.json están copiados acá: en la imagen de Docker
solo viaja backend/, no docs/.
"""

import base64
import hashlib
import hmac
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from sqlmodel import Session, SQLModel, select

from app.core import config
from app.core.database import engine
from app.core.security import crear_token_aspirante, hash_password, hash_token_opaco
from app.core.storage import ruta_del_pdf
from app.models import (
    AccesoDocente,
    Asistencia,
    AuditoriaLegajo,
    Carrera,
    Clase,
    Cohorte,
    Cursada,
    Documento,
    Legajo,
    Seminario,
    TrabajoFinal,
    Tutoria,
    Usuario,
)
from app.models.enums import (
    AccionLegajo,
    ComoConocio,
    CondicionCursada,
    EstadoLegajo,
    RolUsuario,
    Semaforo,
    TipoBeca,
    TipoCarrera,
    TipoDocumento,
    TipoTrabajoFinal,
)

E = EstadoLegajo

# ── Identificadores estables ───────────────────────────────────────────────

_NAMESPACE = uuid.UUID("0f1e2d3c-4b5a-4968-8776-655443322110")


def _id(*partes: object) -> uuid.UUID:
    """UUID fijo a partir de una clave: el mismo en cada corrida (uuid5)."""
    return uuid.uuid5(_NAMESPACE, ":".join(str(parte) for parte in partes))


# ── Usuarios (SEED_DATA.json, sin el docente) ──────────────────────────────

USUARIOS = (
    ("admin@fenix.test", "María González", RolUsuario.COORDINADOR, "Admin1234!"),
    ("cpr@fenix.test", "Laura Martínez", RolUsuario.CPR, "Cpr1234!"),
)
EMAIL_COORDINADOR = USUARIOS[0][0]

# ── Oferta académica ───────────────────────────────────────────────────────

# clave: (nombre del formulario, nombre corto de las tablas, tipo)
CARRERAS = {
    "ESP": (
        "Especialización en Ingeniería en Sistemas",
        "Esp. Ing. Sistemas",
        TipoCarrera.ESPECIALIZACION,
    ),
    "MAE": ("Maestría en Ingeniería en Sistemas", "Maestría", TipoCarrera.MAESTRIA),
    "DOC": ("Doctorado en Ingeniería", "Doctorado", TipoCarrera.DOCTORADO),
}

# anio: (id, fecha de inicio). Los ids de 2024 a 2026 son los de SEED_DATA.
COHORTES = {
    2022: (_id("cohorte", 2022), date(2022, 3, 14)),
    2023: (_id("cohorte", 2023), date(2023, 3, 13)),
    2024: (uuid.UUID("c1a2b3c4-0001-0000-0000-000000000001"), date(2024, 3, 15)),
    2025: (uuid.UUID("c1a2b3c4-0001-0000-0000-000000000002"), date(2025, 3, 20)),
    2026: (uuid.UUID("c1a2b3c4-0001-0000-0000-000000000003"), date(2026, 4, 1)),
}
ANIO_ACTUAL = 2026

# Los totales de la pantalla de Estadísticas:
# anio: (inscriptos, graduados, desgranados, activos, ralentizados)
HISTORICO = {
    2025: (41, 3, 6, 32, 5),
    2024: (38, 20, 8, 10, 4),
    2023: (36, 26, 7, 3, 2),
    2022: (22, 18, 3, 1, 0),
}

MOTIVACION = (
    "Quiero profundizar mi formación en sistemas de información para aplicarla en mi "
    "trabajo y en proyectos tecnológicos de la región."
)

DOCUMENTOS_OBLIGATORIOS = (
    TipoDocumento.FORM_INSCRIPCION,
    TipoDocumento.DNI,
    TipoDocumento.TITULO_GRADO,
    TipoDocumento.PARTIDA,
    TipoDocumento.CUIT_CUIL,
)

# Las mismas etiquetas que las cajas de UploadBox del formulario.
ETIQUETA_DOCUMENTO = {
    TipoDocumento.FORM_INSCRIPCION: "Formulario de preinscripción firmado",
    TipoDocumento.DNI: "Copia del DNI",
    TipoDocumento.TITULO_GRADO: "Copia del título de grado",
    TipoDocumento.PARTIDA: "Partida de nacimiento",
    TipoDocumento.CUIT_CUIL: "Constancia de CUIT / CUIL",
    TipoDocumento.TITULO_POSGRADO: "Copia del título de posgrado",
    TipoDocumento.FORM_BECA: "Formulario de beca firmado",
}

ESTADOS_APROBADOS = {E.COMPLETADO, E.ACTIVO, E.VENCIDO, E.GRADUADO, E.BAJA}


@dataclass(frozen=True)
class Persona:
    """Los datos de un legajo a sembrar."""

    clave: str
    apellido: str
    nombre: str
    dni: str
    email: str
    carrera: str
    estado: EstadoLegajo
    beca: TipoBeca | None = None
    carrera_secundaria: str | None = None
    titulo_grado: str = "Ing. en Sistemas"
    titulo_posgrado: str | None = None
    telefono_movil: str = "+54 221 4000000"
    domicilio: str = "Calle 7 Nro. 1000"
    ciudad: str = "La Plata"
    provincia: str = "Buenos Aires"
    como_conocio: ComoConocio = ComoConocio.SITIO_WEB_UTN
    motivacion: str = MOTIVACION
    faltantes: tuple[TipoDocumento, ...] = ()
    semaforo: Semaforo = Semaforo.VERDE
    semaforo_manual: bool = False
    comentario: str | None = None
    fecha_envio: date | None = None
    fecha_completado: date | None = None
    fecha_activacion: date | None = None


def _personas_2026(hoy: date) -> list[Persona]:
    """Cohorte 2026: Dashboard (8) + SEED_DATA (10) + un vencido y un rechazado."""

    def hace(dias: int) -> date:
        return hoy - timedelta(days=dias)

    matricula = {"fecha_completado": date(2026, 3, 10), "fecha_activacion": date(2026, 4, 1)}
    # fmt: off
    return [
        # ── Los 8 del Dashboard ─────────────────────────────────────────────
        Persona(
            "dash-i1", "Mascena", "Enzo", "38500000", "enzo@mail.com", "ESP", E.ACTIVO,
            semaforo=Semaforo.AMARILLO, fecha_envio=date(2026, 2, 16), **matricula,
        ),
        Persona(
            "dash-i2", "García", "María", "41200111", "mgarcia@mail.com", "MAE", E.ACTIVO,
            beca=TipoBeca.BECA_30, titulo_grado="Ing. Civil", fecha_envio=date(2026, 2, 18),
            **matricula,
        ),
        Persona(
            "dash-i3", "López", "Tomás", "39800444", "tlopez@mail.com", "DOC", E.ACTIVO,
            beca=TipoBeca.BECA_100, titulo_grado="Ing. Eléctrica",
            semaforo=Semaforo.AMARILLO, fecha_envio=date(2026, 2, 20), **matricula,
        ),
        Persona(
            "dash-i4", "Ramírez", "Lucía", "40500222", "lramirez@mail.com", "ESP",
            E.COMPLETADO, titulo_grado="Lic. en Informática",
            fecha_envio=hace(30), fecha_completado=hace(10),
        ),
        Persona(
            "dash-i5", "Fernández", "Diego", "37910333", "dfernandez@mail.com", "MAE",
            E.COMPLETADO, titulo_grado="Ing. Industrial",
            fecha_envio=hace(60), fecha_completado=hace(40),
        ),
        Persona(
            "dash-i6", "Sosa", "Valentina", "42115678", "vsosa@mail.com", "ESP",
            E.EN_REVISION, beca=TipoBeca.BECA_30, fecha_envio=hace(12),
        ),
        Persona(
            "dash-i7", "Benítez", "Martín", "36400900", "mbenitez@mail.com", "DOC",
            E.OBSERVADO, titulo_grado="Lic. en Matemática",
            faltantes=(TipoDocumento.TITULO_GRADO, TipoDocumento.CUIT_CUIL),
            comentario="Falta la copia del título de grado y la constancia de CUIT / CUIL.",
            fecha_envio=hace(20),
        ),
        Persona(
            "dash-i8", "Quiroga", "Sofía", "43020155", "squiroga@mail.com", "MAE",
            E.PENDIENTE, beca=TipoBeca.BECA_100, carrera_secundaria="ESP",
            titulo_grado="Ing. Electrónica", fecha_envio=hace(5),
        ),
        # ── Los 10 de SEED_DATA.json ────────────────────────────────────────
        Persona(
            "leg-2026-001", "Rodríguez", "Ana Laura", "28456789", "ana.rodriguez@gmail.com",
            "ESP", E.ACTIVO, titulo_grado="Ingeniería en Sistemas de Información",
            telefono_movil="+54 221 4567890", domicilio="Av. 7 Nro. 1234",
            como_conocio=ComoConocio.EGRESADOS_UTN,
            motivacion=(
                "Deseo profundizar mis conocimientos en gestión de sistemas para aplicarlos "
                "en mi trabajo actual como analista en una empresa de tecnología de la región."
            ),
            fecha_envio=date(2026, 3, 2), fecha_completado=date(2026, 3, 16),
            fecha_activacion=date(2026, 4, 1),
        ),
        Persona(
            "leg-2026-002", "Fernández", "Martín Alejandro", "32567891",
            "m.fernandez.dev@outlook.com", "MAE", E.EN_REVISION, beca=TipoBeca.BECA_30,
            titulo_grado="Licenciatura en Sistemas", telefono_movil="+54 221 5678901",
            domicilio="Calle 51 Nro. 890", ciudad="Berisso",
            motivacion=(
                "Mi objetivo es acceder a roles de arquitectura de software y para eso "
                "necesito fortalecer la base académica con una maestría que complemente mi "
                "experiencia de 5 años en desarrollo."
            ),
            fecha_envio=date(2026, 4, 5),
        ),
        Persona(
            "leg-2026-003", "López", "Sofía Valentina", "35123456",
            "sofia.lopez.ingenieria@gmail.com", "ESP", E.PENDIENTE,
            titulo_grado="Ingeniería Industrial", telefono_movil="+54 11 5432-1098",
            domicilio="Av. Corrientes 2345 Piso 3 Dto B", ciudad="Buenos Aires",
            como_conocio=ComoConocio.COLEGAS,
            motivacion=(
                "Busco reconvertir mi perfil hacia el área de tecnología e innovación, "
                "combinando mi formación en ingeniería industrial con herramientas digitales "
                "modernas."
            ),
            fecha_envio=date(2026, 4, 8),
        ),
        Persona(
            "leg-2026-004", "García", "Roberto Carlos", "29876543",
            "roberto.garcia@empresa.com.ar", "ESP", E.OBSERVADO,
            titulo_grado="Ingeniería en Sistemas de Información",
            telefono_movil="+54 221 3456789", domicilio="Calle 13 Nro. 456",
            como_conocio=ComoConocio.EGRESADOS_UTN, faltantes=(TipoDocumento.PARTIDA,),
            comentario="Falta la partida de nacimiento.",
            motivacion=(
                "Soy docente universitario y la especialización me permitirá mejorar la "
                "calidad académica de mis clases y actualizar los contenidos con la visión "
                "más moderna de la industria."
            ),
            fecha_envio=date(2026, 4, 3),
        ),
        Persona(
            "leg-2026-005", "Martínez", "Lucía Beatriz", "33210987",
            "lucia.martinez.it@hotmail.com", "DOC", E.PENDIENTE, beca=TipoBeca.BECA_100,
            titulo_grado="Licenciatura en Informática", telefono_movil="+54 11 6789-0123",
            domicilio="Diagonal 74 Nro. 789", como_conocio=ComoConocio.OTROS_SITIOS_WEB,
            motivacion=(
                "Mi proyecto de investigación sobre aprendizaje automático aplicado a la "
                "salud requiere una formación doctoral rigurosa. El grupo de investigación de "
                "UTN FRLP es reconocido en mi área de interés."
            ),
            fecha_envio=date(2026, 4, 10),
        ),
        Persona(
            # El BORRADOR: a medio completar, sin enviar. Su link de seguimiento se
            # imprime al final para probar el menú del aspirante.
            "leg-2026-006", "Sánchez", "Diego Hernán", "31654321",
            "dsanchez@consultora.com.ar", "ESP", E.BORRADOR,
            titulo_grado="Ingeniería en Electrónica", telefono_movil="+54 221 7654321",
            domicilio="Av. 44 Nro. 1100",
            faltantes=(
                TipoDocumento.TITULO_GRADO,
                TipoDocumento.PARTIDA,
                TipoDocumento.CUIT_CUIL,
            ),
            motivacion=(
                "La transformación digital de la industria manufacturera requiere perfiles "
                "que entiendan tanto el dominio técnico físico como los sistemas de "
                "información. Esta especialización cubre exactamente esa brecha."
            ),
        ),
        Persona(
            "leg-2026-007", "Torres", "Carolina Andrea", "34789012",
            "caro.torres.sistemas@gmail.com", "MAE", E.ACTIVO, beca=TipoBeca.BECA_30,
            titulo_grado="Ingeniería en Sistemas de Información",
            telefono_movil="+54 221 8901234", domicilio="Calle 60 Nro. 234 Depto 5A",
            como_conocio=ComoConocio.EGRESADOS_UTN, semaforo=Semaforo.AMARILLO,
            motivacion=(
                "Quiero investigar sobre arquitecturas de microservicios y su aplicabilidad "
                "en organizaciones del sector público argentino, un área con escasa "
                "investigación local."
            ),
            fecha_envio=date(2026, 3, 2), fecha_completado=date(2026, 3, 16),
            fecha_activacion=date(2026, 4, 1),
        ),
        Persona(
            "leg-2026-008", "Romero", "Pablo Andrés", "27345678",
            "pablo.romero.lic@yahoo.com.ar", "DOC", E.EN_REVISION, beca=TipoBeca.BECA_100,
            titulo_grado="Licenciatura en Matemática", telefono_movil="+54 11 9012-3456",
            domicilio="Av. 13 Nro. 2890", ciudad="Ensenada", como_conocio=ComoConocio.COLEGAS,
            motivacion=(
                "Mi investigación en matemática discreta tiene aplicaciones directas en "
                "criptografía y seguridad informática. El doctorado me permitirá desarrollar "
                "esta línea con el rigor académico necesario."
            ),
            fecha_envio=date(2026, 4, 6),
        ),
        Persona(
            "leg-2026-009", "Gómez", "Valeria Inés", "36012345",
            "valeria.gomez.eng@protonmail.com", "ESP", E.ACTIVO,
            titulo_grado="Ingeniería en Sistemas de Información",
            telefono_movil="+54 221 0123456", domicilio="Calle 8 Nro. 567",
            motivacion=(
                "Trabajo como líder de proyectos de transformación digital en el sector "
                "bancario. La especialización me dará el marco teórico para estructurar mejor "
                "mi práctica profesional."
            ),
            fecha_envio=date(2026, 3, 1), fecha_completado=date(2026, 3, 16),
            fecha_activacion=date(2026, 4, 1),
        ),
        Persona(
            "leg-2026-010", "Herrera", "Gonzalo Sebastián", "30987654",
            "g.herrera.devops@gmail.com", "ESP", E.PENDIENTE, titulo_grado="Analista de Sistemas",
            telefono_movil="+54 221 2109876", domicilio="Av. 32 Nro. 1450", ciudad="Berisso",
            como_conocio=ComoConocio.OTROS_SITIOS_WEB,
            motivacion=(
                "Como analista con 10 años de experiencia, siento que necesito formalizar y "
                "actualizar mis conocimientos. La especialización presencial me permite "
                "hacerlo sin descuidar mi trabajo."
            ),
            fecha_envio=date(2026, 4, 9),
        ),
        # ── Para que estén todos los estados ────────────────────────────────
        Persona(
            "extra-vencido", "Paz", "Joaquín", "39555111", "jpaz@mail.com", "ESP", E.VENCIDO,
            fecha_envio=hace(80), fecha_completado=hace(45),
        ),
        Persona(
            "extra-rechazado", "Rivas", "Florencia", "40777222", "frivas@mail.com", "MAE",
            E.RECHAZADO, titulo_grado="Tecnicatura en Programación",
            comentario="El título de grado no corresponde a una carrera de 4 años o más.",
            fecha_envio=hace(35),
        ),
    ]
    # fmt: on


# Los inscriptos del Dashboard de cohortes anteriores (todos activos).
NOMBRADOS_HISTORICO = {
    2025: [
        ("dash-i9", "Álvarez", "Nicolás", "35700480", "MAE", None, "Esp. en Redes"),
        ("dash-i10", "Molina", "Camila", "38045712", "ESP", TipoBeca.BECA_30, None),
        ("dash-i11", "Herrera", "Pablo", "34220865", "DOC", None, None),
    ],
    2024: [
        ("dash-i12", "Cabrera", "Julieta", "33980041", "MAE", None, "Esp. en Software"),
        ("dash-i13", "Duarte", "Iván", "32560777", "ESP", TipoBeca.BECA_100, None),
    ],
}

APELLIDOS = (
    "Acosta", "Aguirre", "Blanco", "Castro", "Correa", "Díaz", "Domínguez", "Figueroa",
    "Flores", "Giménez", "Godoy", "Gutiérrez", "Ibáñez", "Juárez", "Ledesma", "Luna",
    "Medina", "Méndez", "Morales", "Navarro", "Ojeda", "Ortiz", "Peralta", "Ponce",
    "Ramos", "Ríos", "Rojas", "Suárez", "Vera", "Villalba",
)  # fmt: skip
NOMBRES = (
    "Agustín", "Alejandra", "Andrés", "Belén", "Bruno", "Carla", "Cristian", "Daniela",
    "Emiliano", "Florencia", "Franco", "Gabriela", "Gastón", "Julieta", "Leandro", "Lorena",
    "Lucas", "Marina", "Matías", "Micaela", "Nahuel", "Natalia", "Nicolás", "Paula",
    "Ramiro", "Rocío", "Santiago", "Silvina", "Tomás", "Victoria",
)  # fmt: skip
TITULOS_TFI = (
    "Modelo de madurez para equipos ágiles en PyMEs",
    "Tablero de indicadores para la gestión académica",
    "Arquitectura de microservicios para el sector público",
    "Gestión de riesgos en proyectos de software",
    "Calidad de datos en sistemas de salud",
    "Automatización de pruebas en integración continua",
)
DIRECTORES = ("Dr. Pérez, Juan", "Mg. Castro, Elena", "Dra. Molina, Inés", "Mg. Suárez, Raúl")


def _slug(texto: str) -> str:
    """ "Ibáñez" → "ibanez": para armar emails sin acentos."""
    sin_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return "".join(letra for letra in sin_acentos.lower() if letra.isalnum())


def _personas_historicas(anio: int) -> list[Persona]:
    """Una cohorte pasada con los totales de Estadísticas."""
    inscriptos, graduados, desgranados, activos, ralentizados = HISTORICO[anio]
    fechas = {
        "fecha_completado": date(anio, 2, 20),
        "fecha_activacion": COHORTES[anio][1],
    }
    estados = [E.GRADUADO] * graduados + [E.BAJA] * desgranados + [E.ACTIVO] * activos
    assert len(estados) == inscriptos

    nombrados = NOMBRADOS_HISTORICO.get(anio, [])
    personas: list[Persona] = []
    activos_vistos = 0
    for indice, estado in enumerate(estados):
        semaforo, manual = Semaforo.VERDE, False
        if estado is E.ACTIVO:
            if activos_vistos < ralentizados:
                semaforo = Semaforo.AMARILLO if activos_vistos % 2 == 0 else Semaforo.ROJO
            elif activos_vistos == ralentizados and anio == 2024:
                manual = True  # un VERDE puesto a mano por el coordinador (BR-008)
            activos_vistos += 1

        # Los inscriptos del Dashboard ocupan los últimos lugares de activos.
        lugar_nombrado = indice - (inscriptos - len(nombrados))
        if estado is E.ACTIVO and lugar_nombrado >= 0:
            clave, apellido, nombre, dni, carrera, beca, posgrado = nombrados[lugar_nombrado]
            email = f"{_slug(nombre)[0]}{_slug(apellido)}@mail.com"
        else:
            clave = f"hist-{anio}-{indice:02d}"
            apellido = APELLIDOS[(indice * 7 + anio) % len(APELLIDOS)]
            nombre = NOMBRES[(indice * 11 + anio) % len(NOMBRES)]
            dni = str(20_000_000 + (anio - 2000) * 100_000 + indice * 97)
            carrera = ("ESP", "MAE", "DOC")[indice % 3]
            beca = (
                TipoBeca.BECA_30
                if indice % 5 == 1
                else TipoBeca.BECA_100
                if indice % 9 == 4
                else None
            )
            posgrado = None
            email = f"{_slug(nombre)}.{_slug(apellido)}.{anio}{indice:02d}@example.com"

        personas.append(
            Persona(
                clave,
                apellido,
                nombre,
                dni,
                email,
                carrera,
                estado,
                beca=beca,
                titulo_posgrado=posgrado,
                telefono_movil=f"+54 221 {4_000_000 + indice * 37 + anio}",
                como_conocio=tuple(ComoConocio)[indice % len(ComoConocio)],
                semaforo=semaforo,
                semaforo_manual=manual,
                fecha_envio=date(anio - 1, 12, 1 + indice % 20),
                **fechas,
            )
        )
    return personas


# ── Seminarios de la cohorte 2026 (Esp. Ing. Sistemas) ─────────────────────

# clave: (nombre del Legajo, código, horas, obligatorio, docente, email). Los
# nombres salen del mock del Legajo; la docente de GPS, del de la Planilla.
SEMINARIOS = {
    "GPS": ("Gestión de Proyectos de Software", "GPS-001", 32, True,
            "Ing. Rodríguez, Ana", "a.rodriguez@frlp.utn.edu.ar"),
    "ARQ": ("Arquitecturas de Software", "ARQ-001", 48, True,
            "Ing. Díaz, Marcelo", "m.diaz@frlp.utn.edu.ar"),
    "SEG": ("Seguridad Informática", "SEG-001", 32, False,
            "Esp. Jiménez, Laura", "l.jimenez@frlp.utn.edu.ar"),
    "MC": ("Métodos Cuantitativos", "MC-001", 32, True,
           "Dr. Vega, Alejandro", "a.vega@frlp.utn.edu.ar"),
    "INN": ("Innovación y Tecnología", "INN-001", 24, True,
            "Mg. Ruiz, Patricia", "p.ruiz@frlp.utn.edu.ar"),
}  # fmt: skip

# Asistencia por clase dictada: "P" presente, "A" ausente (como la grilla).
# GPS es la grilla de la Planilla: Enzo, María y Tomás.
ASISTENCIAS = {
    "GPS": {"dash-i1": "PPAPPP", "dash-i2": "PPPPPP", "dash-i3": "AAPAPA"},
    "ARQ": {"dash-i1": "PPPPAPPP", "leg-2026-001": "PPPPPPPP", "leg-2026-009": "PPAPPPPP"},
    "SEG": {"dash-i1": "PPAPP", "leg-2026-001": "PPPPP", "leg-2026-009": "PPPAP"},
    "MC": {
        "dash-i1": "PPAPPAPPAPPPAPPAPP",
        "leg-2026-001": "PPPPPPAPPPPPPPAPPP",
        "leg-2026-009": "PPAPPPPPAPPPPAPPPP",
    },
}

# Notas finales ya cargadas: (seminario, persona): (nota, fecha del acta).
NOTAS = {
    ("GPS", "dash-i2"): (Decimal("9"), None),
    ("ARQ", "dash-i1"): (Decimal("9"), date(2026, 4, 20)),
    ("ARQ", "leg-2026-001"): (Decimal("8"), date(2026, 4, 20)),
    ("ARQ", "leg-2026-009"): (Decimal("7"), date(2026, 4, 20)),
    ("SEG", "dash-i1"): (Decimal("7"), date(2026, 5, 10)),
    ("SEG", "leg-2026-001"): (Decimal("9"), date(2026, 5, 10)),
    ("SEG", "leg-2026-009"): (Decimal("6"), date(2026, 5, 10)),
}


def _fechas_de_clase(clave: str, hoy: date) -> list[date]:
    """Las fechas de cursada: GPS tiene 6 dictadas y una futura (+7 días)."""
    if clave == "GPS":
        return [hoy - timedelta(weeks=semanas) for semanas in (6, 5, 4, 3, 2, 1)] + [
            hoy + timedelta(weeks=1)
        ]
    if clave == "ARQ":
        return [date(2026, 3, 2) + timedelta(weeks=semana) for semana in range(8)]
    if clave == "SEG":
        return [date(2026, 4, 6) + timedelta(weeks=semana) for semana in range(5)]
    if clave == "MC":
        return [hoy - timedelta(weeks=semanas) for semanas in range(18, 0, -1)]
    return []  # INN todavía no empezó


def _fecha_limite_actas(clave: str, hoy: date) -> date:
    return {
        "GPS": hoy + timedelta(days=40),
        "ARQ": date(2026, 5, 15),
        "SEG": date(2026, 6, 5),
        "MC": hoy + timedelta(days=15),  # vencimiento próximo: el aviso del Legajo
        "INN": hoy + timedelta(days=75),
    }[clave]


# ── PDFs de prueba ─────────────────────────────────────────────────────────


def _pdf_de_prueba(titulo: str, detalle: str) -> bytes:
    """Un PDF válido de una página con dos líneas de texto (sin dependencias)."""

    def literal(texto: str) -> bytes:
        crudo = texto.encode("cp1252", "replace")
        return (
            b"(" + crudo.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)") + b")"
        )

    contenido = (
        b"BT /F1 16 Tf 72 760 Td " + literal(titulo) + b" Tj "
        b"0 -24 Td /F1 11 Tf " + literal(detalle) + b" Tj "
        b"0 -18 Td " + literal("Documento de prueba generado por el seed.") + b" Tj ET"
    )
    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Length "
        + str(len(contenido)).encode()
        + b" >>\nstream\n"
        + contenido
        + b"\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    posiciones = []
    for numero, cuerpo in enumerate(objetos, start=1):
        posiciones.append(len(pdf))
        pdf += f"{numero} 0 obj\n".encode() + cuerpo + b"\nendobj\n"
    inicio_xref = len(pdf)
    pdf += f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode()
    for posicion in posiciones:
        pdf += f"{posicion:010d} 00000 n \n".encode()
    pdf += (
        f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{inicio_xref}\n%%EOF\n"
    ).encode()
    return bytes(pdf)


def _asegurar_pdf(path_storage: str, contenido: bytes) -> bool:
    """Escribe el PDF si no está en disco. Devuelve True si lo escribió."""
    ruta = ruta_del_pdf(path_storage)
    if ruta.exists():
        return False
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(contenido)
    return True


# ── Link demo del docente ──────────────────────────────────────────────────

ID_ACCESO_DEMO = _id("acceso", "GPS", ANIO_ACTUAL)
ID_LEGAJO_BORRADOR = _id("legajo", "leg-2026-006")


def token_acceso_demo() -> str:
    """El token del link demo. Sale de SECRET_KEY: es el mismo en cada corrida,
    así el seed lo puede imprimir aunque en la base solo esté su hash."""
    firma = hmac.new(
        config.SECRET_KEY.encode(), b"seed:acceso-docente:GPS-2026", hashlib.sha256
    ).digest()
    return base64.urlsafe_b64encode(firma).rstrip(b"=").decode()


# ── Armado de las filas ────────────────────────────────────────────────────


def _momento(dia: date | None) -> datetime | None:
    """Un día como timestamp UTC (al mediodía)."""
    return datetime.combine(dia, time(12, 0), tzinfo=UTC) if dia else None


def _requeridos(persona: Persona) -> list[TipoDocumento]:
    """Los 5 obligatorios, más el título de posgrado y el formulario de beca si aplican."""
    tipos = list(DOCUMENTOS_OBLIGATORIOS)
    if persona.titulo_posgrado:
        tipos.append(TipoDocumento.TITULO_POSGRADO)
    if persona.beca:
        tipos.append(TipoDocumento.FORM_BECA)
    return tipos


# El camino de cada estado por la tabla de transiciones de RF-CORE-003.
_CAMINOS = {
    E.BORRADOR: (),
    E.PENDIENTE: (AccionLegajo.ENVIAR,),
    E.EN_REVISION: (AccionLegajo.ENVIAR, AccionLegajo.REVISAR),
    E.OBSERVADO: (AccionLegajo.ENVIAR, AccionLegajo.REVISAR, AccionLegajo.OBSERVAR),
    E.COMPLETADO: (AccionLegajo.ENVIAR, AccionLegajo.REVISAR, AccionLegajo.APROBAR),
    E.ACTIVO: (
        AccionLegajo.ENVIAR,
        AccionLegajo.REVISAR,
        AccionLegajo.APROBAR,
        AccionLegajo.MATRICULAR,
    ),
    E.VENCIDO: (
        AccionLegajo.ENVIAR,
        AccionLegajo.REVISAR,
        AccionLegajo.APROBAR,
        AccionLegajo.VENCER,
    ),
    E.RECHAZADO: (AccionLegajo.ENVIAR, AccionLegajo.REVISAR, AccionLegajo.RECHAZAR),
}
_TRANSICIONES = {
    AccionLegajo.ENVIAR: (E.BORRADOR, E.PENDIENTE),
    AccionLegajo.REVISAR: (E.PENDIENTE, E.EN_REVISION),
    AccionLegajo.OBSERVAR: (E.EN_REVISION, E.OBSERVADO),
    AccionLegajo.APROBAR: (E.EN_REVISION, E.COMPLETADO),
    AccionLegajo.RECHAZAR: (E.EN_REVISION, E.RECHAZADO),
    AccionLegajo.MATRICULAR: (E.COMPLETADO, E.ACTIVO),
    AccionLegajo.VENCER: (E.COMPLETADO, E.VENCIDO),
}


def _cuando(persona: Persona, accion: AccionLegajo, orden: int) -> date:
    """El día de cada transición: las fechas conocidas, o unos días después del envío."""
    assert persona.fecha_envio is not None
    if accion is AccionLegajo.APROBAR and persona.fecha_completado:
        return persona.fecha_completado
    if accion is AccionLegajo.MATRICULAR and persona.fecha_activacion:
        return persona.fecha_activacion
    if accion is AccionLegajo.VENCER and persona.fecha_completado:
        return persona.fecha_completado + timedelta(days=30)  # BR-005
    return persona.fecha_envio + timedelta(days=orden * 2)


def _quien(persona: Persona, accion: AccionLegajo) -> str | None:
    """Quién hizo la transición: el aspirante envía, el sistema vence, el resto el coordinador."""
    if accion is AccionLegajo.ENVIAR:
        return persona.email
    if accion is AccionLegajo.VENCER:
        return None
    return EMAIL_COORDINADOR


def _auditoria(persona: Persona, legajo_id: uuid.UUID) -> list[AuditoriaLegajo]:
    """Una fila por cada transición que llevó al legajo a su estado actual."""
    if persona.fecha_envio is None:
        return []
    filas = []
    for orden, accion in enumerate(_CAMINOS[persona.estado]):
        anterior, nuevo = _TRANSICIONES[accion]
        con_comentario = accion in (AccionLegajo.OBSERVAR, AccionLegajo.RECHAZAR)
        filas.append(
            AuditoriaLegajo(
                id=_id("auditoria", persona.clave, accion),
                legajo_id=legajo_id,
                accion=accion,
                estado_anterior=anterior,
                estado_nuevo=nuevo,
                comentario=persona.comentario if con_comentario else None,
                usuario_email=_quien(persona, accion),
                created_at=_momento(_cuando(persona, accion, orden)),
            )
        )
    return filas


def _trabajo_final(
    persona: Persona, legajo_id: uuid.UUID, anio: int, indice: int
) -> TrabajoFinal | None:
    """Aprobado si se graduó; en elaboración en la mitad de los activos; si no, ninguno."""
    aprobado = persona.estado is E.GRADUADO
    en_elaboracion = persona.estado is E.ACTIVO and int(persona.dni) % 2 == 0
    if not (aprobado or en_elaboracion):
        return None
    es_el_de_enzo = persona.clave == "dash-i1"  # el TFI del mock del Legajo
    anio_aprobacion = min(anio + 2, ANIO_ACTUAL)
    return TrabajoFinal(
        id=_id("trabajo-final", persona.clave),
        legajo_id=legajo_id,
        tipo=TipoTrabajoFinal.TESIS if persona.carrera == "DOC" else TipoTrabajoFinal.TFI,
        titulo="Sistema de gestión académica para posgrado"
        if es_el_de_enzo
        else TITULOS_TFI[indice % len(TITULOS_TFI)],
        director="Dr. Pérez, Juan" if es_el_de_enzo else DIRECTORES[indice % len(DIRECTORES)],
        fecha_aprobacion_cpr=date(anio_aprobacion, 6, 1 + indice % 25) if aprobado else None,
        numero_resolucion=f"Res. CPR {100 + indice}/{anio_aprobacion}" if aprobado else None,
    )


@dataclass
class _Filas:
    """Todo lo que el seed quiere que exista, en orden de claves foráneas."""

    legajos: list[Legajo]
    documentos: list[tuple[Documento, bytes]]
    auditoria: list[AuditoriaLegajo]
    seminarios: list[Seminario]
    cursadas: list[Cursada]
    clases: list[Clase]
    asistencias: list[Asistencia]
    trabajos_finales: list[TrabajoFinal]
    tutorias: list[Tutoria]


def _armar_filas(hoy: date) -> _Filas:
    filas = _Filas([], [], [], [], [], [], [], [], [])
    carrera_id = {clave: _id("carrera", clave) for clave in CARRERAS}
    legajo_id: dict[str, uuid.UUID] = {}

    for anio, (cohorte_id, _inicio) in sorted(COHORTES.items()):
        personas = _personas_2026(hoy) if anio == ANIO_ACTUAL else _personas_historicas(anio)
        seguimiento = legajo_numero = 0
        for persona in personas:
            legajo_id[persona.clave] = id_legajo = _id("legajo", persona.clave)
            numero_seguimiento = numero_legajo = None
            if persona.estado is not E.BORRADOR:
                seguimiento += 1
                numero_seguimiento = f"SEG-{anio}-{seguimiento:05d}"
            if persona.estado in ESTADOS_APROBADOS:
                legajo_numero += 1
                numero_legajo = f"{anio % 100:02d}-001-{legajo_numero:03d}"

            filas.legajos.append(
                Legajo(
                    id=id_legajo,
                    cohorte_id=cohorte_id,
                    carrera_id=carrera_id[persona.carrera],
                    carrera_secundaria_id=carrera_id.get(persona.carrera_secundaria or ""),
                    estado=persona.estado,
                    numero_seguimiento=numero_seguimiento,
                    numero_legajo=numero_legajo,
                    apellido=persona.apellido,
                    nombre=persona.nombre,
                    nacionalidad="Argentina",
                    dni=persona.dni,
                    telefono_movil=persona.telefono_movil,
                    email=persona.email,
                    domicilio=persona.domicilio,
                    ciudad=persona.ciudad,
                    provincia=persona.provincia,
                    pais="Argentina",
                    titulo_grado=persona.titulo_grado,
                    titulo_posgrado=persona.titulo_posgrado,
                    como_conocio=persona.como_conocio,
                    motivacion=persona.motivacion,
                    solicita_beca=persona.beca is not None,
                    tipo_beca=persona.beca,
                    semaforo=persona.semaforo,
                    semaforo_manual=persona.semaforo_manual,
                    fecha_inscripcion=_momento(persona.fecha_envio),
                    fecha_completado=_momento(persona.fecha_completado),
                    fecha_activacion=_momento(persona.fecha_activacion),
                )
            )

            for tipo in _requeridos(persona):
                if tipo in persona.faltantes:
                    continue
                id_documento = _id("documento", persona.clave, tipo)
                contenido = _pdf_de_prueba(
                    ETIQUETA_DOCUMENTO[tipo],
                    f"{persona.apellido}, {persona.nombre} — DNI {persona.dni}",
                )
                documento = Documento(
                    id=id_documento,
                    legajo_id=id_legajo,
                    tipo=tipo,
                    nombre_original=f"{tipo.value.lower()}_{_slug(persona.apellido)}.pdf",
                    path_storage=f"uploads/{cohorte_id}/{id_legajo}/{id_documento}.pdf",
                    checksum_sha256=hashlib.sha256(contenido).hexdigest(),
                    tamanio_bytes=len(contenido),
                    fecha_subida=_momento(persona.fecha_envio) or datetime.now(UTC),
                )
                filas.documentos.append((documento, contenido))

            if anio == ANIO_ACTUAL:
                filas.auditoria.extend(_auditoria(persona, id_legajo))

            trabajo_final = _trabajo_final(persona, id_legajo, anio, len(filas.trabajos_finales))
            if trabajo_final is not None:
                filas.trabajos_finales.append(trabajo_final)

    # Seminarios de 2026, con sus clases, cursadas, asistencias y notas.
    cohorte_actual = COHORTES[ANIO_ACTUAL][0]
    for clave, (nombre, codigo, horas, obligatorio, docente, email) in SEMINARIOS.items():
        id_seminario = _id("seminario", clave, ANIO_ACTUAL)
        filas.seminarios.append(
            Seminario(
                id=id_seminario,
                cohorte_id=cohorte_actual,
                carrera_id=carrera_id["ESP"],
                nombre=nombre,
                codigo=codigo,
                horas_catedra=horas,
                es_obligatorio=obligatorio,
                docente_nombre=docente,
                docente_email=email,
                fecha_limite_actas=_fecha_limite_actas(clave, hoy),
            )
        )
        # La clave es el NÚMERO de clase, no la fecha: las fechas son relativas a
        # hoy y, si fueran parte del id, cada día se insertarían clases nuevas.
        clases = [
            Clase(
                id=_id("clase", clave, ANIO_ACTUAL, orden), seminario_id=id_seminario, fecha=fecha
            )
            for orden, fecha in enumerate(_fechas_de_clase(clave, hoy))
        ]
        filas.clases.extend(clases)

        for clave_persona, grilla in ASISTENCIAS.get(clave, {}).items():
            nota, fecha_acta = NOTAS.get((clave, clave_persona), (None, None))
            id_cursada = _id("cursada", clave, clave_persona)
            filas.cursadas.append(
                Cursada(
                    id=id_cursada,
                    legajo_id=legajo_id[clave_persona],
                    seminario_id=id_seminario,
                    nota=nota,
                    condicion=CondicionCursada.APROBADO if nota is not None else None,
                    fecha_acta=fecha_acta,
                )
            )
            for orden, clase in enumerate(clases):
                # Las clases futuras arrancan en Ausente, como al crearlas (RF-DOC-002).
                presente = orden < len(grilla) and grilla[orden] == "P"
                filas.asistencias.append(
                    Asistencia(
                        id=_id("asistencia", clase.id, id_cursada),
                        clase_id=clase.id,
                        cursada_id=id_cursada,
                        presente=presente,
                    )
                )

    # Las tutorías del mock del Legajo (las de Enzo).
    for fecha, titulo, detalle in (
        (
            date(2026, 4, 15),
            "Tutoría inicial",
            "Se definió enfoque del TFI. Próxima entrega: borrador cap. 1.",
        ),
        (
            date(2026, 5, 10),
            "Revisión capítulo 1",
            "Observaciones menores. Se aprueba avance hacia cap. 2.",
        ),
    ):
        filas.tutorias.append(
            Tutoria(
                id=_id("tutoria", "dash-i1", fecha),
                legajo_id=legajo_id["dash-i1"],
                fecha=fecha,
                titulo=titulo,
                detalle=detalle,
            )
        )
    return filas


# ── Inserción idempotente ──────────────────────────────────────────────────


def _insertar_faltantes(session: Session, filas: list[SQLModel]) -> int:
    """Inserta las filas cuyo id todavía no está en la base. Devuelve cuántas."""
    if not filas:
        return 0
    modelo = type(filas[0])
    existentes = set(session.exec(select(modelo.id)).all())
    nuevas = [fila for fila in filas if fila.id not in existentes]
    session.add_all(nuevas)
    session.flush()
    return len(nuevas)


def sembrar(session: Session, hoy: date | None = None) -> dict[str, int]:
    """Inserta lo que falte del dataset demo. Devuelve cuántas filas agregó por tabla."""
    hoy = hoy or date.today()
    resumen: dict[str, int] = {}

    existentes = set(session.exec(select(Usuario.email)).all())
    resumen["usuarios"] = _insertar_faltantes(
        session,
        [
            Usuario(
                id=_id("usuario", email),
                email=email,
                nombre=nombre,
                password_hash=hash_password(clave),  # bcrypt solo para los que faltan
                rol=rol,
            )
            for email, nombre, rol, clave in USUARIOS
            if email not in existentes
        ],
    )
    resumen["carreras"] = _insertar_faltantes(
        session,
        [
            Carrera(id=_id("carrera", clave), nombre=nombre, nombre_corto=corto, tipo=tipo)
            for clave, (nombre, corto, tipo) in CARRERAS.items()
        ],
    )
    resumen["cohortes"] = _insertar_faltantes(
        session,
        [
            Cohorte(
                id=cohorte_id,
                anio=anio,
                nombre=f"Cohorte {anio}",
                inscripcion_abierta=anio == ANIO_ACTUAL,
                fecha_inicio=inicio,
            )
            for anio, (cohorte_id, inicio) in COHORTES.items()
        ],
    )

    filas = _armar_filas(hoy)
    resumen["legajos"] = _insertar_faltantes(session, filas.legajos)
    resumen["documentos"] = _insertar_faltantes(session, [doc for doc, _ in filas.documentos])
    resumen["pdfs_en_disco"] = sum(
        _asegurar_pdf(doc.path_storage, contenido) for doc, contenido in filas.documentos
    )
    resumen["auditoria_legajos"] = _insertar_faltantes(session, filas.auditoria)
    resumen["seminarios"] = _insertar_faltantes(session, filas.seminarios)
    resumen["cursadas"] = _insertar_faltantes(session, filas.cursadas)
    resumen["clases"] = _insertar_faltantes(session, filas.clases)
    resumen["asistencias"] = _insertar_faltantes(session, filas.asistencias)
    resumen["trabajos_finales"] = _insertar_faltantes(session, filas.trabajos_finales)
    resumen["tutorias"] = _insertar_faltantes(session, filas.tutorias)
    resumen["accesos_docente"] = _asegurar_acceso_demo(session)

    session.commit()
    return resumen


def _asegurar_acceso_demo(session: Session) -> int:
    """El link del docente de GPS 2026: lo crea, o lo renueva si venció."""
    token_hash = hash_token_opaco(token_acceso_demo())
    acceso = session.get(AccesoDocente, ID_ACCESO_DEMO)
    vigente = (
        acceso is not None
        and acceso.token_hash == token_hash
        and acceso.expira_en > datetime.now(UTC)
    )
    if vigente:
        return 0
    acceso = acceso or AccesoDocente(
        id=ID_ACCESO_DEMO,
        seminario_id=_id("seminario", "GPS", ANIO_ACTUAL),
        token_hash=token_hash,
        expira_en=datetime.now(UTC),
        creado_por=EMAIL_COORDINADOR,
    )
    acceso.token_hash = token_hash
    acceso.expira_en = datetime.now(UTC) + timedelta(days=30)
    session.add(acceso)
    session.flush()
    return 1


def main() -> None:
    """Siembra la base de desarrollo e imprime cómo entrar."""
    with Session(engine) as session:
        resumen = sembrar(session)
        acceso = session.get(AccesoDocente, ID_ACCESO_DEMO)
        vence = acceso.expira_en.astimezone().strftime("%d/%m/%Y") if acceso else "?"

    agregadas = {tabla: cantidad for tabla, cantidad in resumen.items() if cantidad}
    print("Seed del Sistema de Posgrado")
    if agregadas:
        for tabla, cantidad in agregadas.items():
            print(f"  + {cantidad:>4} {tabla}")
    else:
        print("  La base ya tenía todos los datos demo: no se agregó nada.")

    print("\nUsuarios demo:")
    for email, nombre, rol, clave in USUARIOS:
        print(f"  {email:<20} {clave:<14} {rol.value} ({nombre})")
    print(f"\nLink del docente de Gestión de Proyectos de Software (vence el {vence}):")
    print(f"  {config.FRONTEND_URL}/?acceso={token_acceso_demo()}")
    print(
        f"\nLink de seguimiento del aspirante (borrador de Sánchez, vale {config.ASPIRANTE_TOKEN_EXPIRE_DAYS} días):"
    )
    print(f"  {config.FRONTEND_URL}/?seguimiento={crear_token_aspirante(ID_LEGAJO_BORRADOR)}")


if __name__ == "__main__":
    main()
