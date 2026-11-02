# ADR-004: Máquina de estados del legajo como tabla de transiciones por rol

**Estado:** Aceptado  
**Fecha:** 01/11/2026  
**Autor:** Luca De Paola (rol: Desarrollador Backend)  
**Revisores:** Fran (PR L2), Enzo (revisión de arquitectura)

---

## Contexto

El legajo pasa por 10 estados (BORRADOR, PENDIENTE, EN_REVISION, OBSERVADO, COMPLETADO, ACTIVO, VENCIDO, RECHAZADO, BAJA, GRADUADO) y lo mueven tres actores distintos: el aspirante (ENVIAR y CORREGIR), el coordinador (revisar, observar, aprobar, rechazar, matricular, dar de baja) y el sistema (VENCER, con la tarea diaria de E6). US-CORE-005 pide que las transiciones sigan estrictamente el diagrama del SRS (RF-CORE-003), que cada rol haga solo las suyas y que cada cambio quede auditado. Tres módulos dependen de la misma regla: el envío de Fran, el detalle de Loli (que muestra los botones según `accionesPermitidas`) y el vencimiento de Enzo. ARQUITECTURA §2 exige además que la validación de transiciones se pruebe con tests unitarios de milisegundos, sin base ni servidor.

---

## Opciones Evaluadas

### Opción A: Tabla de transiciones por rol en `domain/`
**Descripción:** un diccionario `TRANSICIONES: dict[Accion, Transicion]` en `src/legajos/domain/estados.py`, donde cada `Transicion` dice desde qué estados se puede hacer la acción, a qué estado lleva y qué roles la pueden hacer. `validar_transicion(estado, accion, rol)` y `acciones_permitidas(estado, rol)` consultan esa tabla.  
**Ventajas:** la regla entera se lee en 10 líneas y coincide fila por fila con la tabla del plan §9; cambiar una transición es cambiar una línea; `acciones_permitidas` sale gratis de la misma tabla (no hay una segunda lista que se desincronice); es Python puro, así que se testea con `parametrize` todas las combinaciones (10 acciones × 10 estados × 6 roles) en milisegundos.  
**Desventajas:** los efectos de cada acción (fechas, número de legajo, email) no entran en la tabla y hay que resolverlos aparte, en `ServicioEstados`.

### Opción B: Un `if` por acción en el service
**Descripción:** en el caso de uso, un bloque por acción: `if accion == "APROBAR": if legajo.estado != "EN_REVISION": raise …; if rol != "COORDINADOR": raise …`, como en el service de la cátedra (módulo 03).  
**Ventajas:** es lo que el equipo ya conoce; no hay estructuras nuevas.  
**Desventajas:** la regla queda repartida en 10 bloques mezclados con la base y los emails; es fácil que un bloque valide el estado antes que el rol y otro al revés; para `acciones_permitidas` habría que repetir las condiciones en otra función; y testearlo pide armar el service con todas sus dependencias.

### Opción C: Una librería de máquinas de estado (`transitions`, `python-statemachine`)
**Descripción:** declarar estados y transiciones con la API de la librería, que trae callbacks para los efectos y diagramas generados.  
**Ventajas:** resuelve casos más complejos (estados anidados, guardas, callbacks); dibuja el diagrama.  
**Desventajas:** una dependencia más para una tabla de 10 filas; no maneja roles de fábrica (habría que sumarlos como guardas); la librería quiere ser dueña del objeto (se "monta" sobre la entidad), lo que choca con un dominio de dataclasses puras; y el equipo tendría que aprenderla en una semana.

---

## Decisión

"Decidimos usar **la opción A: una tabla de transiciones por rol en `src/legajos/domain/estados.py`**, porque deja la regla del plan §9 escrita una sola vez, como datos, y se prueba completa sin base."

### Cómo queda

| Acción | De → a | Rol |
| --- | --- | --- |
| ENVIAR | BORRADOR → PENDIENTE | ASPIRANTE |
| REVISAR | PENDIENTE → EN_REVISION | COORDINADOR |
| OBSERVAR | EN_REVISION → OBSERVADO | COORDINADOR |
| CORREGIR | OBSERVADO → PENDIENTE | ASPIRANTE |
| APROBAR | EN_REVISION → COMPLETADO | COORDINADOR |
| RECHAZAR | EN_REVISION → RECHAZADO | COORDINADOR |
| MATRICULAR | COMPLETADO → ACTIVO | COORDINADOR |
| VENCER | COMPLETADO → VENCIDO | SISTEMA |
| GRADUAR | ACTIVO → GRADUADO | SISTEMA (queda para el módulo C; en el Core no se dispara) |
| DAR_DE_BAJA | ACTIVO → BAJA | COORDINADOR |

