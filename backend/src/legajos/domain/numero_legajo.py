"""Número de legajo `AA-CCC-SSS` (plan §9). Python puro.

El secuencial lo calcula el repositorio (el mayor ya usado en la cohorte más 1, con la fila de la
cohorte bloqueada); acá solo se arma el texto.
"""

MINIMO = 1
MAXIMO = 999


def generar_numero_legajo(anio: int, numero_cohorte: int, secuencial: int) -> str:
    """Arma el número: año en dos dígitos, cohorte y secuencial en tres. `(2026, 1, 45)` → `26-001-045`.

    Un número de cohorte o un secuencial fuera de 1 a 999 es un error de programación (la base ya
    lo impide para la cohorte), por eso levanta `ValueError` y no un error de negocio.
    """
    if not MINIMO <= numero_cohorte <= MAXIMO:
        raise ValueError(f"El número de cohorte tiene que estar entre 1 y 999: {numero_cohorte}")
    if not MINIMO <= secuencial <= MAXIMO:
        raise ValueError(f"El secuencial tiene que estar entre 1 y 999: {secuencial}")
    return f"{anio % 100:02d}-{numero_cohorte:03d}-{secuencial:03d}"
