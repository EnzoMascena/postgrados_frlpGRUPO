"""`PUT /seguimiento/{token}` y `POST /seguimiento/{token}/enviar` contra la app real y la base
de test. Los emails quedan en la fixture `bandeja`."""

from datetime import date

import pytest
from sqlmodel import select

from src.gestion_documental.domain.requisitos import DOCUMENTOS_OBLIGATORIOS
from src.gestion_documental.infrastructure.orm_models import DocumentoORM
from src.inscripcion.infrastructure.links import crear_link_seguimiento
from src.legajos.domain.estados import EstadoLegajo
from src.legajos.infrastructure.orm_models import (
    AuditoriaLegajoORM,
    LegajoCarreraORM,
    LegajoORM,
)
from tests.fabricas import crear_carrera, crear_cohorte, crear_legajo

API = "/api/v1/seguimiento"


@pytest.fixture
def cohorte(session):
    return crear_cohorte(session)


@pytest.fixture
def carrera(session):
    return crear_carrera(session)


@pytest.fixture
def legajo(session, cohorte, carrera):
    return crear_legajo(session, cohorte, [carrera], dni="28456789", email="ana@example.com")


@pytest.fixture
def token(session, legajo):
    return crear_link_seguimiento(session, legajo.id)


@pytest.fixture
def datos(carrera) -> dict:
    """El cuerpo del PUT: el mismo del formulario, sin cohorteId."""
    return {
        "carreraIds": [str(carrera.id)],
        "apellido": "Gómez",
        "nombre": "Ana Laura",
        "nacionalidad": "Argentina",
        "dni": "28.456.789",
        "telefonoMovil": "+54 221 4567890",
        "telefonoFijo": None,
        "email": "ana@example.com",
        "emailAlternativo": "ana.trabajo@example.com",
        "domicilio": "Calle 50 Nro. 742",
        "ciudad": "La Plata",
        "provincia": "Buenos Aires",
        "pais": "Argentina",
        "tituloGrado": "Ingeniería en Sistemas de Información",
        "tituloPosgrado": None,
        "comoConocio": "COLEGAS",
        "motivacion": "Quiero especializarme en gestión de proyectos de software en mi trabajo.",
        "solicitaBeca": False,
        "tipoBeca": None,
    }


def cargar_documentos(session, legajo, tipos=DOCUMENTOS_OBLIGATORIOS):
    for tipo in tipos:
        session.add(
            DocumentoORM(
                legajo_id=legajo.id,
                tipo=tipo.value,
                path_storage=f"uploads/x/{tipo.value}.pdf",
                nombre_original=f"{tipo.value}.pdf",
                checksum_sha256="0" * 64,
                tamanio_bytes=1,
            )
        )
    session.commit()


def auditoria(session, legajo) -> list[AuditoriaLegajoORM]:
    consulta = select(AuditoriaLegajoORM).where(AuditoriaLegajoORM.legajo_id == legajo.id)
    return list(session.exec(consulta))


# --- PUT /seguimiento/{token} ---


def test_editar_actualiza_los_datos_y_responde_el_detalle(client, session, token, datos, legajo):
    respuesta = client.put(f"{API}/{token}", json=datos)

    cuerpo = respuesta.json()
    assert respuesta.status_code == 200
    assert (cuerpo["apellido"], cuerpo["domicilio"]) == ("Gómez", "Calle 50 Nro. 742")
    assert cuerpo["puedeEditar"] is True
    session.refresh(legajo)
    assert (legajo.apellido, legajo.como_conocio, legajo.dni) == ("Gómez", "COLEGAS", "28456789")


def test_editar_reemplaza_las_carreras_en_el_orden_nuevo(
    client, session, token, datos, legajo, carrera
):
    otra = crear_carrera(session)

    client.put(f"{API}/{token}", json={**datos, "carreraIds": [str(otra.id), str(carrera.id)]})

    filas = session.exec(
        select(LegajoCarreraORM).where(LegajoCarreraORM.legajo_id == legajo.id)
    ).all()
    assert sorted((f.orden, f.carrera_id) for f in filas) == [(1, otra.id), (2, carrera.id)]


def test_la_cohorte_no_se_puede_cambiar(client, session, token, datos, legajo, cohorte):
    otra_cohorte = crear_cohorte(session, anio=2027)

    client.put(f"{API}/{token}", json={**datos, "cohorteId": str(otra_cohorte.id)})

    session.refresh(legajo)
    assert legajo.cohorte_id == cohorte.id


