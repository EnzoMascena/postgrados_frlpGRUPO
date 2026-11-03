# ADR-001: Stack tecnológico del Core

**Estado:** Aceptado  
**Fecha:** 02/11/2026  
**Autor:** Enzo Mascena (rol: Líder / Desarrollador principal)  
**Revisores:** Dolores Goñi (revisora del PR de E5)

---

## Contexto

Hay que elegir con qué se construye el Módulo Core antes de que los cinco escribamos código en paralelo. La cátedra sugiere un stack en el README y pide un RFC aprobado para cambiarlo. Lo que pesa en la elección:

- **El Core se entrega el 10/11/2026** y cada módulo tiene un dueño distinto: el stack tiene que ser simple de levantar y de entender para todos.
- **`docker compose up` desde un clon limpio tiene que dejar todo andando** (base, back, front y MailHog), y la misma versión de cada dependencia tiene que instalarse en todas las máquinas y en el CI.
- **Las reglas del negocio tienen que vivir en la base y en el código**: la máquina de estados del legajo, el máximo de 2 carreras por legajo (BR-001, ADR-006), el DNI único por cohorte. No alcanza con validarlas solo en la API.
- **El contrato de la API se documenta con Swagger** (DoD) y los tests tienen que correr contra la misma base que producción, con cobertura de al menos 70 %.
- **El front de la 2.ª entrega ya está hecho en React**, y `develop` partió de esa entrega.

---

## Opciones Evaluadas

### Backend: Opción A — Python 3.12 + FastAPI + SQLModel (SQLAlchemy 2) + Alembic
**Descripción:** FastAPI con Pydantic para validar la entrada y generar Swagger, SQLModel para declarar las tablas, Alembic para las migraciones.  
**Ventajas:** Swagger sale solo de los schemas; Pydantic valida la entrada; la lógica de negocio queda en Python puro, sin depender del framework; SQLAlchemy 2 es el estándar maduro de Python y Alembic migra sobre él; pytest con fixtures sirve para aislar cada test con un rollback.  
**Desventajas:** el back y el front quedan en dos lenguajes distintos, sin tipos compartidos; SQLModel es una capa fina y joven sobre SQLAlchemy (versión 0.0.x) y a veces hay que bajar a SQLAlchemy.

### Backend: Opción B — Node.js + NestJS + Prisma
**Descripción:** es la alternativa que la cátedra lista en el README.  
**Ventajas:** un solo lenguaje (TypeScript) en todo el proyecto; estructura por módulos; Prisma genera tipos.  
**Desventajas:** más código de estructura (módulos, decoradores, DTOs) para un plazo de dos semanas; Swagger se agrega con un plugin; el stack que la cátedra marca como recomendado es el de la Opción A.

### ORM: Opción A2 — SQLAlchemy 2 con modelos y schemas escritos por separado
**Descripción:** las tablas se declaran con SQLAlchemy puro y los schemas de la API con Pydantic.  
**Ventajas:** una capa menos; no depende de una librería 0.0.x.  
**Desventajas:** más texto por cada tabla (columnas escritas con `Mapped` y `mapped_column`); en el Core, igual, los schemas de la API son aparte de las tablas (ver Consecuencias), así que la ventaja de SQLModel no es unificar los dos modelos sino escribir menos en cada tabla.

### Base de datos: Opción C — SQLite
**Descripción:** un archivo en disco, sin servidor.  
**Ventajas:** no hace falta un contenedor.  
**Desventajas:** no tiene `SELECT … FOR UPDATE`, que el número de legajo necesita para bloquear la fila de la cohorte; no cambia restricciones con `ALTER`, que Alembic usa para migrar; y los tests no correrían contra el mismo motor que el sistema real.

### Front: React 19 + TypeScript + Vite (sin alternativa)
**Descripción:** es lo que ya tiene la entrega del front, junto con Tailwind 4, TanStack Query 5 y React Router 8.  
**Ventajas:** no se rehace nada.  
**Desventajas:** React Router 8 exige Node 22.22 o más nuevo.

---

## Decisión

