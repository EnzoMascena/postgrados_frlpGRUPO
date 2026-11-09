"""Que el token del link de seguimiento no quede en los logs.

El token va en la ruta (`/seguimiento/{token}/...`) y con él se entra al legajo durante 60 días.
En la base se guarda solo su hash (ADR-005); si quedara entero en el log, leer el log alcanzaría
para entrar. Por eso se tapa en los dos lugares donde el back escribe la ruta: el log de accesos
de uvicorn y el log de los errores 500 (`error_handlers.py`).
"""

import logging
import re

# Lo que sigue a `/seguimiento/` hasta la próxima `/`, `?` o `#`. El token es base64 para URL
# (letras, dígitos, `-` y `_`), así que nunca tiene esos caracteres.
_TOKEN_EN_RUTA = re.compile(r"(/seguimiento/)[^/?#\s\"]+")


def tapar_token(texto: str) -> str:
    """`/api/v1/seguimiento/abc123/enviar` → `/api/v1/seguimiento/***/enviar`."""
    return _TOKEN_EN_RUTA.sub(r"\1***", texto)


class FiltroDeTokens(logging.Filter):
    """Tapa el token en el mensaje y en sus argumentos antes de que se escriba la línea.

    uvicorn arma la línea del log de accesos con `%` y pasa la ruta como argumento:
    `'%s - "%s %s HTTP/%s" %d'` con `(cliente, método, ruta, versión, status)`.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = tapar_token(record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(
                tapar_token(arg) if isinstance(arg, str) else arg for arg in record.args
            )
        return True  # nunca descarta la línea: solo la corrige


# Una sola instancia: `addFilter` no la agrega dos veces si se instala de nuevo.
FILTRO_DE_TOKENS = FiltroDeTokens()


def instalar_filtro_de_tokens() -> None:
    """Agrega el filtro al log de accesos de uvicorn. Lo llama `main.py` al crear la app."""
    logging.getLogger("uvicorn.access").addFilter(FILTRO_DE_TOKENS)
