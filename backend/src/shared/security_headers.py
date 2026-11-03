"""Headers de seguridad en todas las respuestas (NFR-S05)."""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Solo para JSON: Swagger (HTML) y los PDFs no funcionan con una política tan cerrada.
CSP_DE_LA_API = "default-src 'none'; frame-ancestors 'none'"


def agregar_headers_de_seguridad(respuesta: Response) -> None:
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    respuesta.headers["X-Frame-Options"] = "DENY"
    respuesta.headers["Referrer-Policy"] = "no-referrer"
    if respuesta.headers.get("content-type", "").startswith("application/json"):
        respuesta.headers["Content-Security-Policy"] = CSP_DE_LA_API


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        respuesta = await call_next(request)
        agregar_headers_de_seguridad(respuesta)
        return respuesta
