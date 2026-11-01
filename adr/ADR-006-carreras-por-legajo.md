# ADR-006: Carreras por legajo (BR-001)

**Estado:** Aceptado  
**Fecha:** 30/10/2026  
**Autor:** Enzo Mascena (rol: Líder / Desarrollador principal)  
**Revisores:** Fran Buscaglia (revisor del PR E3)

---

## Contexto

La regla BR-001 del SRS dice que un aspirante puede estar en **como máximo 2 carreras en el mismo período**. En el formulario de inscripción elige 1 o 2 carreras (`carreraIds`). Además, el DNI es único dentro de la cohorte (RF-CORE-001): en una cohorte hay **un solo legajo por persona**.

Hay que decidir cómo se guardan las carreras de un legajo. Queremos que el máximo de 2 lo garantice la base de datos, y no solo el código de la API: si mañana otro endpoint, un script o el seed se equivocan, la base tiene que rechazar el dato.

---

## Opciones Evaluadas

### Opción A: dos columnas en `legajos` (`carrera_1_id` y `carrera_2_id`)
**Descripción:** el legajo tiene dos claves foráneas a `carreras`; la segunda puede ser nula.  
**Ventajas:** no hace falta ninguna tabla más ni ningún join; el máximo de 2 sale de la estructura misma.  
**Desventajas:** filtrar los legajos de una carrera (dashboard y Excel) exige mirar las dos columnas con un `OR`; nada impide poner la misma carrera en las dos si no se agrega otro CHECK; si la regla pasa a 3 carreras hay que agregar columnas y reescribir las consultas; "primera" y "segunda" quedan implícitas en el nombre de la columna.

### Opción B: un legajo por carrera
**Descripción:** si el aspirante elige 2 carreras, se crean 2 legajos.  
**Ventajas:** cada carrera tiene su propio estado y su propio número de legajo; filtrar por carrera es trivial.  
**Desventajas:** choca con el DNI único en la cohorte, que tendría que pasar a ser único por (cohorte, DNI, carrera); duplica los datos personales y los PDFs; el aspirante tendría dos trámites, dos aprobaciones y dos emails para lo que, para él, es una sola inscripción; y BR-001 deja de estar en la base: habría que contar legajos en el código.

### Opción C: tabla `legajo_carreras` con `orden` 1 o 2
**Descripción:** una fila por cada carrera elegida, con la clave primaria `(legajo_id, orden)`, un CHECK `orden IN (1, 2)` y un único `(legajo_id, carrera_id)`.  
**Ventajas:** ver abajo, en Consecuencias.  
**Desventajas:** un join más al leer las carreras de un legajo.

---

## Decisión

"Decidimos usar la **Opción C (tabla `legajo_carreras` con `orden` 1 o 2)** porque deja que sea la base de datos la que garantice BR-001, sin romper el legajo único por persona y cohorte."

---

## Consecuencias

### Positivas
- **El máximo de 2 lo garantiza la base.** La clave primaria `(legajo_id, orden)` junto con `CHECK (orden IN (1, 2))` hace imposible una tercera carrera: no hay un tercer valor de `orden` que se pueda insertar. Hay un test por cada caso en `tests/shared/test_modelo_de_datos.py`.
- **No se repite una carrera.** El único `(legajo_id, carrera_id)` impide elegir dos veces la misma.
- **Se mantiene un legajo por persona y cohorte.** El DNI sigue siendo único en `(cohorte_id, dni)` y el aspirante tiene un solo trámite, con un solo estado, un solo número y un solo conjunto de PDFs.
- **El orden se conserva.** `orden = 1` es la primera opción del aspirante.
- **Filtrar por carrera es un `JOIN` simple** sobre `legajo_carreras`, con un índice natural en la clave primaria.
- **Cambiar la regla es barato.** Pasar a 3 carreras es una migración que cambia un CHECK, sin tocar columnas ni consultas.

### Negativas (trade-offs aceptados)
- Leer las carreras de un legajo requiere un join (o un segundo `SELECT ... IN`). Para el listado y el detalle lo resuelve el repositorio de Luca.
- Las dos carreras comparten el estado del legajo: no se puede aprobar una y rechazar la otra.

### Riesgos y Mitigaciones
| Riesgo | Mitigación |
|--------|-----------|
| La base garantiza el máximo de 2, pero **no el mínimo de 1**: un legajo podría quedar sin ninguna carrera | El caso de uso de inscripción valida que `carreraIds` tenga 1 o 2 carreras distintas y activas, y arma el legajo y sus filas en la misma transacción (F4) |
| Alguien cambia el CHECK de `orden` y `alembic check` no se entera, porque Alembic no detecta cambios en los CHECK | Revisar a mano toda migración que toque restricciones; los tests de `test_modelo_de_datos.py` fallan si el CHECK cambia |
| Una carrera inactiva o borrada queda asociada a un legajo | `legajo_carreras.carrera_id` tiene clave foránea a `carreras`; las carreras no se borran, se desactivan (`activa`) |

---

## Revisión

Esta decisión será revisada en: el planeamiento del módulo especializado (después de v0.5).  
Criterio de revisión: si BR-001 cambia a más de 2 carreras (alcanza con ampliar el CHECK) o si cada carrera pasa a tener su propio estado de admisión, caso en el que la Opción B vuelve a ser la adecuada.
