"""El `domain/` de legajos no depende de frameworks (plan §7, ARQUITECTURA §2.1).

Lee los imports de cada archivo sin ejecutarlo: si alguno importa FastAPI, SQLModel, SQLAlchemy o
la infraestructura, este test falla antes de que lo note la revisión del PR.
"""

import ast
from pathlib import Path

import pytest

CARPETA_DOMINIO = Path(__file__).parents[2] / "src" / "legajos" / "domain"
PROHIBIDOS = ("fastapi", "sqlmodel", "sqlalchemy", "pydantic")


def _modulos_importados(archivo: Path) -> set[str]:
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    modulos: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            modulos.update(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            modulos.add(nodo.module)
    return modulos


@pytest.mark.parametrize(
    "archivo", sorted(CARPETA_DOMINIO.glob("*.py")), ids=lambda archivo: archivo.name
)
def test_el_dominio_no_importa_frameworks_ni_infraestructura(archivo):
    importados = _modulos_importados(archivo)

    prohibidos = {m for m in importados if m.split(".")[0] in PROHIBIDOS or ".infrastructure" in m}
    assert prohibidos == set(), f"{archivo.name} importa {sorted(prohibidos)}"
