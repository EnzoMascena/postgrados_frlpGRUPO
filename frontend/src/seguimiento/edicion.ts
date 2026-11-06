/* ═══════════════════════════════════════════════════════════════
   edicion.ts — DEL LEGAJO AL FORMULARIO (EDITAR MIS DATOS)
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   El formulario de la inscripción (FormularioDatos) se reusa para
   editar. Pero el legajo que manda el back y el estado del
   formulario no tienen la misma forma:
     · el back manda null en lo opcional; el formulario usa ''
       porque un <input> siempre trabaja con texto
     · el back manda las carreras como objetos; el formulario
       guarda solo sus ids (los checkboxes)
   Esta función pura hace esa traducción. La vuelta (formulario →
   cuerpo del PUT) es aCuerpo() de inscripcion/api.ts, la misma
   que usa la inscripción: un solo lugar decide qué va como null.
   ═══════════════════════════════════════════════════════════════ */

import type { LegajoDetalle } from '../shared/api/tipos'
import type { DatosInscripcion } from '../inscripcion/types'

/** Los datos actuales del legajo, como valores iniciales de FormularioDatos. */
export function datosDesdeLegajo(legajo: LegajoDetalle): DatosInscripcion {
  return {
    carreraIds: legajo.carreras.map((c) => c.id),
    apellido: legajo.apellido,
    nombre: legajo.nombre,
    nacionalidad: legajo.nacionalidad,
    dni: legajo.dni,
    telefonoMovil: legajo.telefonoMovil,
    telefonoFijo: legajo.telefonoFijo ?? '',
    email: legajo.email,
    emailAlternativo: legajo.emailAlternativo,
    domicilio: legajo.domicilio,
    ciudad: legajo.ciudad,
    provincia: legajo.provincia,
    pais: legajo.pais,
    tituloGrado: legajo.tituloGrado,
    tituloPosgrado: legajo.tituloPosgrado ?? '',
    comoConocio: legajo.comoConocio,
    motivacion: legajo.motivacion,
    solicitaBeca: legajo.solicitaBeca,
    tipoBeca: legajo.solicitaBeca ? legajo.tipoBeca : null,
  }
}