- **Orden de validación:** primero el rol y después el estado. Si el rol no puede hacer la acción → 403 `FORBIDDEN` ("No tenés permiso para esta acción"); si el estado no corresponde → 409 `TRANSICION_INVALIDA` ("No se puede APROBAR un legajo en estado PENDIENTE"). Validar el rol primero evita que alguien sin permiso averigüe en qué estado está un legajo probando acciones. En los dos casos no cambia nada.
- **Comentario:** OBSERVAR exige un comentario de 5 caracteres o más (sin contar espacios) → si no, 422 con `field: "comentario"`. En RECHAZAR y DAR_DE_BAJA es opcional (`validar_comentario`).
- **Botones del front:** `acciones_permitidas(estado, rol)` recorre la misma tabla; el detalle del coordinador la devuelve como `accionesPermitidas` (L3).
- **Reglas vecinas, también en `domain/`:** el número de legajo `AA-CCC-SSS` (`numero_legajo.py`) y la regla de vencimiento de 30 días de BR-005 (`vencimiento.py`, que usa E6). Son funciones puras: el secuencial y la hora actual llegan por parámetro.

### Defensa en tres capas

1. **Dominio:** la tabla decide qué transición es válida. Es la única regla.
2. **Aplicación:** `ServicioEstados.cambiar(legajo_id, accion, actor, comentario)` (L3) es el único lugar que cambia `legajos.estado`: valida con la tabla, aplica los efectos del plan §9, guarda el legajo y su fila de `auditoria_legajos` en un solo `commit` y recién después manda el email. Lo usan el coordinador (`PATCH /legajos/{id}/estado`), el aspirante (envío y corrección de Fran) y el sistema (vencimiento de Enzo, con `Actor(Rol.SISTEMA)`).
3. **Base:** el CHECK `ck_legajos_estado` (migración inicial de Enzo) rechaza cualquier valor que no sea uno de los 10 estados, aunque alguien escriba la tabla a mano o un bug se saltee el servicio. El CHECK no conoce las transiciones (eso solo lo sabe el dominio), pero garantiza que el estado guardado siempre exista.

---

## Consecuencias

### Positivas
- La tabla del código, la del plan §9 y la del ADR son la misma; el test la compara contra una copia escrita a mano del plan, así un cambio sin querer en el código hace fallar el test.
- Los 182 casos de `tests/legajos/test_estados.py` corren en 0,05 s, sin base.
- El front no repite la regla: pide `accionesPermitidas` y muestra esos botones.
- Toda transición queda auditada (quién, con qué rol, de qué estado a cuál, cuándo y con qué comentario), porque no hay otro camino que `ServicioEstados`.

### Negativas (trade-offs aceptados)
- Cada transición tiene un solo estado de origen y un solo rol; la estructura (`frozenset`) admite varios, pero hoy no se usa. Si mañana el ADMIN también puede aprobar, alcanza con sumarlo al `frozenset`.
- Los efectos de cada acción viven en `ServicioEstados` y no en la tabla: para entender una acción completa hay que mirar los dos lugares.
- El CHECK de la base no impide una transición inválida hecha con SQL a mano (por ejemplo, de BORRADOR a ACTIVO); eso solo lo frena el servicio.

### Riesgos y Mitigaciones
| Riesgo | Mitigación |
|--------|-----------|
| Alguien cambia `legajos.estado` sin pasar por el servicio (y queda sin auditoría ni email) | Regla del plan §4 y de este ADR; en las revisiones de F (envío) y E6 (vencimiento) se controla que llamen a `ServicioEstados` |
| La tabla del código se desvía del plan | El test compara contra la tabla del plan escrita a mano, con todas las combinaciones de acción, estado y rol |
| Un nuevo estado en `EstadoLegajo` sin migración | El modelo arma el CHECK desde el enum, pero la migración tiene la lista escrita y `alembic check` no compara CHECK constraints: sumar un estado exige una migración nueva hecha a mano que reemplace `ck_legajos_estado` (si no, la base lo rechaza al guardar) |
| El coordinador ve un botón que después da 409 (el estado cambió mientras miraba) | El 409 trae un mensaje claro y el front recarga el detalle |

---

## Revisión

Esta decisión será revisada en: el módulo C (seguimiento y graduación), cuando GRADUAR se dispare de verdad.  
Criterio de revisión: si aparecen transiciones con condiciones que dependen de datos (por ejemplo, graduar solo con la tesis aprobada) o estados anidados, conviene evaluar guardas en la tabla o la opción C.
