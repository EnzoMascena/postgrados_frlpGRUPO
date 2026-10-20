"""
Enums del dominio — Python puro, sin SQLModel ni FastAPI.

Viven acá, separados de las tablas, para que cualquier capa los pueda
importar sin arrastrar la base de datos: un reglas.py (funciones puras,
módulo 07) puede hacer `from app.models.enums import EstadoLegajo` y sus
tests siguen corriendo sin postgres.

En la base se guardan como VARCHAR con un CHECK (no como ENUM nativo de
PostgreSQL): sumar un valor es una migración chica, sin ALTER TYPE. Se
guarda el VALOR (por ejemplo "Especializacion"), igual que en
ARQUITECTURA §8.1.
"""

from enum import StrEnum


class Rol(StrEnum):
    """Los roles de quien hace un request (el "principal")."""

    COORDINADOR = "COORDINADOR"
    CPR = "CPR"
    DOCENTE = "DOCENTE"
    ASPIRANTE = "ASPIRANTE"


class RolUsuario(StrEnum):
    """Los roles que tienen usuario y contraseña (tabla usuarios).

    El docente entra con el link del coordinador y el aspirante con su
    token de seguimiento: ninguno de los dos tiene usuario.
    """

    COORDINADOR = "COORDINADOR"
    CPR = "CPR"


class TipoCarrera(StrEnum):
    """Tipo de carrera: define la duración y las reglas del semáforo (RF-GRAD-002)."""

    ESPECIALIZACION = "Especializacion"
    MAESTRIA = "Maestria"
    DOCTORADO = "Doctorado"


class EstadoLegajo(StrEnum):
    """Estados del workflow del legajo (RF-CORE-003)."""

    BORRADOR = "BORRADOR"
    PENDIENTE = "PENDIENTE"
    EN_REVISION = "EN_REVISION"
    OBSERVADO = "OBSERVADO"
    COMPLETADO = "COMPLETADO"
    ACTIVO = "ACTIVO"
    VENCIDO = "VENCIDO"
    RECHAZADO = "RECHAZADO"
    BAJA = "BAJA"
    GRADUADO = "GRADUADO"


class AccionLegajo(StrEnum):
    """Las transiciones de la tabla de RF-CORE-003 (validar_transicion)."""

    ENVIAR = "ENVIAR"
    REVISAR = "REVISAR"
    OBSERVAR = "OBSERVAR"
    CORREGIR = "CORREGIR"
    APROBAR = "APROBAR"
    RECHAZAR = "RECHAZAR"
    MATRICULAR = "MATRICULAR"
    VENCER = "VENCER"
    GRADUAR = "GRADUAR"
    DAR_DE_BAJA = "DAR_DE_BAJA"


class Semaforo(StrEnum):
    """Riesgo académico (RF-GRAD-002). El VERDE manual lo pone el coordinador (BR-008)."""

    VERDE = "VERDE"
    AMARILLO = "AMARILLO"
    ROJO = "ROJO"


class TipoBeca(StrEnum):
    """Porcentaje de beca solicitado (RF-CORE-001)."""

    BECA_30 = "30"
    BECA_100 = "100"


class TipoDocumento(StrEnum):
    """Los documentos del legajo (RF-CORE-002, ARQUITECTURA §8.1).

    Los 5 primeros son siempre obligatorios; el título de posgrado y el
    formulario de beca, solo cuando correspondan.
    """

    FORM_INSCRIPCION = "FORM_INSCRIPCION"
    DNI = "DNI"
    TITULO_GRADO = "TITULO_GRADO"
    PARTIDA = "PARTIDA"
    CUIT_CUIL = "CUIT_CUIL"
    TITULO_POSGRADO = "TITULO_POSGRADO"
    FORM_BECA = "FORM_BECA"


class ComoConocio(StrEnum):
    """Opciones de "¿Cómo conoció la oferta?", las mismas del formulario."""

    SITIO_WEB_UTN = "Sitio web UTN FRLP"
    OTROS_SITIOS_WEB = "Otros sitios web"
    EGRESADOS_UTN = "Egresados de la UTN FRLP"
    COLEGAS = "Comentarios de colegas"
    OTROS = "Otros"


class CondicionCursada(StrEnum):
    """Condición final de un estudiante en un seminario (BR-003)."""

    APROBADO = "APROBADO"
    DESAPROBADO = "DESAPROBADO"
    LIBRE = "LIBRE"
    REGULAR = "REGULAR"


class TipoTrabajoFinal(StrEnum):
    """Trabajo final integrador o tesis (RF-GRAD-001)."""

    TFI = "TFI"
    TESIS = "TESIS"
