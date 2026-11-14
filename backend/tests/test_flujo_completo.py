"""El flujo completo del Core por la API (E8, hito 3 del plan).

Recorre lo mismo que la demo, con la app real, la base de test y la bandeja de emails: el
aspirante se inscribe, sube sus PDFs y envía; el coordinador revisa y observa; el aspirante
corrige; el coordinador aprueba (número de legajo y email) y matricula. Cada módulo tiene sus
propios tests; este prueba que funcionan juntos. Si un PR rompe lo que un módulo espera de otro
(inscripción, documentos, estados, emails, búsqueda), falla acá.
"""

from datetime import datetime, timedelta

import pytest

from src.legajos.infrastructure.job_vencimiento import correr_vencimiento
from tests.fabricas import crear_carrera, crear_cohorte

API = "/api/v1"
PDF = b"%PDF-1.7\n1 0 obj << >> endobj\n%%EOF"
# Los 5 obligatorios más el formulario de beca, porque Ana pide beca (no tiene título de posgrado).
DOCUMENTOS_DE_ANA = ["FORM_INSCRIPCION", "DNI", "TITULO_GRADO", "PARTIDA", "CUIT_CUIL", "FORM_BECA"]
EMAIL_DE_ANA = "ana.rodriguez@example.com"


@pytest.fixture
def cohorte(session):
    return crear_cohorte(session, anio=2026, numero=1, abierta=True)


@pytest.fixture
def carrera(session):
    return crear_carrera(session, nombre="Maestría en Ingeniería en Sistemas de Información")


def formulario(cohorte, carrera, **cambios) -> dict:
    """Lo que manda el formulario del front, con camelCase y los opcionales vacíos como ""."""
    datos = {
        "cohorteId": str(cohorte.id),
        "carreraIds": [str(carrera.id)],
        "apellido": "Rodríguez",
        "nombre": "Ana Laura",
        "nacionalidad": "Argentina",
        "dni": "28.456.789",
        "telefonoMovil": "+54 221 4567890",
        "telefonoFijo": "",
        "email": EMAIL_DE_ANA,
        "emailAlternativo": "ana.trabajo@example.com",
        "domicilio": "Av. 7 Nro. 1234",
        "ciudad": "La Plata",
        "provincia": "Buenos Aires",
        "pais": "Argentina",
        "tituloGrado": "Ingeniería en Sistemas de Información",
        "tituloPosgrado": "",
        "comoConocio": "EGRESADOS",
        "motivacion": (
            "Quiero profundizar en gestión de sistemas para aplicarlo en mi trabajo como analista."
        ),
        "solicitaBeca": True,
        "tipoBeca": "30",
    }
    return {**datos, **cambios}


def subir(client, token: str, tipo: str, contenido: bytes = PDF):
    return client.post(
        f"{API}/seguimiento/{token}/documentos",
        data={"tipo": tipo},
        files={"archivo": (f"{tipo.lower()}.pdf", contenido, "application/pdf")},
    )


