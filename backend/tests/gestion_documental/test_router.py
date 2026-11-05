"""Subida y descarga de PDFs y `GET /seguimiento/{token}`, contra la app real, la base de test y
una carpeta temporal como STORAGE_PATH (la pone el conftest)."""

import hashlib

import pytest
from sqlmodel import select

from src.gestion_documental.domain.pdf import MENSAJE_DEMASIADO_GRANDE, MENSAJE_NO_ES_PDF
from src.gestion_documental.domain.tipos import TAMANIO_MAXIMO_BYTES
from src.gestion_documental.infrastructure.almacenamiento import borrar_pdf, ruta_del_pdf
from src.gestion_documental.infrastructure.orm_models import DocumentoORM
from src.inscripcion.infrastructure.links import crear_link_seguimiento
from src.legajos.domain.estados import EstadoLegajo
from tests.fabricas import crear_carrera, crear_cohorte, crear_legajo

PDF = b"%PDF-1.7\n1 0 obj << >> endobj\n%%EOF"
API = "/api/v1"


@pytest.fixture
def cohorte(session):
    return crear_cohorte(session)


@pytest.fixture
def legajo(session, cohorte):
    return crear_legajo(session, cohorte, [crear_carrera(session)])


@pytest.fixture
def token(session, legajo):
    return crear_link_seguimiento(session, legajo.id)


def subir(client, token, tipo="DNI", contenido=PDF, nombre="dni.pdf"):
    return client.post(
        f"{API}/seguimiento/{token}/documentos",
        data={"tipo": tipo},
        files={"archivo": (nombre, contenido, "application/pdf")},
    )


def documentos(session) -> list[DocumentoORM]:
    return list(session.exec(select(DocumentoORM)))


# --- POST /seguimiento/{token}/documentos ---


def test_subir_un_pdf_da_201_con_el_cuerpo_del_plan(client, token):
    respuesta = subir(client, token)

    cuerpo = respuesta.json()
    assert respuesta.status_code == 201
    assert set(cuerpo) == {
        "documentoId",
        "tipo",
        "nombreOriginal",
        "tamanioBytes",
        "checksumSha256",
        "fechaSubida",
    }
    assert (cuerpo["tipo"], cuerpo["nombreOriginal"]) == ("DNI", "dni.pdf")
    assert cuerpo["tamanioBytes"] == len(PDF)
    assert cuerpo["checksumSha256"] == hashlib.sha256(PDF).hexdigest()


def test_el_archivo_queda_en_disco_con_nombre_uuid_y_su_fila_en_la_base(
    client, session, token, cohorte, legajo
):
    subir(client, token, nombre="mi DNI escaneado.pdf")

    fila = documentos(session)[0]
    assert fila.legajo_id == legajo.id
    assert fila.path_storage.startswith(f"uploads/{cohorte.id}/{legajo.id}/")
    assert fila.path_storage.endswith(".pdf")
    assert "DNI" not in fila.path_storage  # el nombre del aspirante no llega al disco
    assert ruta_del_pdf(fila.path_storage).read_bytes() == PDF


def test_subir_otro_del_mismo_tipo_reemplaza_la_fila_y_borra_el_archivo_viejo(
    client, session, token
):
    primero = subir(client, token).json()
    viejo = documentos(session)[0].path_storage
    nuevo_pdf = PDF + b"\n% version 2"

    segundo = subir(client, token, contenido=nuevo_pdf, nombre="dni-v2.pdf").json()

    filas = documentos(session)
    assert len(filas) == 1
    assert segundo["documentoId"] == primero["documentoId"]
    assert segundo["checksumSha256"] == hashlib.sha256(nuevo_pdf).hexdigest()
    assert not ruta_del_pdf(viejo).exists()
    assert ruta_del_pdf(filas[0].path_storage).read_bytes() == nuevo_pdf


@pytest.mark.parametrize(
    ("contenido", "mensaje"),
    [
        (b"esto es texto con extension .pdf", MENSAJE_NO_ES_PDF),
        (b"", MENSAJE_NO_ES_PDF),
        (b"%PDF-" + b"0" * TAMANIO_MAXIMO_BYTES, MENSAJE_DEMASIADO_GRANDE),
    ],
)
def test_lo_que_no_es_pdf_o_pasa_los_5_mb_da_422_y_no_guarda_nada(
    client, session, token, contenido, mensaje
):
    respuesta = subir(client, token, contenido=contenido)

    assert respuesta.status_code == 422
    assert respuesta.json()["error"] == "ARCHIVO_INVALIDO"
    assert (respuesta.json()["field"], respuesta.json()["message"]) == ("archivo", mensaje)
    assert documentos(session) == []


def test_un_tipo_que_no_le_corresponde_al_legajo_da_422_en_tipo(client, token):
    respuesta = subir(client, token, tipo="FORM_BECA")  # el legajo no pidió beca

    assert respuesta.status_code == 422
    assert (respuesta.json()["error"], respuesta.json()["field"]) == ("ARCHIVO_INVALIDO", "tipo")


