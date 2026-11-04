/* ═══════════════════════════════════════════════════════════════
   api.ts — LOS PEDIDOS DE LA INSCRIPCIÓN A LA API
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Dos endpoints públicos (plan §10), los dos sin JWT:
     POST /legajos                    → crea el legajo en Borrador
                                        y manda el email con el link
     POST /legajos/recuperar-acceso   → manda un link nuevo

   Acá solo están las funciones que hacen el pedido (con apiFetch,
   nunca fetch suelto) y dos ayudas:
     aPayload(datos, cohorteId) → pasa el estado del formulario
                                  (todo texto) al cuerpo exacto del
                                  contrato ('' opcional → null).
     separarError(error)        → decide dónde se muestra un error
                                  del back: al lado del campo (si
                                  trae `field`) o en una Alerta.
   Los componentes no las llaman directo: usan los hooks de
   hooks/useInscripcion.ts (TanStack Query).
   ═══════════════════════════════════════════════════════════════ */

import { ApiError, apiFetch } from '../shared/api/client'
import type { ComoConocio } from '../shared/api/tipos'
import type {
  CampoInscripcion,
  DatosInscripcion,
  Errores,
  InscripcionPayload,
  RespuestaInscripcion,
  RespuestaRecuperarAcceso,
} from './types'

/** POST /legajos: 201 con el token para ir a /seguimiento/{token}. */
export function inscribir(payload: InscripcionPayload): Promise<RespuestaInscripcion> {
  return apiFetch<RespuestaInscripcion>('/legajos', { method: 'POST', json: payload })
}

/** POST /legajos/recuperar-acceso: siempre 202 con el mismo mensaje, exista o no el email. */
export function recuperarAcceso(email: string): Promise<RespuestaRecuperarAcceso> {
  return apiFetch<RespuestaRecuperarAcceso>('/legajos/recuperar-acceso', {
    method: 'POST',
    json: { email: email.trim() },
  })
}

/** El estado del formulario → el cuerpo de POST /legajos. */
export function aPayload(datos: DatosInscripcion, cohorteId: string): InscripcionPayload {
  const opcional = (valor: string) => (valor.trim() === '' ? null : valor)
  return {
    ...datos,
    cohorteId,
    telefonoFijo: opcional(datos.telefonoFijo),
    tituloPosgrado: opcional(datos.tituloPosgrado),
    // Solo se llama después de validarFormulario, que ya exige una opción.
    comoConocio: datos.comoConocio as ComoConocio,
    tipoBeca: datos.solicitaBeca ? datos.tipoBeca : null,
  }
}

// Los campos que tienen un lugar en pantalla para su error. `solicitaBeca`
// es un checkbox sin mensaje propio, y `cohorteId` no está en el
// formulario: esos errores van a la Alerta de arriba.
const CAMPOS_CON_ERROR: ReadonlySet<string> = new Set<CampoInscripcion>([
  'carreraIds',
  'apellido',
  'nombre',
  'nacionalidad',
  'dni',
  'telefonoMovil',
  'telefonoFijo',
  'email',
  'emailAlternativo',
  'domicilio',
  'ciudad',
  'provincia',
  'pais',
  'tituloGrado',
  'tituloPosgrado',
  'comoConocio',
  'motivacion',
  'tipoBeca',
])

export type ErrorSeparado = {
  /** Para FormularioDatos (erroresServidor): el mensaje al lado de su campo. */
  porCampo: Errores
  /** Para la Alerta de arriba: sin campo, de un campo que no está en pantalla, o sin conexión. */
  general: string | null
}

const SIN_ERROR: ErrorSeparado = { porCampo: {}, general: null }

/** Decide dónde se ve un error del back. */
export function separarError(error: Error | null): ErrorSeparado {
  if (!error) return SIN_ERROR
  if (error instanceof ApiError && error.campo && CAMPOS_CON_ERROR.has(error.campo)) {
    return { porCampo: { [error.campo as CampoInscripcion]: error.mensaje }, general: null }
  }
  return { porCampo: {}, general: error.message }
}

/** true si es el 409 de "ya hay una preinscripción con este email". */
export function esEmailRepetido(error: Error | null): boolean {
  return error instanceof ApiError && error.status === 409 && error.campo === 'email'
}

/** true si la cohorte se cerró mientras el aspirante completaba el formulario. */
export function esPeriodoCerrado(error: Error | null): boolean {
  return error instanceof ApiError && error.codigo === 'PERIODO_CERRADO'
}
