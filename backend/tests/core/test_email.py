"""Tests del envío de mails (NFR-REL-002).

El servidor SMTP se reemplaza por uno falso: los tests no dependen de que
MailHog esté levantado.
"""

import logging
import smtplib

import pytest

from app.core import config
from app.core.email import enviar_email


class SMTPFalso:
    """Imita a smtplib.SMTP y guarda lo que se le pidió."""

    def __init__(self, host, port, timeout):
        self.host, self.port, self.timeout = host, port, timeout
        self.tls = False
        self.credenciales = None
        self.enviados = []
        SMTPFalso.ultimo = self

    def __enter__(self):
        return self

    def __exit__(self, *excepcion):
        return False

    def starttls(self):
        self.tls = True

    def login(self, usuario, clave):
        self.credenciales = (usuario, clave)

    def send_message(self, mensaje):
        self.enviados.append(mensaje)


@pytest.fixture
def smtp_falso(monkeypatch) -> type[SMTPFalso]:
    monkeypatch.setattr(smtplib, "SMTP", SMTPFalso)
    return SMTPFalso


def test_enviar_email_arma_el_mensaje_y_lo_manda(smtp_falso):
    enviado = enviar_email("ana@example.com", "Recibimos tu preinscripción", "Hola Ana")
    servidor = smtp_falso.ultimo
    mensaje = servidor.enviados[0]
    assert enviado is True
    assert (servidor.host, servidor.port) == (config.SMTP_HOST, config.SMTP_PORT)
    assert mensaje["From"] == config.EMAIL_FROM
    assert mensaje["To"] == "ana@example.com"
    assert mensaje["Subject"] == "Recibimos tu preinscripción"
    assert mensaje.get_content().strip() == "Hola Ana"


def test_con_smtp_institucional_usa_starttls_y_login(smtp_falso, monkeypatch):
    monkeypatch.setattr(config, "SMTP_STARTTLS", True)
    monkeypatch.setattr(config, "SMTP_USER", "posgrado")
    monkeypatch.setattr(config, "SMTP_PASSWORD", "secreta")
    enviar_email("ana@example.com", "Asunto", "Cuerpo")
    assert smtp_falso.ultimo.tls is True
    assert smtp_falso.ultimo.credenciales == ("posgrado", "secreta")


@pytest.mark.parametrize(
    "falla",
    [ConnectionRefusedError("MailHog apagado"), smtplib.SMTPException("rechazado")],
)
def test_si_el_smtp_falla_devuelve_false_y_no_lanza(monkeypatch, caplog, falla):
    def smtp_caido(*args, **kwargs):
        raise falla

    monkeypatch.setattr(smtplib, "SMTP", smtp_caido)
    with caplog.at_level(logging.ERROR):
        enviado = enviar_email("ana.rodriguez@example.com", "Legajo aprobado", "Datos privados")
    assert enviado is False
    # El error queda en el log, con el destinatario enmascarado y SIN el cuerpo.
    assert "Legajo aprobado" in caplog.text
    assert "a***@example.com" in caplog.text
    assert "ana.rodriguez" not in caplog.text
    assert "Datos privados" not in caplog.text
