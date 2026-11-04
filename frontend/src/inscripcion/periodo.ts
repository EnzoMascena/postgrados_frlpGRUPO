/* ═══════════════════════════════════════════════════════════════
   periodo.ts — ¿ESTÁ ABIERTA LA INSCRIPCIÓN? (US-CORE-009)
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Antes el Badge decía "Período abierto" fijo. Ahora lo decide el
   coordinador desde el dashboard (PATCH /cohortes/{id}/inscripcion)
   y el formulario lo lee de GET /cohortes. Estas funciones puras
   dicen qué cohortes aceptan inscripciones y qué mensaje mostrar
   cuando no hay ninguna.

   OJO CON LAS FECHAS: `proximaApertura` es una fecha sin hora
   ("2027-03-01"). Si la pasáramos por new Date(), JavaScript la
   toma como medianoche UTC, que en Argentina (UTC-3) es el 28/02
   a las 21 h: mostraríamos el día anterior. Por eso la armamos
   partiendo el texto, sin Date.
   ═══════════════════════════════════════════════════════════════ */

import type { Cohorte } from '../shared/api/tipos'

/** Las cohortes con el período abierto, en el orden de la API (la más nueva primero). */
export function cohortesAbiertas(cohortes: Cohorte[]): Cohorte[] {
  return cohortes.filter((cohorte) => cohorte.inscripcionAbierta)
}

/** "2027-03-01" → "01/03/2027". */
export function formatearFecha(fechaIso: string): string {
  const [anio, mes, dia] = fechaIso.slice(0, 10).split('-')
  return `${dia}/${mes}/${anio}`
}

/** Hoy en Argentina, como "AAAA-MM-DD" (para comparar con las fechas de la API). */
export function hoyEnArgentina(ahora = new Date()): string {
  // 'sv-SE' es el idioma que escribe las fechas como AAAA-MM-DD.
  return ahora.toLocaleDateString('sv-SE', { timeZone: 'America/Argentina/Buenos_Aires' })
}

/**
 * La próxima apertura más cercana entre las cohortes, sin contar las
 * fechas que ya pasaron. null si ninguna tiene fecha.
 */
export function proximaApertura(cohortes: Cohorte[], hoy = hoyEnArgentina()): string | null {
  const fechas = cohortes
    .map((cohorte) => cohorte.proximaApertura)
    .filter((fecha): fecha is string => fecha !== null && fecha.slice(0, 10) >= hoy)
    .sort() // "AAAA-MM-DD" se ordena bien como texto
  return fechas[0] ?? null
}

/** El mismo mensaje que el 409 PERIODO_CERRADO del back. */
export function mensajeCerrada(fecha: string | null): string {
  const base = 'La inscripción está cerrada.'
  return fecha ? `${base} Próxima apertura: ${formatearFecha(fecha)}` : base
}
