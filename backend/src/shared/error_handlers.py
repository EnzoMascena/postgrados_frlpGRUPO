"""Convierte cualquier error en el formato uniforme de ARQUITECTURA §11.2:

{"statusCode": 409, "error": "CONFLICT", "message": "...", "field": "dni", "timestamp": "...Z"}
"""

import logging
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic.alias_generators import to_camel
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.shared.errors import ErrorDeNegocio
from src.shared.security_headers import agregar_headers_de_seguridad

logger = logging.getLogger(__name__)

CODIGOS_HTTP = {
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    429: "RATE_LIMITED",
}

# Mensajes en español para los errores que levanta el propio framework (una ruta que no existe,
# un método que no corresponde, etc.), cuyo `detail` viene en inglés.
MENSAJES_HTTP = {
    401: "Necesitás iniciar sesión para continuar",
    403: "No tenés permiso para hacer esto",
    404: "No encontramos lo que buscás",
    405: "Este método no está permitido en esta ruta",
    429: "Hiciste demasiadas solicitudes. Probá de nuevo más tarde",
}


def cuerpo_de_error(
    status_code: int, codigo: str, mensaje: str, campo: str | None = None
) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "error": codigo,
        "message": mensaje,
        "field": campo,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def _mensaje_http(status_code: int, detalle: Any) -> str:
    frase_en_ingles = HTTPStatus(status_code).phrase
    if isinstance(detalle, str) and detalle != frase_en_ingles:
        return detalle  # alguien levantó un HTTPException con su propio mensaje
    return MENSAJES_HTTP.get(status_code, frase_en_ingles)


def _campo_del_error(error: dict[str, Any]) -> str | None:
    # `loc` es algo como ("body", "telefonoMovil") o ("body", "carreraIds", 0): el campo es el
    # último nombre, y los índices de lista no cuentan.
    nombres = [parte for parte in error["loc"] if isinstance(parte, str)]
    return to_camel(nombres[-1]) if nombres else None


def registrar_manejadores_de_errores(app: FastAPI) -> None:
    @app.exception_handler(ErrorDeNegocio)
    async def manejar_error_de_negocio(request: Request, exc: ErrorDeNegocio) -> JSONResponse:
        cuerpo = cuerpo_de_error(exc.status_code, exc.codigo, exc.mensaje, exc.campo)
        return JSONResponse(status_code=exc.status_code, content=cuerpo)

    @app.exception_handler(StarletteHTTPException)
    async def manejar_error_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        codigo = CODIGOS_HTTP.get(exc.status_code, "HTTP_ERROR")
        mensaje = _mensaje_http(exc.status_code, exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=cuerpo_de_error(exc.status_code, codigo, mensaje),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def manejar_error_de_validacion(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Se informa solo el primer error, que es lo que el front muestra junto al campo.
        error = exc.errors()[0]
        campo = _campo_del_error(error)
        if error["type"] == "missing":
            mensaje = f"El campo {campo} es obligatorio"
        else:
            mensaje = f"El valor de {campo} no es válido"
        return JSONResponse(
            status_code=422, content=cuerpo_de_error(422, "VALIDATION_ERROR", mensaje, campo)
        )

    @app.exception_handler(Exception)
    async def manejar_error_inesperado(request: Request, exc: Exception) -> JSONResponse:
        # Al cliente no le llega ningún detalle interno: queda solo en el log.
        logger.exception("Error no controlado en %s %s", request.method, request.url.path)
        mensaje = "Ocurrió un error inesperado. Probá de nuevo más tarde"
        respuesta = JSONResponse(
            status_code=500, content=cuerpo_de_error(500, "INTERNAL_ERROR", mensaje)
        )
        # Starlette responde este error desde su middleware más externo, por fuera del nuestro.
        agregar_headers_de_seguridad(respuesta)
        return respuesta
