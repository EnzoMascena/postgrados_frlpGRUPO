"""El envío de emails: la bandeja de prueba, el mensaje real (texto, HTML y logo) y los errores.

Usan las plantillas reales de `templates/` con los contextos de ejemplo de
`scripts/previsualizar_emails.py` (los mismos que usa `test_plantillas_email.py`), y un SMTP falso:
no necesitan MailHog.
"""

import smtplib
from email import message_from_bytes, policy

import pytest
from jinja2 import TemplateNotFound, UndefinedError

from scripts.previsualizar_emails import EJEMPLOS
from src.shared.config import settings
from src.shared.email.sender import LOGO, enviar_email

PLANTILLA = "link_seguimiento.html"
CONTEXTO = EJEMPLOS[PLANTILLA]  # nombre, codigo_seguimiento y link
LINK = CONTEXTO["link"]
SCRIPT = "<script>alert('hola')</script>"


@pytest.fixture
def smtp(monkeypatch):
    """Reemplaza `smtplib.SMTP` por uno falso que anota todo lo que se le pide."""

    class SMTPFalso:
        conexiones: list[tuple] = []
        mensajes: list = []
        error_al_conectar: Exception | None = None
        error_al_enviar: Exception | None = None

        def __init__(self, host, port, timeout=None):
            if SMTPFalso.error_al_conectar:
                raise SMTPFalso.error_al_conectar
            SMTPFalso.conexiones.append((host, port, timeout))

        def __enter__(self):
            return self

        def __exit__(self, *excepcion):
            return False

        def send_message(self, mensaje):
            if SMTPFalso.error_al_enviar:
                raise SMTPFalso.error_al_enviar
            SMTPFalso.mensajes.append(mensaje)

    monkeypatch.setattr(smtplib, "SMTP", SMTPFalso)
    return SMTPFalso


@pytest.fixture
def en_desarrollo(monkeypatch):
    """Fuera de testing el email sale por SMTP en vez de quedar en la bandeja."""
    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings, "smtp_host", "mailhog")
    monkeypatch.setattr(settings, "smtp_port", 1025)


def _partes_con_logo(mensaje):
    return [parte for parte in mensaje.walk() if parte.get_content_type() == "image/png"]


# --- en testing: la bandeja -------------------------------------------------------------------


def test_la_bandeja_llega_vacia_a_cada_test(bandeja):
    assert bandeja == []


def test_en_testing_el_email_queda_en_la_bandeja_y_no_sale_por_smtp(bandeja, smtp):
    salio = enviar_email("ana@example.com", "Tu preinscripción", PLANTILLA, CONTEXTO)

    assert salio is True
    assert smtp.conexiones == []
    (email,) = bandeja
    assert email.destinatario == "ana@example.com"
    assert email.asunto == "Tu preinscripción"
    assert email.plantilla == PLANTILLA
    assert email.contexto == CONTEXTO
    assert "Hola Martina" in email.html
    assert LINK in email.html


def test_lo_que_viene_del_contexto_sale_escapado(bandeja):
    # El comentario que escribe el coordinador llega así a la plantilla de observación.
    contexto = {**EJEMPLOS["observacion.html"], "comentario": SCRIPT}

    enviar_email("ana@example.com", "Observaciones", "observacion.html", contexto)

    assert "<script>" not in bandeja[0].html
    assert "&lt;script&gt;" in bandeja[0].html


@pytest.mark.parametrize("plantilla", EJEMPLOS)
def test_cada_plantilla_real_sale_por_enviar_email(bandeja, plantilla):
    assert enviar_email("ana@example.com", "Asunto", plantilla, EJEMPLOS[plantilla]) is True

    (email,) = bandeja
    assert email.plantilla == plantilla
    assert 'src="cid:logo-utn"' in email.html


# --- fuera de testing: el mensaje que sale por SMTP -------------------------------------------


def test_en_desarrollo_manda_por_smtp_con_timeout_y_no_usa_la_bandeja(bandeja, smtp, en_desarrollo):
    salio = enviar_email("ana@example.com", "Tu preinscripción", PLANTILLA, CONTEXTO)

    assert salio is True
    assert bandeja == []
    assert smtp.conexiones == [("mailhog", 1025, 10)]
    (mensaje,) = smtp.mensajes
    assert mensaje["To"] == "ana@example.com"
    assert mensaje["From"] == settings.email_from
    assert mensaje["Subject"] == "Tu preinscripción"


