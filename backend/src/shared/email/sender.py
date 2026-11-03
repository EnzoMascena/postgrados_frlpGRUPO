"""Envío de emails con plantillas HTML (US-CORE-006).

`enviar_email` arma el HTML con Jinja2 desde `templates/` y lo manda por SMTP (MailHog en
desarrollo, http://localhost:8025). En los tests no sale nada: cada email queda en
`BANDEJA_DE_PRUEBA`, que se mira con la fixture `bandeja`.
"""

import html as html_stdlib
import logging
import re
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from src.shared.config import settings

logger = logging.getLogger(__name__)

CARPETA = Path(__file__).parent
LOGO = CARPETA / "static" / "logo-utn.png"
LOGO_CID = "logo-utn"  # las plantillas lo usan como <img src="cid:logo-utn">

# StrictUndefined: una variable que falta en el contexto es un error, no un hueco en blanco.
# select_autoescape: en las plantillas .html todo lo que viene del contexto sale escapado.
_entorno = Environment(
    loader=FileSystemLoader(CARPETA / "templates"),
    undefined=StrictUndefined,
    autoescape=select_autoescape(),
)


@dataclass(frozen=True)
class EmailEnviado:
    destinatario: str
    asunto: str
    plantilla: str
    contexto: dict[str, Any]
    html: str


# En los tests (ENVIRONMENT=testing) los emails no salen: se guardan acá.
BANDEJA_DE_PRUEBA: list[EmailEnviado] = []


def _link_a_texto(coincidencia: re.Match[str]) -> str:
    url, texto = coincidencia.group(1), coincidencia.group(2).strip()
    # Si el link ya muestra su dirección, repetirla entre paréntesis sería ruido.
    return url if texto == url else f"{texto} ({url})"


def _a_texto(html: str) -> str:
    """Una versión de texto simple del HTML, para los clientes de correo que no lo muestran."""
    texto = re.sub(r"(?is)<(style|script|head).*?</\1>", "", html)
    # El preheader (el resumen que muestra la bandeja de entrada) está oculto con display:none.
    texto = re.sub(r"(?is)<div[^>]*display:\s*none[^>]*>.*?</div>", "", texto)
    # Un link se lee como "texto (url)": sin eso, en texto plano el botón no tiene a dónde ir.
    texto = re.sub(r'(?is)<a\s[^>]*href="([^"]+)"[^>]*>(.*?)</a>', _link_a_texto, texto)
    texto = re.sub(r"(?i)<br\s*/?>|</(p|div|tr|h[1-6]|li)>", "\n", texto)
    texto = html_stdlib.unescape(re.sub(r"<[^>]+>", "", texto))
    lineas = (re.sub(r"[ \t]+", " ", linea).strip() for linea in texto.splitlines())
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lineas)).strip()


def _armar_mensaje(destinatario: str, asunto: str, html: str) -> EmailMessage:
    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = settings.email_from
    mensaje["To"] = destinatario
    # quoted-printable: el mensaje viaja en ASCII puro. Con 8 bits crudos, un servidor que no
    # anuncie 8BITMIME puede romper los acentos (MailHog no se queja, pero uno real sí).
    mensaje.set_content(_a_texto(html), cte="quoted-printable")
    mensaje.add_alternative(html, subtype="html", cte="quoted-printable")
    # El logo viaja dentro del mensaje, como imagen relacionada con el HTML (cid:logo-utn).
    parte_html = mensaje.get_body(preferencelist=("html",))
    parte_html.add_related(LOGO.read_bytes(), maintype="image", subtype="png", cid=f"<{LOGO_CID}>")
    return mensaje


def enviar_email(destinatario: str, asunto: str, plantilla: str, contexto: dict[str, Any]) -> bool:
    """Manda un email armado con `plantilla` (por ejemplo "aprobacion.html") y devuelve si salió.

    Si el SMTP falla devuelve `False` y lo deja en el log, sin levantar la excepción: un email
    que no sale no tiene que deshacer un cambio de estado. En cambio, una plantilla que no
    existe o una variable que falta en `contexto` sí levantan un error: son fallas del código,
    no del servidor de correo.
    """
    html = _entorno.get_template(plantilla).render(contexto)
    mensaje = _armar_mensaje(destinatario, asunto, html)

    if settings.environment == "testing":
        BANDEJA_DE_PRUEBA.append(EmailEnviado(destinatario, asunto, plantilla, contexto, html))
        return True

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as servidor:
            servidor.send_message(mensaje)
    except OSError:  # incluye smtplib.SMTPException, que hereda de OSError
        logger.exception("No se pudo enviar el email %s a %s", plantilla, destinatario)
        return False
    return True