@pytest.mark.parametrize(
    ("pedido", "campo"),
    [
        ({"data": {"tipo": "FOTO"}, "files": {"archivo": ("a.pdf", PDF)}}, "tipo"),
        ({"data": {}, "files": {"archivo": ("a.pdf", PDF)}}, "tipo"),
        ({"data": {"tipo": "DNI"}}, "archivo"),
    ],
)
def test_falta_o_viene_mal_un_campo_del_formulario_da_422(client, token, pedido, campo):
    respuesta = client.post(f"{API}/seguimiento/{token}/documentos", **pedido)

    assert respuesta.status_code == 422
    assert (respuesta.json()["error"], respuesta.json()["field"]) == ("VALIDATION_ERROR", campo)


def test_con_el_legajo_ya_enviado_da_409_y_no_guarda_nada(client, session, token, legajo):
    legajo.estado = EstadoLegajo.PENDIENTE.value
    session.commit()

    respuesta = subir(client, token)

    assert respuesta.status_code == 409
    assert respuesta.json()["error"] == "LEGAJO_NO_EDITABLE"
    assert documentos(session) == []


def test_con_un_link_invalido_da_404(client):
    respuesta = subir(client, "token-inventado")

    assert respuesta.status_code == 404


# --- descargas ---


def descarga_del_aspirante(client, token, documento_id):
    return client.get(f"{API}/seguimiento/{token}/documentos/{documento_id}/download")


def test_el_aspirante_descarga_su_pdf_con_los_headers_del_plan(client, token):
    documento_id = subir(client, token, nombre="Título ñandú.pdf").json()["documentoId"]

    respuesta = descarga_del_aspirante(client, token, documento_id)

    assert respuesta.status_code == 200
    assert respuesta.content == PDF
    assert respuesta.headers["content-type"] == "application/pdf"
    assert respuesta.headers["content-disposition"].startswith("inline;")
    assert (
        "filename*=utf-8''T%C3%ADtulo%20%C3%B1and%C3%BA.pdf"
        in (respuesta.headers["content-disposition"])
    )
    assert respuesta.headers["cache-control"] == "no-store"
    assert respuesta.headers["x-content-type-options"] == "nosniff"


def test_el_aspirante_no_puede_bajar_un_pdf_de_otro_legajo(client, session, cohorte, token):
    otro = crear_legajo(session, cohorte, [crear_carrera(session)])
    token_del_otro = crear_link_seguimiento(session, otro.id)
    ajeno = subir(client, token_del_otro).json()["documentoId"]

    respuesta = descarga_del_aspirante(client, token, ajeno)

    assert respuesta.status_code == 404


def test_si_el_archivo_ya_no_esta_en_disco_da_404(client, session, token):
    documento_id = subir(client, token).json()["documentoId"]
    borrar_pdf(documentos(session)[0].path_storage)

    respuesta = descarga_del_aspirante(client, token, documento_id)

    assert respuesta.status_code == 404


def test_el_coordinador_descarga_cualquier_pdf(client, token, headers_coordinador):
    documento_id = subir(client, token).json()["documentoId"]

    respuesta = client.get(f"{API}/documentos/{documento_id}/download", headers=headers_coordinador)

    assert respuesta.status_code == 200
    assert respuesta.content == PDF
    assert respuesta.headers["cache-control"] == "no-store"


def test_la_descarga_del_coordinador_pide_sesion_y_rol(client, token, headers_docente):
    documento_id = subir(client, token).json()["documentoId"]
    url = f"{API}/documentos/{documento_id}/download"

    assert client.get(url).status_code == 401
    assert client.get(url, headers=headers_docente).status_code == 403


def test_un_documento_que_no_existe_da_404_al_coordinador(client, headers_coordinador):
    url = f"{API}/documentos/00000000-0000-0000-0000-000000000000/download"

    assert client.get(url, headers=headers_coordinador).status_code == 404


# --- GET /seguimiento/{token} ---


def test_ver_mi_legajo_muestra_el_checklist_con_lo_subido(client, token, legajo):
    documento_id = subir(client, token).json()["documentoId"]

    respuesta = client.get(f"{API}/seguimiento/{token}")

    cuerpo = respuesta.json()
    assert respuesta.status_code == 200
    assert cuerpo["id"] == str(legajo.id)
    assert cuerpo["puedeEditar"] is True
    assert "historial" not in cuerpo and "accionesPermitidas" not in cuerpo
    dni = next(item for item in cuerpo["documentos"] if item["tipo"] == "DNI")
    assert (dni["cargado"], dni["documentoId"]) == (True, documento_id)
    assert "DNI" not in cuerpo["documentosFaltantes"]
    assert len(cuerpo["documentosFaltantes"]) == 4


def test_ver_mi_legajo_con_un_link_invalido_da_404(client):
    respuesta = client.get(f"{API}/seguimiento/token-inventado")

    assert respuesta.status_code == 404
    assert respuesta.json()["error"] == "NOT_FOUND"
