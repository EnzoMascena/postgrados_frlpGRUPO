"""
Formato UNIFORME de errores (ARQUITECTURA §11.2) y los handlers globales.

Toda respuesta de error de la API tiene la misma forma, así el front puede
mostrar el mensaje al lado del campo que corresponde (NFR-U02):

    {
      "statusCode": 400,
      "error": "VALIDATION_ERROR",
      "message": "Ya existe una preinscripción con este DNI para la cohorte actual",
      "field": "dni",
      "timestamp": "2026-04-14T10:30:00Z"
    }

Acá viven tres cosas:

  1. ErrorAPI: la excepción que lanza el CONTROLLER cuando ya decidió el
     status (es una HTTPException con `error` y `field`).
  2. Los handlers que registra main.py, para que TODO error salga con este
     formato y en español:
       · HTTPException → incluye ErrorAPI, los 401/403 de require_role y el
         404/405 de una ruta inexistente.
       · RequestValidationError → 422: el body, un query o un path no valida.
       · NotImplementedError → 501: el método del service todavía es TODO.
       · Cualquier otra excepción → 500, sin filtrar el detalle técnico.
  3. `respuestas(...)`: documenta en Swagger los errores de cada ruta.

El service nunca importa este archivo: lanza las excepciones de dominio de
core/excepciones.py y el controller las traduce.
"""

import logging
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.schemas import CamelModel

logger = logging.getLogger(__name__)

# Código de error legible por status. El front puede decidir por `error`.
_CODIGOS: dict[int, str] = {
    400: "VALIDATION_ERROR",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    422: "VALIDATION_ERROR",
    429: "TOO_MANY_REQUESTS",
    500: "INTERNAL_ERROR",
    501: "NOT_IMPLEMENTED",
    503: "SERVICE_UNAVAILABLE",
}

# Mensaje en español cuando el error no trae uno propio (por ejemplo, el
# "Not Found" en inglés que genera Starlette para una ruta inexistente).
_MENSAJES_POR_DEFECTO: dict[int, str] = {
    400: "La solicitud no es válida.",
    401: "Credenciales inválidas.",
    403: "No tenés permiso para realizar esta operación.",
    404: "El recurso solicitado no existe.",
    405: "Método no permitido en esta ruta.",
    409: "El dato ya existe.",
    413: "El archivo es demasiado grande.",
    422: "Los datos enviados no son válidos.",
    429: "Demasiados intentos. Probá de nuevo más tarde.",
    500: "Ocurrió un error inesperado. Probá de nuevo más tarde.",
    501: "Esta funcionalidad todavía no está implementada.",
    503: "El servicio no está disponible en este momento.",
}

# Las partes de `loc` que indican DÓNDE vino el dato, no CUÁL campo es.
_ORIGENES = {"body", "query", "path", "header", "cookie"}


class ErrorRead(CamelModel):
    """La forma de toda respuesta de error (ARQUITECTURA §11.2)."""

    status_code: int
    error: str
    message: str
    field: str | None = None
    timestamp: datetime


class ErrorAPI(HTTPException):
    """La excepción que lanza el controller con el status ya decidido.

    Uso:
        raise ErrorAPI(404, "El legajo no existe")
        raise ErrorAPI(400, error.mensaje, campo=error.campo) from error
    """

    def __init__(
        self,
        status_code: int,
        mensaje: str,
        *,
        campo: str | None = None,
        error: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=mensaje, headers=headers)
        self.campo = campo
        self.error = error or codigo_de_error(status_code)


def codigo_de_error(status_code: int) -> str:
    """El código legible de un status (`404` → `"NOT_FOUND"`)."""
    return _CODIGOS.get(status_code, "ERROR")


