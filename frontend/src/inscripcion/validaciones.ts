/* ═══════════════════════════════════════════════════════════════
   validaciones.ts — LAS REGLAS DEL FORMULARIO (plan §10)
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Son funciones puras: reciben un valor y devuelven el mensaje de
   error, o null si está bien. No tocan React, ni la pantalla, ni
   la API. Por eso se prueban solas y se reusan para crear y para
   editar el legajo.

   ¿Por qué validar acá si el back valida igual?
     - Front: para el aspirante. Ve el error al salir del campo,
       sin esperar a la red (US-CORE-001).
     - Back: para la seguridad. Cualquiera puede saltearse el front
       y llamar a la API directo; el back es la última palabra.
   Las reglas son las mismas en los dos lados. Si el back responde
   un error con `field`, se muestra al lado de ese campo igual.

   Mensajes en español y orientados a la acción (NFR-U02): dicen
   qué hacer, no solo qué está mal.
   ═══════════════════════════════════════════════════════════════ */

import type { CampoInscripcion, DatosInscripcion, Errores } from './types'

/** Lo que devuelve cada regla: el mensaje del error, o null si está bien. */
export type Resultado = string | null

export const MOTIVACION_MINIMA = 50
export const MAXIMO_CARRERAS = 2

// ── Reglas sueltas ─────────────────────────────────────────────

/** Que no esté vacío (los espacios solos cuentan como vacío). */
export function obligatorio(valor: string, mensaje = 'Completá este campo'): Resultado {
  return valor.trim() === '' ? mensaje : null
}

/** Saca puntos y espacios: "28.456 789" → "28456789". El back hace lo mismo. */
export function normalizarDni(valor: string): string {
  return valor.replace(/[.\s]/g, '')
}

/** DNI de 7 u 8 números; acepta puntos y espacios. */
export function validarDni(valor: string): Resultado {
  if (valor.trim() === '') return 'Ingresá tu DNI'
  return /^\d{7,8}$/.test(normalizarDni(valor)) ? null : 'Ingresá un DNI de 7 u 8 números'
}

/** Un email con forma de email: algo@algo.algo, sin espacios. */
export function validarEmail(valor: string, mensajeVacio = 'Ingresá tu email'): Resultado {
  const email = valor.trim()
  if (email === '') return mensajeVacio
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
    ? null
    : 'Ingresá un email válido, por ejemplo nombre@dominio.com'
}

/**
 * Teléfono: al menos 8 números, sin contar espacios, +, guiones ni
 * paréntesis. Sin formato estricto hasta que el back defina el suyo.
 * Si no es obligatorio, vacío está bien.
 */
export function validarTelefono(valor: string, esObligatorio = true): Resultado {
  const telefono = valor.trim()
  if (telefono === '') return esObligatorio ? 'Ingresá tu teléfono móvil' : null
  return /^\d{8,}$/.test(telefono.replace(/[\s+()-]/g, ''))
    ? null
    : 'Ingresá un teléfono de al menos 8 números, con código de área'
}

/** Motivación de 50 caracteres o más (sin contar espacios de los bordes). */
export function validarMotivacion(valor: string): Resultado {
  const largo = valor.trim().length
  if (largo === 0) return `Contanos por qué querés cursar (mínimo ${MOTIVACION_MINIMA} caracteres)`
  const faltan = MOTIVACION_MINIMA - largo
  return faltan > 0
    ? `Escribí al menos ${MOTIVACION_MINIMA} caracteres (te faltan ${faltan})`
    : null
}

/** Una o dos carreras distintas (BR-001). */
export function validarCarreras(ids: string[]): Resultado {
  if (ids.length === 0) return 'Elegí al menos una carrera'
  if (new Set(ids).size !== ids.length) return 'Elegiste la misma carrera dos veces'
  return ids.length > MAXIMO_CARRERAS ? `Podés elegir hasta ${MAXIMO_CARRERAS} carreras` : null
}

/** Si pide beca, tiene que elegir 30% o 100%. */
export function validarBeca(solicitaBeca: boolean, tipoBeca: string | null): Resultado {
  if (!solicitaBeca) return null
  return tipoBeca === '30' || tipoBeca === '100' ? null : 'Elegí el tipo de beca: 30% o 100%'
}

// ── Todo el formulario ─────────────────────────────────────────

/**
 * Valida un solo campo con los datos actuales. La usa el formulario
 * al salir de un campo (onBlur) y mientras se escribe después.
 */
export function validarCampo(campo: CampoInscripcion, datos: DatosInscripcion): Resultado {
  switch (campo) {
    case 'carreraIds':
      return validarCarreras(datos.carreraIds)
    case 'apellido':
      return obligatorio(datos.apellido, 'Ingresá tu apellido')
    case 'nombre':
      return obligatorio(datos.nombre, 'Ingresá tu nombre')
    case 'nacionalidad':
      return obligatorio(datos.nacionalidad, 'Ingresá tu nacionalidad')
    case 'dni':
      return validarDni(datos.dni)
    case 'telefonoMovil':
      return validarTelefono(datos.telefonoMovil)
    case 'telefonoFijo':
      return validarTelefono(datos.telefonoFijo, false)
    case 'email':
      return validarEmail(datos.email)
    case 'emailAlternativo':
      return validarEmail(datos.emailAlternativo, 'Ingresá un email alternativo')
    case 'domicilio':
      return obligatorio(datos.domicilio, 'Ingresá tu domicilio (calle y número)')
    case 'ciudad':
      return obligatorio(datos.ciudad, 'Ingresá tu ciudad')
    case 'provincia':
      return obligatorio(datos.provincia, 'Ingresá tu provincia')
    case 'pais':
      return obligatorio(datos.pais, 'Ingresá tu país')
    case 'tituloGrado':
      return obligatorio(datos.tituloGrado, 'Ingresá tu título de grado')
    case 'comoConocio':
      return datos.comoConocio === '' ? 'Elegí cómo conociste la oferta' : null
    case 'motivacion':
      return validarMotivacion(datos.motivacion)
    case 'tipoBeca':
      return validarBeca(datos.solicitaBeca, datos.tipoBeca)
    case 'tituloPosgrado':
    case 'solicitaBeca':
      return null // opcionales, sin reglas propias
  }
}

/** Valida todo junto (al apretar "Guardar"). Devuelve solo los campos con error. */
export function validarFormulario(datos: DatosInscripcion): Errores {
  const errores: Errores = {}
  for (const campo of Object.keys(datos) as CampoInscripcion[]) {
    const mensaje = validarCampo(campo, datos)
    if (mensaje) errores[campo] = mensaje
  }
  return errores
}

/** true si no hay ningún error. */
export function sinErrores(errores: Errores): boolean {
  return Object.keys(errores).length === 0
}
