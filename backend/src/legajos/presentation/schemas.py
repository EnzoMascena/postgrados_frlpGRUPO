"""Schemas de legajos (plan §10): JSON en camelCase, atributos en snake_case.

Las respuestas del detalle se arman directo desde el `LegajoDetalle` de `obtener_detalle`:
`LegajoDetalleCoordinadorResponse.model_validate(detalle)`. Fran usa la del aspirante en
`GET /seguimiento/{token}`.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import ConfigDict, Field

from src.cohortes.domain.tipos import TipoCarrera
from src.gestion_documental.domain.tipos import TipoDocumento
from src.inscripcion.domain.tipos import ComoConocio, TipoBeca
from src.legajos.domain.estados import Accion, EstadoLegajo
from src.shared.roles import Rol
from src.shared.schemas import CamelModel

LARGO_MAXIMO_COMENTARIO = 2000

_EJEMPLO_BASE: dict[str, Any] = {
    "id": "4b0e6f1a-2c3d-4e5f-8a9b-0c1d2e3f4a5b",
    "codigoSeguimiento": "7F3A9C21",
    "numeroLegajo": None,
    "estado": "EN_REVISION",
    "cohorte": {
        "id": "c1a2b3c4-d5e6-4f70-8192-a3b4c5d6e7f8",
        "nombre": "Cohorte 2026",
        "anio": 2026,
    },
    "carreras": [
        {
            "id": "5d2f8e1a-9b3c-4d5e-8f6a-7b8c9d0e1f2a",
            "nombre": "Maestría en Tecnología Informática",
            "tipo": "Maestria",
        }
    ],
    "apellido": "Rodríguez",
    "nombre": "Ana Laura",
    "nacionalidad": "Argentina",
    "dni": "28456789",
    "telefonoMovil": "+54 221 4567890",
    "telefonoFijo": None,
    "email": "ana.rodriguez@example.com",
    "emailAlternativo": "ana.trabajo@example.com",
    "domicilio": "Av. 7 Nro. 1234",
    "ciudad": "La Plata",
    "provincia": "Buenos Aires",
    "pais": "Argentina",
    "tituloGrado": "Ingeniería en Sistemas de Información",
    "tituloPosgrado": None,
    "comoConocio": "EGRESADOS",
    "motivacion": "Quiero profundizar en gestión de sistemas para aplicarlo en mi trabajo.",
    "solicitaBeca": True,
    "tipoBeca": "30",
    "fechaInscripcion": "2026-11-03T14:20:00Z",
    "fechaAprobacion": None,
    "fechaActivacion": None,
    "createdAt": "2026-11-03T13:58:00Z",
    "documentos": [
        {
            "tipo": "DNI",
            "nombre": "Copia del DNI o pasaporte",
            "obligatorio": True,
            "cargado": True,
            "documentoId": "9f1c2d3e-4f5a-4b6c-8d7e-9f0a1b2c3d4e",
            "nombreOriginal": "dni.pdf",
            "tamanioBytes": 183412,
            "fechaSubida": "2026-11-03T14:01:00Z",
        },
        {
            "tipo": "TITULO_GRADO",
            "nombre": "Copia del título de grado",
            "obligatorio": True,
            "cargado": False,
            "documentoId": None,
            "nombreOriginal": None,
            "tamanioBytes": None,
            "fechaSubida": None,
        },
    ],
    "documentosFaltantes": ["TITULO_GRADO"],
    "ultimaObservacion": None,
}


class CohorteResponse(CamelModel):
    id: UUID
    nombre: str
    anio: int


class CarreraResponse(CamelModel):
    id: UUID
    nombre: str
    tipo: TipoCarrera


class DocumentoChecklistResponse(CamelModel):
    """Una fila del checklist. Los datos del archivo son nulos si todavía no lo subió."""

    tipo: TipoDocumento
    nombre: str
    obligatorio: bool
    cargado: bool
    documento_id: UUID | None
    nombre_original: str | None
    tamanio_bytes: int | None
    fecha_subida: datetime | None


class RegistroHistorialResponse(CamelModel):
    """Una fila del historial: se arma desde `RegistroAuditoria` (su `fecha` es `created_at`)."""

    fecha: datetime
    accion: Accion
    estado_anterior: EstadoLegajo
    estado_nuevo: EstadoLegajo
    comentario: str | None
    rol: Rol
    usuario_email: str | None  # nulo si lo hizo el aspirante o el sistema


class LegajoDetalleBase(CamelModel):
    """Lo que ven el coordinador y el aspirante."""

    id: UUID
    codigo_seguimiento: str
    numero_legajo: str | None
    estado: EstadoLegajo
    cohorte: CohorteResponse
    carreras: list[CarreraResponse]
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
    fecha_inscripcion: datetime | None
    fecha_aprobacion: datetime | None
    fecha_activacion: datetime | None
    created_at: datetime
    documentos: list[DocumentoChecklistResponse]
    documentos_faltantes: list[TipoDocumento]
    ultima_observacion: str | None  # el comentario del último OBSERVAR


class LegajoDetalleCoordinadorResponse(LegajoDetalleBase):
    """`GET /legajos/{id}` y `PATCH /legajos/{id}/estado`."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    **_EJEMPLO_BASE,
                    "historial": [
                        {
                            "fecha": "2026-11-03T14:20:00Z",
                            "accion": "ENVIAR",
                            "estadoAnterior": "BORRADOR",
                            "estadoNuevo": "PENDIENTE",
                            "comentario": None,
                            "rol": "ASPIRANTE",
                            "usuarioEmail": None,
                        }
                    ],
                    "accionesPermitidas": ["OBSERVAR", "APROBAR", "RECHAZAR"],
                }
            ]
        }
    )

    historial: list[RegistroHistorialResponse]
    # Las que el front muestra como botones: las calcula el back con la tabla de transiciones.
    acciones_permitidas: list[Accion]


class LegajoDetalleAspiranteResponse(LegajoDetalleBase):
    """`GET /seguimiento/{token}` (Fran, F5): sin historial ni acciones del coordinador."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{**_EJEMPLO_BASE, "estado": "BORRADOR", "puedeEditar": True}]
        }
    )

    puede_editar: bool  # verdadero en BORRADOR y OBSERVADO


class CambiarEstadoRequest(CamelModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "accion": "OBSERVAR",
                    "comentario": "Falta la copia del título de grado legalizada",
                }
            ]
        }
    )

    accion: Accion
    # Obligatorio (5 caracteres o más) solo para OBSERVAR: eso lo valida el dominio, que da el
    # mismo 422 venga de donde venga. Acá solo un tope contra bodies enormes.
    comentario: str | None = Field(default=None, max_length=LARGO_MAXIMO_COMENTARIO)
