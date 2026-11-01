/* ═══════════════════════════════════════════════════════════════
   types.ts — LOS DATOS DEL FORMULARIO DE INSCRIPCIÓN
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   En la entrega 2 el formulario no guardaba nada: cada input era
   HTML suelto. Ahora cada campo es estado de React, y este archivo
   dice qué forma tiene ese estado.

   Hay dos tipos parecidos a propósito:
     DatosInscripcion   → lo que tiene el formulario en memoria.
                          Todo es texto ('' = vacío), porque un
                          <input> siempre trabaja con texto.
     InscripcionPayload → lo que viaja a POST /legajos (plan §10).
                          Lo opcional vacío va como null y se suma
                          la cohorte, que no se elige en el form.
   Separarlos deja al formulario simple y al contrato exacto.
   ═══════════════════════════════════════════════════════════════ */

import type { ComoConocio, EstadoLegajo, TipoBeca } from '../shared/api/tipos'

/** El estado del formulario (FormularioDatos). Se usa para crear y para editar. */
export type DatosInscripcion = {
  carreraIds: string[]
  apellido: string
  nombre: string
  nacionalidad: string
  dni: string
  telefonoMovil: string
  telefonoFijo: string // opcional: '' si no tiene
  email: string
  emailAlternativo: string
  domicilio: string
  ciudad: string
  provincia: string
  pais: string
  tituloGrado: string
  tituloPosgrado: string // opcional: '' si no tiene
  comoConocio: ComoConocio | '' // '' hasta que elige una opción
  motivacion: string
  solicitaBeca: boolean
  tipoBeca: TipoBeca | null
}

/** Un campo del formulario: 'dni', 'email', 'carreraIds', etc. */
export type CampoInscripcion = keyof DatosInscripcion

/** Un mensaje por campo con error. Si un campo no está, está bien. */
export type Errores = Partial<Record<CampoInscripcion, string>>

/** El cuerpo de POST /legajos, tal cual el plan §10. */
export type InscripcionPayload = Omit<
  DatosInscripcion,
  'telefonoFijo' | 'tituloPosgrado' | 'comoConocio'
> & {
  cohorteId: string
  telefonoFijo: string | null
  tituloPosgrado: string | null
  comoConocio: ComoConocio
}

/** La respuesta 201 de POST /legajos. Con el token se navega a /seguimiento/{token}. */
export type RespuestaInscripcion = {
  legajoId: string
  codigoSeguimiento: string
  token: string
  estado: EstadoLegajo
}

/** Las opciones del desplegable "¿Cómo conoció la oferta?" (mismas etiquetas que el back). */
export const OPCIONES_COMO_CONOCIO: ReadonlyArray<{ valor: ComoConocio; etiqueta: string }> = [
  { valor: 'SITIO_WEB_UTN', etiqueta: 'Sitio web UTN FRLP' },
  { valor: 'OTROS_SITIOS', etiqueta: 'Otros sitios web' },
  { valor: 'EGRESADOS', etiqueta: 'Egresados de la UTN FRLP' },
  { valor: 'COLEGAS', etiqueta: 'Comentarios de colegas' },
  { valor: 'OTROS', etiqueta: 'Otros' },
]

/** El formulario recién abierto, sin nada cargado. */
export const DATOS_VACIOS: DatosInscripcion = {
  carreraIds: [],
  apellido: '',
  nombre: '',
  nacionalidad: '',
  dni: '',
  telefonoMovil: '',
  telefonoFijo: '',
  email: '',
  emailAlternativo: '',
  domicilio: '',
  ciudad: '',
  provincia: '',
  pais: '',
  tituloGrado: '',
  tituloPosgrado: '',
  comoConocio: '',
  motivacion: '',
  solicitaBeca: false,
  tipoBeca: null,
}