def cambiar(client, headers, legajo_id: str, accion: str, comentario: str | None = None) -> dict:
    """Una acción del coordinador desde el detalle del legajo. Devuelve el detalle actualizado."""
    respuesta = client.patch(
        f"{API}/legajos/{legajo_id}/estado",
        json={"accion": accion, "comentario": comentario},
        headers=headers,
    )
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def test_un_aspirante_va_de_la_inscripcion_a_la_matricula(
    client, cohorte, carrera, headers_coordinador, bandeja
):
    # 1. Ana se inscribe: el legajo nace en BORRADOR y le llega el link por email.
    respuesta = client.post(f"{API}/legajos", json=formulario(cohorte, carrera))
    assert respuesta.status_code == 201, respuesta.text
    creado = respuesta.json()
    token, legajo_id = creado["token"], creado["legajoId"]
    assert creado["estado"] == "BORRADOR"
    assert [(e.plantilla, e.destinatario) for e in bandeja] == [
        ("link_seguimiento.html", EMAIL_DE_ANA)
    ]
    assert bandeja[0].contexto["link"].endswith(f"/seguimiento/{token}")

    # 2. Con el link ve qué le falta. Sin los PDFs no puede enviar y el legajo no cambia.
    seguimiento = client.get(f"{API}/seguimiento/{token}").json()
    assert sorted(seguimiento["documentosFaltantes"]) == sorted(DOCUMENTOS_DE_ANA)
    sin_pdfs = client.post(f"{API}/seguimiento/{token}/enviar")
    assert (sin_pdfs.status_code, sin_pdfs.json()["error"]) == (422, "DOCUMENTOS_FALTANTES")
    assert client.get(f"{API}/seguimiento/{token}").json()["estado"] == "BORRADOR"

    # 3. Sube los 6 PDFs y envía: queda PENDIENTE, ya no puede editar y le llega la confirmación.
    for tipo in DOCUMENTOS_DE_ANA:
        assert subir(client, token, tipo).status_code == 201
    respuesta = client.post(f"{API}/seguimiento/{token}/enviar")
    assert respuesta.status_code == 200, respuesta.text
    enviado = respuesta.json()
    assert (enviado["estado"], enviado["documentosFaltantes"]) == ("PENDIENTE", [])
    assert enviado["puedeEditar"] is False
    assert enviado["fechaInscripcion"] is not None
    assert bandeja[-1].plantilla == "confirmacion_envio.html"
    assert bandeja[-1].contexto["es_correccion"] is False

    # 4. El coordinador la encuentra en el dashboard por DNI y por apellido.
    por_dni = client.get(f"{API}/legajos", params={"q": "28456789"}, headers=headers_coordinador)
    assert [(f["id"], f["estado"]) for f in por_dni.json()["items"]] == [(legajo_id, "PENDIENTE")]
    por_apellido = client.get(f"{API}/legajos", params={"q": "rodr"}, headers=headers_coordinador)
    assert [f["id"] for f in por_apellido.json()["items"]] == [legajo_id]

    # 5. La revisa y la observa: a Ana le llega el comentario por email.
    revisado = cambiar(client, headers_coordinador, legajo_id, "REVISAR")
    assert revisado["estado"] == "EN_REVISION"
    assert set(revisado["accionesPermitidas"]) == {"OBSERVAR", "APROBAR", "RECHAZAR"}
    observacion = "Falta la copia del título de grado legalizada"
    observado = cambiar(client, headers_coordinador, legajo_id, "OBSERVAR", observacion)
    assert observado["estado"] == "OBSERVADO"
    assert (bandeja[-1].plantilla, bandeja[-1].contexto["comentario"]) == (
        "observacion.html",
        observacion,
    )

    # 6. Ana ve la observación, corrige un dato y el PDF, y reenvía: es CORREGIR, no ENVIAR.
    seguimiento = client.get(f"{API}/seguimiento/{token}").json()
    assert (seguimiento["estado"], seguimiento["ultimaObservacion"]) == ("OBSERVADO", observacion)
    assert seguimiento["puedeEditar"] is True
    datos = formulario(cohorte, carrera, telefonoFijo="0221 4123456")
    del datos["cohorteId"]  # la cohorte no se cambia al editar
    editado = client.put(f"{API}/seguimiento/{token}", json=datos)
    assert editado.status_code == 200, editado.text
    assert editado.json()["telefonoFijo"] == "0221 4123456"
    titulo_legalizado = PDF + b"\n% legalizado"
    assert subir(client, token, "TITULO_GRADO", titulo_legalizado).status_code == 201
    corregido = client.post(f"{API}/seguimiento/{token}/enviar")
    assert corregido.json()["estado"] == "PENDIENTE"
    assert (bandeja[-1].plantilla, bandeja[-1].contexto["es_correccion"]) == (
        "confirmacion_envio.html",
        True,
    )

    # 7. El coordinador la aprueba: número de legajo AA-CCC-SSS y email con ese número.
    cambiar(client, headers_coordinador, legajo_id, "REVISAR")
    aprobado = cambiar(client, headers_coordinador, legajo_id, "APROBAR")
    assert (aprobado["estado"], aprobado["numeroLegajo"]) == ("COMPLETADO", "26-001-001")
    assert aprobado["fechaAprobacion"] is not None
    assert (bandeja[-1].plantilla, bandeja[-1].contexto["numero_legajo"]) == (
        "aprobacion.html",
        "26-001-001",
    )

    # 8. La matricula: queda ACTIVO, con su fecha.
    matriculado = cambiar(client, headers_coordinador, legajo_id, "MATRICULAR")
    assert matriculado["estado"] == "ACTIVO"
    assert matriculado["fechaActivacion"] is not None

    # 9. El historial cuenta cada paso con quién lo hizo, y Ana recibió los 5 emails del camino.
    assert [(r["accion"], r["rol"]) for r in matriculado["historial"]] == [
        ("ENVIAR", "ASPIRANTE"),
        ("REVISAR", "COORDINADOR"),
        ("OBSERVAR", "COORDINADOR"),
        ("CORREGIR", "ASPIRANTE"),
        ("REVISAR", "COORDINADOR"),
        ("APROBAR", "COORDINADOR"),
        ("MATRICULAR", "COORDINADOR"),
    ]
    assert [e.plantilla for e in bandeja] == [
        "link_seguimiento.html",
        "confirmacion_envio.html",
        "observacion.html",
        "confirmacion_envio.html",
        "aprobacion.html",
    ]
    assert {e.destinatario for e in bandeja} == {EMAIL_DE_ANA}

    # 10. El coordinador baja el título corregido: es el último que subió Ana.
    titulo = next(d for d in matriculado["documentos"] if d["tipo"] == "TITULO_GRADO")
    descarga = client.get(
        f"{API}/documentos/{titulo['documentoId']}/download", headers=headers_coordinador
    )
    assert descarga.status_code == 200
    assert descarga.content == titulo_legalizado