def test_el_mensaje_tiene_el_html_y_el_logo_con_su_cid(smtp, en_desarrollo):
    enviar_email("ana@example.com", "Tu preinscripción", PLANTILLA, CONTEXTO)

    (mensaje,) = smtp.mensajes
    html = mensaje.get_body(preferencelist=("html",)).get_content()
    assert "Hola Martina" in html
    assert 'src="cid:logo-utn"' in html
    (logo,) = _partes_con_logo(mensaje)
    assert logo["Content-ID"] == "<logo-utn>"
    assert logo.get_content() == LOGO.read_bytes()


def test_el_texto_simple_incluye_el_link_y_deja_afuera_el_resumen_oculto_y_el_estilo(
    smtp, en_desarrollo
):
    enviar_email("ana@example.com", "Tu preinscripción", PLANTILLA, CONTEXTO)

    (mensaje,) = smtp.mensajes
    texto = mensaje.get_body(preferencelist=("plain",)).get_content()
    assert "Hola Martina" in texto
    assert f"Continuar mi preinscripción ({LINK})" in texto
    # El link que ya muestra su dirección no se repite entre paréntesis.
    assert f"{LINK} ({LINK})" not in texto
    # El resumen que la bandeja de entrada muestra al lado del asunto está oculto en el HTML.
    assert "Con este link continuás" not in texto
    assert "<" not in texto


def test_el_asunto_con_acentos_sobrevive_al_viaje(smtp, en_desarrollo):
    asunto = "Tu preinscripción al Posgrado UTN FRLP"
    enviar_email("ana@example.com", asunto, PLANTILLA, CONTEXTO)

    (mensaje,) = smtp.mensajes
    recibido = message_from_bytes(mensaje.as_bytes(), policy=policy.default)
    assert recibido["Subject"] == asunto


@pytest.mark.parametrize("plantilla", EJEMPLOS)
def test_cada_plantilla_real_viaja_en_ascii_con_su_logo_y_sus_links(smtp, en_desarrollo, plantilla):
    contexto = EJEMPLOS[plantilla]

    enviar_email("ana@example.com", "Asunto con acentos: preinscripción", plantilla, contexto)

    (mensaje,) = smtp.mensajes
    # smtplib no avisa que acepta 8 bits (8BITMIME): un acento crudo se puede romper en el camino.
    assert mensaje.as_bytes().isascii()
    assert len(_partes_con_logo(mensaje)) == 1
    texto = mensaje.get_body(preferencelist=("plain",)).get_content()
    assert texto.strip()
    for valor in contexto.values():
        if isinstance(valor, str) and valor.startswith("http"):
            assert valor in texto


# --- cuando algo falla ------------------------------------------------------------------------


@pytest.mark.parametrize(
    "error",
    [
        OSError("sin red"),
        ConnectionRefusedError(),
        TimeoutError(),
        smtplib.SMTPException("rechazado"),
        smtplib.SMTPServerDisconnected("se cortó"),
    ],
)
def test_si_no_se_puede_conectar_devuelve_false_y_lo_deja_en_el_log(
    bandeja, smtp, en_desarrollo, caplog, error
):
    smtp.error_al_conectar = error

    salio = enviar_email("ana@example.com", "Hola", PLANTILLA, CONTEXTO)

    assert salio is False
    assert f"No se pudo enviar el email {PLANTILLA} a ana@example.com" in caplog.text
    assert bandeja == []


def test_si_falla_al_enviar_el_mensaje_tambien_devuelve_false(smtp, en_desarrollo):
    smtp.error_al_enviar = smtplib.SMTPRecipientsRefused({"ana@example.com": (550, b"no existe")})

    assert enviar_email("ana@example.com", "Hola", PLANTILLA, CONTEXTO) is False
    assert smtp.mensajes == []


def test_si_falta_una_variable_del_contexto_falla_en_vez_de_mandar_un_hueco(bandeja):
    contexto = {clave: valor for clave, valor in CONTEXTO.items() if clave != "link"}

    with pytest.raises(UndefinedError, match="link"):
        enviar_email("ana@example.com", "Hola", PLANTILLA, contexto)

    assert bandeja == []


def test_una_plantilla_que_no_existe_falla(bandeja):
    with pytest.raises(TemplateNotFound):
        enviar_email("ana@example.com", "Hola", "no_existe.html", {})


def test_un_error_de_plantilla_no_se_confunde_con_un_smtp_caido(smtp, en_desarrollo):
    # Solo los fallos del servidor de correo devuelven False: un bug en la plantilla tiene que verse.
    smtp.error_al_conectar = OSError("sin red")

    with pytest.raises(UndefinedError):
        enviar_email("ana@example.com", "Hola", PLANTILLA, {"nombre": "Ana"})
