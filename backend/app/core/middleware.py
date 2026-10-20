"""
Headers de seguridad — hardening de la capa HTTP (NFR-S05).

Es el SecurityHeadersMiddleware del módulo 05 con un agregado que pide el
SRS: la Content-Security-Policy. Cada header responde a un ataque:

  - X-Content-Type-Options: nosniff → el navegador no "adivina" el tipo MIME:
    un archivo subido no se ejecuta como HTML o JS.
  - X-Frame-Options: DENY → la API no se puede meter en un <iframe>
    (clickjacking).
  - Content-Security-Policy: default-src 'none' → una respuesta de la API no
    puede cargar ni ejecutar nada. Es JSON o un PDF: no necesita scripts.
  - Referrer-Policy: no-referrer → la URL no se filtra en el header Referer.
  - Strict-Transport-Security → fuerza HTTPS cuando el server lo sirva.
  - Cache-Control: no-store en /api/v1 → los datos personales no quedan en la
    caché del navegador ni de un proxy.

Swagger es la excepción: /api/docs carga su JS y su CSS desde un CDN y
ejecuta un script inline, así que una CSP estricta lo deja en blanco. Por
eso la CSP NO se manda en /api/docs ni en /api/openapi.json.

Es un middleware ASGI puro: corre antes que cualquier router y agrega los
headers a TODAS las respuestas, también a las de error.
"""

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import API_PREFIX

# Para respuestas JSON y PDF: no se carga ni se ejecuta nada.
CSP_API = "default-src 'none'; frame-ancestors 'none'"

# Rutas de Swagger, que necesitan su JS y su CSS.
_RUTAS_SIN_CSP = ("/api/docs", "/api/openapi.json")


class SecurityHeadersMiddleware:
    """Agrega los headers de seguridad a cada respuesta HTTP."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            # No es HTTP (por ejemplo, el lifespan): pasa sin tocar.
            await self.app(scope, receive, send)
            return

        ruta: str = scope["path"]

        async def enviar_con_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-Content-Type-Options"] = "nosniff"
                headers["X-Frame-Options"] = "DENY"
                headers["Referrer-Policy"] = "no-referrer"
                headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
                if not ruta.startswith(_RUTAS_SIN_CSP):
                    headers["Content-Security-Policy"] = CSP_API
                if ruta.startswith(API_PREFIX):
                    headers["Cache-Control"] = "no-store"
            await send(message)

        await self.app(scope, receive, enviar_con_headers)
