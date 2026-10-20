"""
Excepciones de DOMINIO — lo que lanza un service cuando algo no se puede.

La lección del módulo 03: el service NO sabe de HTTP. No importa FastAPI,
no lanza HTTPException y no elige status codes. Cuando una regla de negocio
no se cumple, lanza una de estas excepciones (Python puro) y el CONTROLLER
decide qué status corresponde:

    # service.py
    if self.repository.existe_dni(cohorte_id, dni):
        raise Conflicto(
            "Ya existe una preinscripción con este DNI para la cohorte actual",
            campo="dni",
        )

    # controller.py
    try:
        return service.crear_borrador(body)
    except Conflicto as error:
        raise ErrorAPI(400, error.mensaje, campo=error.campo) from error

Para "no existe" no hace falta excepción: el service devuelve None y el
controller lo traduce a 404, igual que en el módulo 03.

El mensaje va en español y orientado a la acción (NFR-U02): es lo que el
front le muestra al usuario al lado del campo.
"""


class ErrorDeDominio(Exception):
    """Base de las excepciones de dominio: un mensaje y, si aplica, el campo."""

    def __init__(self, mensaje: str, campo: str | None = None) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.campo = campo


class ReglaDeNegocioViolada(ErrorDeDominio):
    """No se cumple una regla de negocio (BR-xxx, una transición inválida...)."""


class Conflicto(ErrorDeDominio):
    """El dato choca con uno que ya existe (por ejemplo, un DNI repetido)."""


class PermisoDenegado(ErrorDeDominio):
    """Está autenticado, pero no puede hacer esto sobre ESE recurso."""


class ArchivoInvalido(ErrorDeDominio):
    """El archivo subido no es un PDF o supera el tamaño máximo."""