"Decidimos usar **FastAPI + SQLModel/Alembic sobre PostgreSQL 16** para el back y **React 19 + TypeScript + Vite** para el front, con **uv** y **npm** para las dependencias, porque Swagger, la validación y las migraciones salen del mismo stack, y porque las reglas del negocio las puede garantizar la base de datos, que es la misma en los tests, en Docker y en el CI."

Las versiones que quedan fijadas en los archivos de bloqueo:

| Parte | Versión | Dónde se fija |
| --- | --- | --- |
| Python | 3.12 | `backend/.python-version`, imagen `python:3.12-slim` |
| FastAPI / Pydantic | 0.162 / 2.14 | `backend/uv.lock` |
| SQLModel / SQLAlchemy | 0.0.48 / 2.1 | `backend/uv.lock` |
| Alembic / psycopg | 1.20 / 3.3 | `backend/uv.lock` |
| PostgreSQL | 16 | `docker-compose.yml` (`postgres:16-alpine`), servicio del CI |
| React / TypeScript / Vite | 19.2 / 6.0 / 8.1 | `frontend/package-lock.json` |
| Node | 22.22 o más nuevo | imagen `node:22-alpine`, job del front del CI |

---

## Consecuencias

### Positivas
- **Swagger sale del código.** `/api/docs` se arma con los schemas, así que el contrato no se desactualiza respecto de los endpoints.
- **La capa de dominio no conoce el framework.** `domain/` y `application/` son Python puro. SQLModel solo aparece en `infrastructure/orm_models.py`, y los schemas de la API son clases aparte (`CamelModel`), así que cambiar una tabla no cambia el JSON de la API.
- **La base hace cumplir las reglas.** Las 8 tablas tienen 22 restricciones con nombre (`uq_*`, `ck_*`) y `tests/shared/test_modelo_de_datos.py` comprueba cada una por su nombre. Los tests corren sobre PostgreSQL 16 real, con un rollback por test.
- **Todos instalamos lo mismo.** `uv.lock` y `package-lock.json` fijan las versiones; el CI usa `uv sync --locked` y `npm ci`, y el Dockerfile instala con los mismos comandos.
- **Un solo comando levanta todo.** `docker compose up --build` arma las cuatro piezas, migra y carga el seed.

### Negativas (trade-offs aceptados)
- **Dos lenguajes, sin tipos compartidos.** El contrato de la API se copia a mano en `frontend/src/shared/api/tipos.ts`. Si un campo cambia en el back, hay que cambiarlo ahí.
- **SQLModel obliga a bajar a SQLAlchemy.** Las columnas de texto largo y de fecha con zona horaria se declaran con `sa_column` (`columna_fecha` en `src/shared/orm.py`), y las claves primarias compuestas necesitan `sa_column_kwargs`. Además, un modelo `table=True` no valida al construirse: la validación de los datos está en los schemas de la API y en las restricciones de la base.
- **Alembic no detecta los cambios de CHECK.** Si se modifica un `CheckConstraint`, `alembic revision --autogenerate` no lo ve y hay que escribir la migración a mano. Lo cubren los tests del modelo de datos, que comprueban cada restricción por su nombre.
- **Sesiones síncronas.** Usamos `Session` de SQLAlchemy con psycopg 3 y endpoints `def`: FastAPI los corre en un pool de hilos. Alcanza para la carga del TP, pero no es la variante `async` que el README menciona como opcional.

### Riesgos y Mitigaciones
| Riesgo | Mitigación |
|--------|-----------|
| SQLModel 0.0.x cambia de comportamiento al actualizarlo | La versión está fijada en `uv.lock`; solo las tablas dependen de SQLModel, y el CI corre `alembic check` y toda la suite |
| Node más viejo que 22.22 en una máquina: `npm` avisa `EBADENGINE` y el front puede no arrancar | El README pide Node 22.22 o más nuevo y da el comando de instalación |
| Un PostgreSQL local ocupa el puerto 5432 y el back se conecta a ese en vez de al contenedor | El README explica cómo frenarlo o cambiar `DB_PORT` |

---

## Revisión

Esta decisión será revisada al empezar el módulo especializado de cada equipo, después de la entrega del Core.  
Criterio de revisión: si el módulo necesita algo que el stack no da (por ejemplo, un volumen de consultas que haga insuficientes las sesiones síncronas), se abre un RFC como pide la cátedra.
