"""Errores de negocio del sistema. Python puro: no importa FastAPI.

El dominio y los casos de uso levantan estos errores; `error_handlers.py` los convierte en la
respuesta JSON uniforme. Cada módulo hereda de estas clases para sus códigos propios:

    class PeriodoCerrado(Conflicto):
        codigo = "PERIODO_CERRADO"
"""


class ErrorDeNegocio(Exception):
    status_code = 400
    codigo = "BAD_REQUEST"

    def __init__(self, mensaje: str, campo: str | None = None) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.campo = campo


class NoAutenticado(ErrorDeNegocio):
    status_code = 401
    codigo = "UNAUTHORIZED"


class SinPermiso(ErrorDeNegocio):
    status_code = 403
    codigo = "FORBIDDEN"


class NoEncontrado(ErrorDeNegocio):
    status_code = 404
    codigo = "NOT_FOUND"


class Conflicto(ErrorDeNegocio):
    status_code = 409
    codigo = "CONFLICT"


class ErrorDeValidacion(ErrorDeNegocio):
    status_code = 422
    codigo = "VALIDATION_ERROR"