def test_con_el_periodo_cerrado_el_formulario_no_acepta_inscripciones(
    client, cohorte, carrera, headers_coordinador
):
    url_periodo = f"{API}/cohortes/{cohorte.id}/inscripcion"

    # El coordinador cierra el período con la próxima apertura: el formulario lo ve cerrado.
    cerrar = {"abierta": False, "proximaApertura": "2027-03-01"}
    assert client.patch(url_periodo, json=cerrar, headers=headers_coordinador).status_code == 200
    cohortes = client.get(f"{API}/cohortes").json()
    assert next(c for c in cohortes if c["id"] == str(cohorte.id))["inscripcionAbierta"] is False
    rechazada = client.post(f"{API}/legajos", json=formulario(cohorte, carrera))
    assert (rechazada.status_code, rechazada.json()["error"]) == (409, "PERIODO_CERRADO")

    # Lo vuelve a abrir y la misma inscripción entra.
    abrir = {"abierta": True}
    assert client.patch(url_periodo, json=abrir, headers=headers_coordinador).status_code == 200
    assert client.post(f"{API}/legajos", json=formulario(cohorte, carrera)).status_code == 201


def test_una_reserva_aprobada_vence_a_los_30_dias_y_avisa_a_los_coordinadores(
    client, session, cohorte, carrera, coordinador, headers_coordinador, bandeja
):
    # Ana llega a COMPLETADO por el camino corto: inscripción, PDFs, envío, revisión y aprobación.
    creado = client.post(f"{API}/legajos", json=formulario(cohorte, carrera)).json()
    token, legajo_id = creado["token"], creado["legajoId"]
    for tipo in DOCUMENTOS_DE_ANA:
        subir(client, token, tipo)
    client.post(f"{API}/seguimiento/{token}/enviar")
    cambiar(client, headers_coordinador, legajo_id, "REVISAR")
    aprobado = cambiar(client, headers_coordinador, legajo_id, "APROBAR")
    fecha_aprobacion = datetime.fromisoformat(aprobado["fechaAprobacion"])

    # A los 29 días la tarea diaria no la toca; a los 30 la vence (BR-005, E6).
    antes = correr_vencimiento(session, ahora=fecha_aprobacion + timedelta(days=29))
    assert antes.vencidos == []
    resultado = correr_vencimiento(session, ahora=fecha_aprobacion + timedelta(days=30))
    assert [legajo.numero_legajo for legajo in resultado.vencidos] == ["26-001-001"]

    # El coordinador la ve VENCIDO, hecho por el sistema, y le llegó el aviso por email.
    detalle = client.get(f"{API}/legajos/{legajo_id}", headers=headers_coordinador).json()
    assert detalle["estado"] == "VENCIDO"
    assert (detalle["historial"][-1]["accion"], detalle["historial"][-1]["rol"]) == (
        "VENCER",
        "SISTEMA",
    )
    assert (bandeja[-1].plantilla, bandeja[-1].destinatario) == (
        "vencimiento_coordinador.html",
        coordinador.email,
    )
