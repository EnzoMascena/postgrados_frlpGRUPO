# ADR-007: Tarea de vencimiento dentro del proceso de la API

**Estado:** Aceptado  
**Fecha:** 06/11/2026  
**Autor:** Enzo Mascena (rol: Líder / Desarrollador principal)  
**Revisores:** Luca De Paola (revisor del PR de E6)

---

## Contexto

La regla BR-005 (US-CORE-010) dice que un legajo COMPLETADO tiene **30 días corridos desde la aprobación** para matricularse. Cumplidos, pasa a VENCIDO, queda auditado y se avisa a cada coordinador activo. A diferencia de las otras acciones, a esta no la dispara una persona: la dispara el paso del tiempo. Hace falta algo que la corra solo todos los días.

Lo que pesa en la elección:

- **El Core se entrega el 10/11/2026** y `docker compose up` tiene que seguir levantando todo con un solo comando.
- **El cambio tiene que pasar por `ServicioEstados`** (plan §9), el único lugar que cambia `legajos.estado`: así se valida la transición, queda la auditoría y sale el email, igual que en cualquier otra acción.
- **La demo tiene que poder mostrarlo en el momento** (hito 3: "vencimiento con el comando manual"): el seed deja un legajo COMPLETADO aprobado hace 31 días para eso.

---

## Opciones Evaluadas

### Opción A: APScheduler dentro del proceso de la API, más un comando manual
**Descripción:** un `BackgroundScheduler` que se arranca en el `lifespan` de FastAPI y corre la tarea todos los días a las 3:00. El mismo código se corre a mano con `python -m`.  
**Ventajas:** ningún servicio nuevo en el compose; usa el mismo código, la misma configuración y la misma conexión que la API; la zona horaria la maneja el disparador.  
**Desventajas:** corre solo mientras la API está levantada; si la API tuviera varios procesos, correría una vez por proceso.

### Opción B: cron en un contenedor aparte que corre el comando
**Descripción:** un servicio más en el compose, con cron, que a las 3:00 ejecuta el comando de la Opción A.  
**Ventajas:** no depende de que la API esté levantada; corre una sola vez aunque la API tenga varios procesos.  
**Desventajas:** un contenedor más, con su imagen, su zona horaria y las variables de entorno duplicadas; usar el cron de la máquina no sirve, porque cada uno trabaja en un sistema distinto (Linux y Windows).

### Opción C: Celery beat (o RQ) con Redis
**Descripción:** una cola de tareas con un programador.  
**Ventajas:** reintentos, monitoreo y escala.  
**Desventajas:** dos servicios nuevos (el broker y el worker) para una tarea por día; desproporcionado para el tamaño del Core.

### Opción D: pg_cron en PostgreSQL
**Descripción:** la base misma corre un `UPDATE` todos los días.  
**Ventajas:** no depende de la API.  
**Desventajas:** la lógica quedaría en SQL, fuera de `ServicioEstados`: sin la validación de la transición ni el email; además, pg_cron no viene en la imagen `postgres:16-alpine`.

---

## Decisión

"Decidimos usar la **Opción A (APScheduler dentro del proceso de la API, más un comando para correrla a mano)** porque es la única que no agrega servicios y hace que el vencimiento pase por el mismo `ServicioEstados` que cualquier otro cambio de estado."

| Pieza | Dónde |
| --- | --- |
| La regla: 30 días o más desde la aprobación | `reserva_vencida` en `src/legajos/domain/vencimiento.py` (Luca, L2) |
| El caso de uso | `vencer_reservas` en `src/legajos/application/vencer_reservas.py` |
| La consulta, la tarea y el comando | `src/legajos/infrastructure/job_vencimiento.py` |
| El arranque y el apagado | `lifespan` de `backend/main.py` (con `ENVIRONMENT=testing` no se programa) |
| Correrla a mano | `uv run python -m src.legajos.infrastructure.job_vencimiento` |

---

## Consecuencias

### Positivas
- **Mismo camino que el resto.** VENCER pasa por `ServicioEstados` con `Actor(Rol.SISTEMA)`: se valida la transición, la auditoría queda con rol SISTEMA y sin usuario, y cada coordinador activo recibe `vencimiento_coordinador`.
- **La regla está en un solo lugar.** La consulta trae todos los COMPLETADO y el caso de uso decide con `reserva_vencida`; la tarea no repite el cálculo de los 30 días.
- **Es idempotente.** Un legajo vencido deja de ser COMPLETADO, así que correrla dos veces seguidas no vence ni avisa dos veces. Lo comprueba `tests/legajos/test_job_vencimiento.py`.
- **Se corrige sola.** Como la regla es "30 días o más", si un día no corre (la API estaba apagada a las 3:00) la corrida siguiente o el comando toman ese legajo: vence con un día de atraso, pero no se pierde.
- **Hora de Argentina.** El disparador usa `ZONA_HORARIA` (`America/Argentina/Buenos_Aires`), no la hora del servidor.

### Negativas (trade-offs aceptados)
- **Corre solo con la API levantada, y a propósito no se pone al día al arrancar:** si corriera al arrancar, `docker compose up` vencería el legajo de la demo antes de poder mostrarlo.
- **Un solo proceso.** Con varios workers (`uvicorn --workers N`) correría N veces a las 3:00. Hoy `start.sh` levanta un solo proceso.
- **Precisión de un día.** La regla compara instantes: un legajo aprobado a las 15:00 cumple los 30 días a las 15:00, y lo vence la corrida de las 3:00 del día siguiente.
- **La agenda no se guarda.** El programador vive en memoria y se arma de nuevo en cada arranque; no hace falta guardarla porque la tarea es idempotente.
- **APScheduler saltea, por defecto, una corrida que arranca más de 1 segundo tarde.** Se le da una hora de margen (`misfire_grace_time=3600`) para que un proceso ocupado no pierda el día.

### Riesgos y Mitigaciones
| Riesgo | Mitigación |
|--------|-----------|
| La API pasa a tener varios procesos y la tarea corre varias veces a la vez | Mover la tarea a su propio proceso con el mismo comando (Opción B), o tomar un `pg_try_advisory_lock` al empezar la corrida |
| Un coordinador matricula el legajo mientras corre la tarea | Si la matrícula entra antes, la tarea recibe `TransicionInvalida`, lo saltea y sigue con los demás (hay test). Queda una ventana de milisegundos, entre que la tarea lee y guarda, en la que gana el último que guarda: a las 3:00 es improbable, y cerrarla exige que `ServicioEstados` bloquee la fila al leerla (`FOR UPDATE`) |
| La API está apagada a las 3:00 | La corrida siguiente lo toma (la regla es "30 o más") y para la demo está el comando |
| Falla el servidor de correo | El estado y la auditoría quedan guardados igual: `ServicioEstados` avisa después del commit, y `enviar_email` deja el error en el log |
| Se cae la base en medio de la corrida | Los legajos ya vencidos quedan guardados (cada uno tiene su commit); el resto lo toma la corrida siguiente |

---

## Revisión

Esta decisión será revisada si la API pasa a correr en más de un proceso o servidor, o si aparecen más tareas programadas.  
Criterio de revisión: con más de un proceso, la tarea se muda a un proceso propio (Opción B) para que corra una sola vez.
