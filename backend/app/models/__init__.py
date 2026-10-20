"""
Modelos de la base: las 13 tablas del sistema (SQLModel).

Solo Enzo modifica este paquete (PLAN_BACKEND, "Modelo de datos"): así
nunca hay dos migraciones de Alembic en paralelo. ¿Necesitás una columna?
Abrí un issue y pedila.

Importar este paquete registra TODAS las tablas en SQLModel.metadata, que
es lo que lee Alembic (alembic/env.py) para generar las migraciones.

Sin Relationship() a propósito: cada repository arma sus consultas (y sus
join) de forma explícita, como en los módulos de la cátedra.
"""

from app.models.graduacion import TrabajoFinal, Tutoria
from app.models.legajo import AuditoriaLegajo, Documento, Legajo
from app.models.oferta import Carrera, Cohorte
from app.models.seminario import AccesoDocente, Asistencia, Clase, Cursada, Seminario
from app.models.usuario import Usuario

__all__ = [
    "AccesoDocente",
    "Asistencia",
    "AuditoriaLegajo",
    "Carrera",
    "Clase",
    "Cohorte",
    "Cursada",
    "Documento",
    "Legajo",
    "Seminario",
    "TrabajoFinal",
    "Tutoria",
    "Usuario",
]
