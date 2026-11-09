"""`GET /legajos/{id}` y `PATCH /legajos/{id}/estado` contra la app real y la base de test."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlmodel import select

from src.gestion_documental.domain.tipos import TipoDocumento
from src.gestion_documental.infrastructure.orm_models import DocumentoORM
from src.legajos.domain.estados import Accion, EstadoLegajo
from src.legajos.infrastructure.orm_models import AuditoriaLegajoORM, LegajoORM
from src.legajos.presentation.dependencies import get_servicio_estados
from src.shared.roles import Actor, Rol
from tests.fabricas import crear_carrera, crear_cohorte, crear_legajo, crear_usuario

CLAVES_DE_ERROR = {"statusCode", "error", "message", "field", "timestamp"}


def detalle_url(legajo_id) -> str:
    return f"/api/v1/legajos/{legajo_id}"


def estado_url(legajo_id) -> str:
    return f"/api/v1/legajos/{legajo_id}/estado"


@pytest.fixture
def cohorte(session):
    return crear_cohorte(session, anio=2026, numero=1, nombre="Cohorte 2026")


@pytest.fixture
def carrera(session):
    return crear_carrera(session, nombre="Maestría en Tecnología Informática")


@pytest.fixture
def pendiente(session, cohorte, carrera):
    return crear_legajo(
        session,
        cohorte,
        [carrera],
        estado=EstadoLegajo.PENDIENTE,
        nombre="Ana Laura",
        apellido="Rodríguez",
        email="ana@example.com",
        fecha_inscripcion=datetime(2026, 11, 3, 14, 20, tzinfo=UTC),
    )


def _subir_documento(session, legajo, tipo: TipoDocumento) -> DocumentoORM:
    fila = DocumentoORM(
        legajo_id=legajo.id,
        tipo=tipo.value,
        path_storage=f"uploads/{legajo.cohorte_id}/{legajo.id}/{uuid4()}.pdf",
        nombre_original=f"{tipo.value.lower()}.pdf",
        checksum_sha256="0" * 64,
        tamanio_bytes=183_412,
    )
    session.add(fila)
    session.commit()
    session.refresh(fila)
    return fila


def _auditoria(session, legajo_id) -> list[tuple[str, str, str, str, str | None]]:
    filas = session.exec(
        select(AuditoriaLegajoORM)
        .where(AuditoriaLegajoORM.legajo_id == legajo_id)
        .order_by(AuditoriaLegajoORM.created_at)
    ).all()
    return [(f.accion, f.estado_anterior, f.estado_nuevo, f.rol, f.usuario_email) for f in filas]


def cambiar(client, headers, legajo_id, accion: str, comentario: str | None = None):
    cuerpo = (
        {"accion": accion} if comentario is None else {"accion": accion, "comentario": comentario}
    )
    return client.patch(estado_url(legajo_id), json=cuerpo, headers=headers)


# --- El recorrido completo ---


def test_recorrido_del_coordinador_hasta_matricular(
    client, session, headers_coordinador, pendiente, bandeja
):
    # REVISAR: sin email.
    respuesta = cambiar(client, headers_coordinador, pendiente.id, "REVISAR")
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "EN_REVISION"
    assert respuesta.json()["accionesPermitidas"] == ["OBSERVAR", "APROBAR", "RECHAZAR"]
    assert bandeja == []

    # OBSERVAR: email al aspirante con el comentario.
    respuesta = cambiar(client, headers_coordinador, pendiente.id, "OBSERVAR", "Falta el DNI")
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "OBSERVADO"
    assert respuesta.json()["ultimaObservacion"] == "Falta el DNI"
    assert respuesta.json()["accionesPermitidas"] == []
    assert [(e.destinatario, e.plantilla) for e in bandeja] == [
        ("ana@example.com", "observacion.html")
    ]

    # CORREGIR lo hace el aspirante (Fran, con el mismo servicio): confirmación como corrección.
    get_servicio_estados(session).cambiar(pendiente.id, Accion.CORREGIR, Actor(Rol.ASPIRANTE))
    assert bandeja[-1].plantilla == "confirmacion_envio.html"
    assert bandeja[-1].contexto["es_correccion"] is True

    # REVISAR de nuevo y APROBAR: número 26-001-001 y email de aprobación.
    assert cambiar(client, headers_coordinador, pendiente.id, "REVISAR").status_code == 200
    respuesta = cambiar(client, headers_coordinador, pendiente.id, "APROBAR")
    cuerpo = respuesta.json()
    assert respuesta.status_code == 200
    assert cuerpo["estado"] == "COMPLETADO"
    assert cuerpo["numeroLegajo"] == "26-001-001"
    assert cuerpo["fechaAprobacion"] is not None
    assert cuerpo["accionesPermitidas"] == ["MATRICULAR"]
    assert bandeja[-1].plantilla == "aprobacion.html"
    assert bandeja[-1].contexto["numero_legajo"] == "26-001-001"

    # MATRICULAR: fecha de activación, sin email.
    emails_antes = len(bandeja)
    respuesta = cambiar(client, headers_coordinador, pendiente.id, "MATRICULAR")
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "ACTIVO"
    assert respuesta.json()["fechaActivacion"] is not None
    assert respuesta.json()["accionesPermitidas"] == ["DAR_DE_BAJA"]
    assert len(bandeja) == emails_antes

    # Una fila de auditoría por cambio, en orden, con quién lo hizo.
    coord = "coordinador@example.com"
    assert _auditoria(session, pendiente.id) == [
        ("REVISAR", "PENDIENTE", "EN_REVISION", "COORDINADOR", coord),
        ("OBSERVAR", "EN_REVISION", "OBSERVADO", "COORDINADOR", coord),
        ("CORREGIR", "OBSERVADO", "PENDIENTE", "ASPIRANTE", None),
        ("REVISAR", "PENDIENTE", "EN_REVISION", "COORDINADOR", coord),
        ("APROBAR", "EN_REVISION", "COMPLETADO", "COORDINADOR", coord),
        ("MATRICULAR", "COMPLETADO", "ACTIVO", "COORDINADOR", coord),
    ]
    # El historial del detalle muestra lo mismo.
    historial = client.get(detalle_url(pendiente.id), headers=headers_coordinador).json()[
        "historial"
    ]
    assert [fila["accion"] for fila in historial] == [
        "REVISAR",
        "OBSERVAR",
        "CORREGIR",
        "REVISAR",
        "APROBAR",
        "MATRICULAR",
    ]


def test_la_segunda_aprobacion_de_la_cohorte_toma_el_numero_siguiente(
    client, session, headers_coordinador, cohorte, carrera
):
    primero = crear_legajo(session, cohorte, [carrera], estado=EstadoLegajo.EN_REVISION)
    segundo = crear_legajo(session, cohorte, [carrera], estado=EstadoLegajo.EN_REVISION)

    uno = cambiar(client, headers_coordinador, primero.id, "APROBAR").json()["numeroLegajo"]
    dos = cambiar(client, headers_coordinador, segundo.id, "APROBAR").json()["numeroLegajo"]

    assert (uno, dos) == ("26-001-001", "26-001-002")


def test_rechazar_sin_comentario_manda_el_rechazo(
    client, headers_coordinador, session, cohorte, carrera, bandeja
):
    legajo = crear_legajo(
        session, cohorte, [carrera], estado=EstadoLegajo.EN_REVISION, email="ana@example.com"
    )

    respuesta = cambiar(client, headers_coordinador, legajo.id, "RECHAZAR")

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "RECHAZADO"
    assert [(e.destinatario, e.plantilla, e.contexto["comentario"]) for e in bandeja] == [
        ("ana@example.com", "rechazo.html", "")
    ]


# --- VENCER, como lo usa la tarea diaria de Enzo (E6) ---


def test_vencer_por_el_servicio_avisa_a_cada_coordinador_activo(
    client, session, coordinador, cohorte, carrera, bandeja
):
    crear_usuario(session, email="otro.coordinador@example.com", rol=Rol.COORDINADOR)
    crear_usuario(session, email="inactivo@example.com", rol=Rol.COORDINADOR, activo=False)
    crear_usuario(session, email="docente@example.com", rol=Rol.DOCENTE)
    legajo = crear_legajo(
        session,
        cohorte,
        [carrera],
        estado=EstadoLegajo.COMPLETADO,
        numero_legajo="26-001-010",
        fecha_aprobacion=datetime.now(UTC) - timedelta(days=31),
    )

    get_servicio_estados(session).cambiar(legajo.id, Accion.VENCER, Actor(Rol.SISTEMA))

    session.expire_all()
    assert session.get(LegajoORM, legajo.id).estado == "VENCIDO"
    assert _auditoria(session, legajo.id) == [("VENCER", "COMPLETADO", "VENCIDO", "SISTEMA", None)]
    assert sorted(e.destinatario for e in bandeja) == [
        "coordinador@example.com",
        "otro.coordinador@example.com",
    ]
    assert {e.plantilla for e in bandeja} == {"vencimiento_coordinador.html"}


# --- Errores del cambio de estado ---


def test_una_accion_que_no_corresponde_al_estado_da_409_y_no_cambia_nada(
    client, session, headers_coordinador, pendiente, bandeja
):
    respuesta = cambiar(client, headers_coordinador, pendiente.id, "APROBAR")

    assert respuesta.status_code == 409
    assert set(respuesta.json()) == CLAVES_DE_ERROR
    assert respuesta.json()["error"] == "TRANSICION_INVALIDA"
    assert respuesta.json()["message"] == "No se puede APROBAR un legajo en estado PENDIENTE"
    session.expire_all()
    assert session.get(LegajoORM, pendiente.id).estado == "PENDIENTE"
    assert _auditoria(session, pendiente.id) == []
    assert bandeja == []


@pytest.mark.parametrize("comentario", [None, "", "abc"])
def test_observar_sin_comentario_suficiente_da_422(
    client, session, headers_coordinador, cohorte, carrera, comentario
):
    legajo = crear_legajo(session, cohorte, [carrera], estado=EstadoLegajo.EN_REVISION)

    respuesta = cambiar(client, headers_coordinador, legajo.id, "OBSERVAR", comentario)

    assert respuesta.status_code == 422
    assert respuesta.json()["error"] == "VALIDATION_ERROR"
    assert respuesta.json()["field"] == "comentario"
    assert _auditoria(session, legajo.id) == []


@pytest.mark.parametrize("accion", ["ENVIAR", "CORREGIR", "VENCER", "GRADUAR"])
def test_las_acciones_que_no_son_del_coordinador_dan_403(
    client, headers_coordinador, pendiente, accion
):
    respuesta = cambiar(client, headers_coordinador, pendiente.id, accion)

    assert respuesta.status_code == 403
    assert respuesta.json()["error"] == "FORBIDDEN"


def test_una_accion_que_no_existe_da_422(client, headers_coordinador, pendiente):
    respuesta = cambiar(client, headers_coordinador, pendiente.id, "APROBARR")

    assert respuesta.status_code == 422
    assert set(respuesta.json()) == CLAVES_DE_ERROR


# --- Acceso: 401, 403 y 404 en los dos endpoints ---


@pytest.fixture(params=["detalle", "estado"])
def llamar(request, client):
    def _llamar(legajo_id, headers=None):
        if request.param == "detalle":
            return client.get(detalle_url(legajo_id), headers=headers or {})
        return client.patch(
            estado_url(legajo_id), json={"accion": "REVISAR"}, headers=headers or {}
        )

    return _llamar


def test_sin_token_da_401(llamar, pendiente):
    respuesta = llamar(pendiente.id)

    assert respuesta.status_code == 401
    assert set(respuesta.json()) == CLAVES_DE_ERROR


def test_con_un_docente_da_403(llamar, headers_docente, pendiente, session):
    respuesta = llamar(pendiente.id, headers_docente)

    assert respuesta.status_code == 403
    session.expire_all()
    assert session.get(LegajoORM, pendiente.id).estado == "PENDIENTE"


def test_un_legajo_inexistente_da_404(llamar, headers_coordinador):
    respuesta = llamar(uuid4(), headers_coordinador)

    assert respuesta.status_code == 404
    assert respuesta.json()["message"] == "No encontramos el legajo"


def test_un_id_que_no_es_uuid_da_422(llamar, headers_coordinador):
    assert llamar("no-es-un-uuid", headers_coordinador).status_code == 422


# --- El detalle ---


def test_el_detalle_trae_documentos_faltantes_historial_y_acciones(
    client, session, headers_coordinador, pendiente, cohorte, carrera
):
    dni = _subir_documento(session, pendiente, TipoDocumento.DNI)
    _subir_documento(session, pendiente, TipoDocumento.FORM_INSCRIPCION)
    cambiar(client, headers_coordinador, pendiente.id, "REVISAR")

    respuesta = client.get(detalle_url(pendiente.id), headers=headers_coordinador)

    cuerpo = respuesta.json()
    assert respuesta.status_code == 200
    assert cuerpo["id"] == str(pendiente.id)
    assert cuerpo["estado"] == "EN_REVISION"
    assert cuerpo["cohorte"] == {"id": str(cohorte.id), "nombre": "Cohorte 2026", "anio": 2026}
    assert cuerpo["carreras"] == [
        {"id": str(carrera.id), "nombre": "Maestría en Tecnología Informática", "tipo": "Maestria"}
    ]
    assert [d["tipo"] for d in cuerpo["documentos"]] == [
        "FORM_INSCRIPCION",
        "DNI",
        "TITULO_GRADO",
        "PARTIDA",
        "CUIT_CUIL",
    ]
    item_dni = cuerpo["documentos"][1]
    assert item_dni["cargado"] is True
    assert item_dni["obligatorio"] is True
    assert item_dni["documentoId"] == str(dni.id)
    assert item_dni["nombreOriginal"] == "dni.pdf"
    assert item_dni["tamanioBytes"] == 183_412
    assert cuerpo["documentos"][2]["cargado"] is False
    assert cuerpo["documentos"][2]["documentoId"] is None
    assert cuerpo["documentosFaltantes"] == ["TITULO_GRADO", "PARTIDA", "CUIT_CUIL"]
    assert [fila["accion"] for fila in cuerpo["historial"]] == ["REVISAR"]
    assert cuerpo["historial"][0]["usuarioEmail"] == "coordinador@example.com"
    assert cuerpo["accionesPermitidas"] == ["OBSERVAR", "APROBAR", "RECHAZAR"]
    assert cuerpo["ultimaObservacion"] is None
    assert "puedeEditar" not in cuerpo
    # La ruta en disco del PDF nunca sale en la API.
    assert "pathStorage" not in str(cuerpo) and "uploads/" not in str(cuerpo)


def test_los_endpoints_aparecen_en_swagger(client):
    rutas = client.get("/api/openapi.json").json()["paths"]

    assert "get" in rutas["/api/v1/legajos/{legajo_id}"]
    patch = rutas["/api/v1/legajos/{legajo_id}/estado"]["patch"]
    assert patch["tags"] == ["Legajos"]
    assert {"401", "403", "404", "409", "422"} <= set(patch["responses"])
