"""
Envío de mails por SMTP — MailHog en desarrollo.

En local, MailHog recibe todo en el puerto 1025 y lo muestra en
http://localhost:8025: ningún mail sale a internet. En producción se apunta
SMTP_HOST al SMTP institucional (supuesto A-004 del SRS).

Tolerancia a fallos (NFR-REL-002): si el SMTP falla, la operación que
mandaba el mail SIGUE. `enviar_email` nunca lanza: devuelve False y deja
el error en el log. Que un mail no salga no puede deshacer, por ejemplo,
la aprobación de un legajo.
(El PRD además pide reintentar en 1 hora: queda pendiente.)

Datos personales (DoD): el log registra el asunto y el destinatario
enmascarado, nunca el cuerpo del mail.

Uso desde un service:
    from app.core.email import enviar_email
    enviar_email(legajo.email, "Recibimos tu preinscripción", cuerpo)
"""

import logging
import smtplib
from email.message import EmailMessage

from app.core import config

logger = logging.getLogger(__name__)


def _enmascarar(email: str) -> str:
    """Enmascara el email para el log: ana.rodriguez@gmail.com → a***@gmail.com."""
    usuario, _, dominio = email.partition("@")
    return f"{usuario[:1]}***@{dominio}" if dominio else "***"


def enviar_email(destinatario: str, asunto: str, cuerpo: str) -> bool:
    """Manda un mail de texto plano. True si salió; False si falló el SMTP."""
    mensaje = EmailMessage()
    mensaje["From"] = config.EMAIL_FROM
    mensaje["To"] = destinatario
    mensaje["Subject"] = asunto
    mensaje.set_content(cuerpo)

    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=10) as smtp:
            if config.SMTP_STARTTLS:
                smtp.starttls()
            if config.SMTP_USER and config.SMTP_PASSWORD:
                smtp.login(config.SMTP_USER, config.SMTP_PASSWORD)
            smtp.send_message(mensaje)
    except (OSError, smtplib.SMTPException):
        logger.exception(
            "No se pudo enviar el mail '%s' a %s: la operación sigue sin el mail",
            asunto,
            _enmascarar(destinatario),
        )
        return False

    logger.info("Mail enviado: '%s' a %s", asunto, _enmascarar(destinatario))
    return True
