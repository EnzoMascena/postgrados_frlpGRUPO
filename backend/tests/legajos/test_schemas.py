"""Schemas de legajos: el JSON que reciben Loli (coordinador) y Fran (aspirante), plan §10."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from src.legajos.application.obtener_detalle import obtener_detalle
from src.legajos.domain.entidades import RegistroAuditoria
from src.legajos.domain.estados import Accion, EstadoLegajo
from src.legajos.infrastructure.pg_repository import PgLegajoRepository
from src.legajos.presentation.schemas import (
    LARGO_MAXIMO_COMENTARIO,
    CambiarEstadoRequest,
    LegajoDetalleAspiranteResponse,
    LegajoDetalleCoordinadorResponse,
)
from src.shared.roles import Rol
from tests.fabricas import crear_carrera, crear_cohorte, crear_legajo

AHORA = datetime(2026, 11, 3, 14, 20, tzinfo=UTC)

CLAVES_BASE = {
    "id",
    "codigoSeguimiento",
    "numeroLegajo",
    "estado",
    "cohorte",
    "carreras",
    "apellido",
    "nombre",
    "nacionalidad",
    "dni",
    "telefonoMovil",
    "telefonoFijo",
    "email",
    "emailAlternativo",
    "domicilio",
    "ciudad",
    "provincia",
    "pais",
    "tituloGrado",
    "tituloPosgrado",
    "comoConocio",
    "motivacion",
    "solicitaBeca",
    "tipoBeca",
    "fechaInscripcion",
    "fechaAprobacion",
    "fechaActivacion",
    "createdAt",
    "documentos",
    "documentosFaltantes",
    "ultimaObservacion",
}


@pytest.fixture
def legajo_id(session):
    cohorte = crear_cohorte(session, nombre="Cohorte 2026")
    carrera = crear_carrera(session, nombre="Maestría en Tecnología Informática")
    legajo = crear_legajo(
        session, cohorte, [carrera], estado=EstadoLegajo.EN_REVISION, fecha_inscripcion=AHORA
    )
    repo = PgLegajoRepository(session)
    repo.guardar_cambio(
        repo.obtener(legajo.id),
        RegistroAuditoria(
            legajo_id=legajo.id,
            accion=Accion.REVISAR,
            estado_anterior=EstadoLegajo.PENDIENTE,
            estado_nuevo=EstadoLegajo.EN_REVISION,
            comentario=None,
            rol=Rol.COORDINADOR,
            usuario_email="coordinador@example.com",
            fecha=AHORA,
        ),
    )
    return legajo.id


def _json(schema, session, legajo_id, vista):
    detalle = obtener_detalle(legajo_id, PgLegajoRepository(session), vista)
    return schema.model_validate(detalle).model_dump(mode="json", by_alias=True)


def test_la_vista_coordinador_tiene_las_claves_del_plan_en_camel_case(session, legajo_id):
    cuerpo = _json(LegajoDetalleCoordinadorResponse, session, legajo_id, "coordinador")

    assert set(cuerpo) == CLAVES_BASE | {"historial", "accionesPermitidas"}
    assert cuerpo["accionesPermitidas"] == ["OBSERVAR", "APROBAR", "RECHAZAR"]
    assert cuerpo["historial"] == [
        {
            "fecha": "2026-11-03T14:20:00Z",
            "accion": "REVISAR",
            "estadoAnterior": "PENDIENTE",
            "estadoNuevo": "EN_REVISION",
            "comentario": None,
            "rol": "COORDINADOR",
            "usuarioEmail": "coordinador@example.com",
        }
    ]
    assert set(cuerpo["documentos"][0]) == {
        "tipo",
        "nombre",
        "obligatorio",
        "cargado",
        "documentoId",
        "nombreOriginal",
        "tamanioBytes",
        "fechaSubida",
    }
    assert set(cuerpo["cohorte"]) == {"id", "nombre", "anio"}
    assert set(cuerpo["carreras"][0]) == {"id", "nombre", "tipo"}
    assert cuerpo["fechaInscripcion"] == "2026-11-03T14:20:00Z"


def test_la_vista_aspirante_trae_puede_editar_y_no_el_historial(session, legajo_id):
    cuerpo = _json(LegajoDetalleAspiranteResponse, session, legajo_id, "aspirante")

    assert set(cuerpo) == CLAVES_BASE | {"puedeEditar"}
    assert cuerpo["puedeEditar"] is False


def test_cambiar_estado_acepta_la_accion_y_el_comentario_en_camel_case():
    datos = CambiarEstadoRequest.model_validate(
        {"accion": "OBSERVAR", "comentario": "Falta la copia del título de grado legalizada"}
    )

    assert datos.accion == Accion.OBSERVAR
    assert datos.comentario == "Falta la copia del título de grado legalizada"


def test_cambiar_estado_sin_comentario_lo_deja_nulo():
    assert CambiarEstadoRequest.model_validate({"accion": "APROBAR"}).comentario is None


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"accion": "APROBARR"},
        {},
        {"accion": "OBSERVAR", "comentario": "a" * (LARGO_MAXIMO_COMENTARIO + 1)},
    ],
    ids=["accion-inexistente", "sin-accion", "comentario-largo"],
)
def test_cambiar_estado_rechaza_un_cuerpo_invalido(cuerpo):
    with pytest.raises(ValidationError):
        CambiarEstadoRequest.model_validate(cuerpo)
