/* ═══════════════════════════════════════════════════════════════
   fechas.ts — FECHAS DEL LEGAJO EN HORA ARGENTINA
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   El back manda las fechas en UTC ("2026-11-04T02:30:00Z"). Si
   las mostráramos tal cual, una aprobación del 3/11 a las 23:30
   de La Plata se vería como del 4/11. Por eso siempre las pasamos
   por toLocaleDateString con la zona de Buenos Aires.

   FECHA LÍMITE PARA MATRICULARSE (BR-005): la reserva de la
   vacante vence a los 30 días corridos desde la aprobación. Se
   suman sobre el instante en UTC (30 × 24 h), igual que hace el
   back en legajos/domain/vencimiento.py; Argentina no tiene
   horario de verano, así que no hay días de 23 o 25 horas.
   Si el plazo ya pasó pero el legajo sigue en Completado (la tarea
   de vencimiento corre una vez por día), el aviso lo dice en vez
   de mostrar una fecha que ya pasó como si fuera futura.
   ═══════════════════════════════════════════════════════════════ */

const ZONA = 'America/Argentina/Buenos_Aires'
const DIAS_PARA_MATRICULARSE = 30
const UN_DIA_MS = 24 * 60 * 60 * 1000

/** "2026-11-04T02:30:00Z" → "03/11/2026" (en hora argentina). */
export function fechaArgentina(fechaUtc: string): string {
  return new Date(fechaUtc).toLocaleDateString('es-AR', {
    timeZone: ZONA,
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

function instanteLimite(fechaAprobacionUtc: string): number {
  return new Date(fechaAprobacionUtc).getTime() + DIAS_PARA_MATRICULARSE * UN_DIA_MS
}

/** Hasta cuándo puede matricularse: la aprobación + 30 días, en hora argentina. */
export function fechaLimiteMatricula(fechaAprobacionUtc: string): string {
  return fechaArgentina(new Date(instanteLimite(fechaAprobacionUtc)).toISOString())
}

/**
 * true si ya pasaron los 30 días. Puede pasar que el legajo siga en
 * Completado unas horas: la tarea que lo pasa a Vencido corre una vez por día.
 */
export function plazoMatriculaVencido(fechaAprobacionUtc: string, ahora = Date.now()): boolean {
  return ahora >= instanteLimite(fechaAprobacionUtc)
}