def test_el_dni_de_otro_legajo_de_la_cohorte_da_409(client, session, token, datos, cohorte):
    crear_legajo(session, cohorte, [crear_carrera(session)], dni="30111222")

    respuesta = client.put(f"{API}/{token}", json={**datos, "dni": "30111222"})

    assert respuesta.status_code == 409
    assert (respuesta.json()["error"], respuesta.json()["field"]) == ("CONFLICT", "dni")


def test_con_el_legajo_enviado_no_se_puede_editar(client, session, token, datos, legajo):
    legajo.estado = EstadoLegajo.PENDIENTE.value
    session.commit()

    respuesta = client.put(f"{API}/{token}", json=datos)

    assert respuesta.status_code == 409
    assert respuesta.json()["error"] == "LEGAJO_NO_EDITABLE"
    session.refresh(legajo)
    assert legajo.apellido == "Rodríguez"


def test_con_el_periodo_cerrado_no_se_puede_editar(client, session, token, datos, cohorte):
    cohorte.inscripcion_abierta = False
    cohorte.proxima_apertura = date(2027, 3, 1)
    session.commit()

    respuesta = client.put(f"{API}/{token}", json=datos)

    assert respuesta.status_code == 409
    assert respuesta.json()["error"] == "PERIODO_CERRADO"


def test_editar_aplica_las_mismas_validaciones_que_el_formulario(client, token, datos):
    respuesta = client.put(f"{API}/{token}", json={**datos, "dni": "123"})

    assert respuesta.status_code == 422
    assert respuesta.json()["field"] == "dni"


def test_editar_con_un_link_invalido_da_404(client, datos):
    assert client.put(f"{API}/token-inventado", json=datos).status_code == 404


# --- POST /seguimiento/{token}/enviar ---


def test_enviar_con_todo_cargado_pasa_a_pendiente(client, session, token, legajo, bandeja):
    cargar_documentos(session, legajo)

    respuesta = client.post(f"{API}/{token}/enviar")

    cuerpo = respuesta.json()
    assert respuesta.status_code == 200
    assert (cuerpo["estado"], cuerpo["puedeEditar"]) == ("PENDIENTE", False)
    assert cuerpo["fechaInscripcion"] is not None
    [registro] = auditoria(session, legajo)
    assert (registro.accion, registro.estado_anterior, registro.estado_nuevo) == (
        "ENVIAR",
        "BORRADOR",
        "PENDIENTE",
    )
    assert (registro.rol, registro.usuario_email) == ("ASPIRANTE", None)
    assert [email.plantilla for email in bandeja] == ["confirmacion_envio.html"]


def test_enviar_desde_observado_es_corregir(client, session, token, legajo, bandeja):
    legajo.estado = EstadoLegajo.OBSERVADO.value
    session.commit()
    cargar_documentos(session, legajo)

    respuesta = client.post(f"{API}/{token}/enviar")

    assert respuesta.json()["estado"] == "PENDIENTE"
    assert auditoria(session, legajo)[0].accion == "CORREGIR"
    assert bandeja[0].contexto["es_correccion"] is True


def test_si_falta_un_documento_da_422_y_no_cambia_nada(client, session, token, legajo, bandeja):
    cargar_documentos(session, legajo, tipos=DOCUMENTOS_OBLIGATORIOS[:-1])  # sin el CUIT/CUIL

    respuesta = client.post(f"{API}/{token}/enviar")

    assert respuesta.status_code == 422
    assert respuesta.json()["error"] == "DOCUMENTOS_FALTANTES"
    assert respuesta.json()["message"] == (
        "Faltan documentos obligatorios: Constancia de CUIT / CUIL"
    )
    session.refresh(legajo)
    assert legajo.estado == "BORRADOR"
    assert auditoria(session, legajo) == []
    assert bandeja == []


def test_enviar_un_legajo_ya_enviado_da_409(client, session, token, legajo):
    cargar_documentos(session, legajo)
    client.post(f"{API}/{token}/enviar")

    respuesta = client.post(f"{API}/{token}/enviar")

    assert respuesta.status_code == 409
    assert respuesta.json()["error"] == "TRANSICION_INVALIDA"


def test_enviar_con_un_link_invalido_da_404(client):
    assert client.post(f"{API}/token-inventado/enviar").status_code == 404


def test_el_legajo_enviado_aparece_en_el_detalle_sin_poder_editarse(client, session, token, legajo):
    cargar_documentos(session, legajo)
    client.post(f"{API}/{token}/enviar")

    cuerpo = client.get(f"{API}/{token}").json()

    assert (cuerpo["estado"], cuerpo["puedeEditar"], cuerpo["documentosFaltantes"]) == (
        "PENDIENTE",
        False,
        [],
    )
    assert session.get(LegajoORM, legajo.id).fecha_inscripcion is not None
