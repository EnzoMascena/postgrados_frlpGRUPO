/* formato.ts — Cómo se muestran fechas y tamaños en el detalle del legajo.
   La API manda las fechas en UTC ("2026-11-03T14:20:00Z"); acá se
   muestran en hora de Argentina, sin importar en qué zona esté la
   computadora del coordinador. */

const ZONA = 'America/Argentina/Buenos_Aires'

/** "2026-11-03T14:20:00Z" → "03/11/2026". */
export function fecha(utc: string): string {
  return new Date(utc).toLocaleDateString('es-AR', {
    timeZone: ZONA,
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

/** "2026-11-03T14:20:00Z" → "03/11/2026 11:20". */
export function fechaHora(utc: string): string {
  const hora = new Date(utc).toLocaleTimeString('es-AR', {
    timeZone: ZONA,
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
  return `${fecha(utc)} ${hora}`
}

/** 245760 → "240 KB"; 1572864 → "1,5 MB". */
export function tamanio(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`
  return `${(bytes / (1024 * 1024)).toLocaleString('es-AR', { maximumFractionDigits: 1 })} MB`
}