def respuesta_error(
    status_code: int,
    mensaje: str | None = None,
    *,
    campo: str | None = None,
    error: str | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Arma la respuesta JSON con el formato §11.2."""
    cuerpo = ErrorRead(
        status_code=status_code,
        error=error or codigo_de_error(status_code),
        message=mensaje or _MENSAJES_POR_DEFECTO.get(status_code, "Ocurrió un error."),
        field=campo,
        timestamp=datetime.now(UTC).replace(microsecond=0),
    )
    return JSONResponse(
        status_code=status_code,
        content=cuerpo.model_dump(mode="json"),
        headers=headers,
    )


def respuestas(*codigos: int) -> dict[int | str, dict[str, Any]]:
    """Documenta en Swagger los errores que puede devolver una ruta.

    Uso: @router.get("/legajos/{id}", responses=respuestas(401, 403, 404))
    """
    return {
        codigo: {"model": ErrorRead, "description": _MENSAJES_POR_DEFECTO.get(codigo, "Error")}
        for codigo in codigos
    }


# ── Traducción de los errores de validación de Pydantic ───────────────────


def _campo(loc: tuple[Any, ...]) -> str | None:
    """("body", "apellidoNombre") → "apellidoNombre"; ("body",) → None."""
    partes = [str(parte) for parte in loc if parte not in _ORIGENES]
    return ".".join(partes) or None


def _mensaje_validacion(detalle: dict[str, Any]) -> str:
    """Traduce el primer error de Pydantic a un mensaje en español."""
    tipo = detalle.get("type", "")
    ctx = detalle.get("ctx") or {}
    mensaje_original = str(detalle.get("msg", ""))

    if tipo == "value_error":
        # Un field_validator nuestro que lanzó ValueError("mensaje en español").
        if mensaje_original.startswith("Value error, "):
            return mensaje_original.removeprefix("Value error, ")
        if "email address" in mensaje_original:
            return "El email no tiene un formato válido."
        return "El valor ingresado no es válido."

    mensajes = {
        "missing": "Este campo es obligatorio.",
        "string_type": "Tiene que ser un texto.",
        "string_too_short": f"Tiene que tener al menos {ctx.get('min_length')} caracteres.",
        "string_too_long": f"Tiene que tener como máximo {ctx.get('max_length')} caracteres.",
        "string_pattern_mismatch": "El formato no es válido.",
        "int_parsing": "Tiene que ser un número entero.",
        "int_type": "Tiene que ser un número entero.",
        "float_parsing": "Tiene que ser un número.",
        "decimal_parsing": "Tiene que ser un número.",
        "bool_parsing": "Tiene que ser verdadero o falso.",
        "greater_than": f"Tiene que ser mayor que {ctx.get('gt')}.",
        "greater_than_equal": f"Tiene que ser mayor o igual a {ctx.get('ge')}.",
        "less_than": f"Tiene que ser menor que {ctx.get('lt')}.",
        "less_than_equal": f"Tiene que ser menor o igual a {ctx.get('le')}.",
        "uuid_parsing": "El identificador no es válido.",
        "uuid_type": "El identificador no es válido.",
        "date_parsing": "La fecha no es válida (formato AAAA-MM-DD).",
        "date_from_datetime_parsing": "La fecha no es válida (formato AAAA-MM-DD).",
        "datetime_parsing": "La fecha y hora no son válidas.",
        "datetime_from_date_parsing": "La fecha y hora no son válidas.",
        "enum": "El valor no es una de las opciones permitidas.",
        "literal_error": "El valor no es una de las opciones permitidas.",
        "list_type": "Tiene que ser una lista.",
        "too_short": f"Tiene que tener al menos {ctx.get('min_length')} elementos.",
        "too_long": f"Tiene que tener como máximo {ctx.get('max_length')} elementos.",
        "json_invalid": "El cuerpo de la solicitud no es un JSON válido.",
        "model_attributes_type": "El cuerpo de la solicitud no tiene el formato esperado.",
        "dict_type": "El cuerpo de la solicitud no tiene el formato esperado.",
    }
    return mensajes.get(tipo, "El valor ingresado no es válido.")


# ── Handlers globales (los registra main.py) ───────────────────────────────


def _frase_estandar(status_code: int) -> str | None:
    """La frase en inglés del status ("Not Found"), o None si no es estándar."""
    try:
        return HTTPStatus(status_code).phrase
    except ValueError:
        return None


async def _manejar_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    campo = getattr(exc, "campo", None)
    error = getattr(exc, "error", None)
    mensaje = exc.detail if isinstance(exc.detail, str) else None
    # Los errores que arma Starlette solos ("Not Found", "Method Not Allowed")
    # vienen en inglés: los cambiamos por el mensaje en español.
    if mensaje == _frase_estandar(exc.status_code):
        mensaje = None
    return respuesta_error(
        exc.status_code,
        mensaje,
        campo=campo,
        error=error,
        headers=getattr(exc, "headers", None),
    )


async def _manejar_validacion(request: Request, exc: RequestValidationError) -> JSONResponse:
    errores = exc.errors()
    primero = errores[0] if errores else {}
    campo = None if primero.get("type") == "json_invalid" else _campo(tuple(primero.get("loc", ())))
    return respuesta_error(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        _mensaje_validacion(primero),
        campo=campo,
    )


async def _manejar_no_implementado(request: Request, exc: NotImplementedError) -> JSONResponse:
    # El texto del TODO dice de quién es y qué historia falta, por ejemplo
    # "TODO(Dolores): US-CORE-005 ...". En Swagger se ve qué falta y de quién.
    return respuesta_error(status.HTTP_501_NOT_IMPLEMENTED, str(exc) or None)


async def _manejar_inesperado(request: Request, exc: Exception) -> JSONResponse:
    # El detalle va al log del servidor, NUNCA a la respuesta: un traceback
    # le muestra a un atacante cómo está hecho el sistema.
    logger.exception("Error no manejado en %s %s", request.method, request.url.path)
    return respuesta_error(status.HTTP_500_INTERNAL_SERVER_ERROR)


def registrar_handlers(app: FastAPI) -> None:
    """Conecta los handlers a la app (main.py lo llama una vez)."""
    app.add_exception_handler(StarletteHTTPException, _manejar_http)
    app.add_exception_handler(RequestValidationError, _manejar_validacion)
    app.add_exception_handler(NotImplementedError, _manejar_no_implementado)
    app.add_exception_handler(Exception, _manejar_inesperado)
