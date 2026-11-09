/* ═══════════════════════════════════════════════════════════════
   envio.ts — CUÁNDO PUEDE ENVIAR EL ASPIRANTE (US-CORE-004)
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Solo desde Borrador (enviar) u Observado (reenviar la
   corrección), que son justo los estados en que el back manda
   `puedeEditar: true`. En los demás la Secretaría ya tiene el
   legajo y no hay nada que mandar. Es una función pura aparte
   del componente para poder usarla también en la página.
   ═══════════════════════════════════════════════════════════════ */

import type { LegajoDetalle } from '../shared/api/tipos'

/** Si el legajo está en un estado desde el que el aspirante puede enviar. */
export function sePuedeEnviar(legajo: LegajoDetalle): boolean {
  return (
    legajo.puedeEditar === true && (legajo.estado === 'BORRADOR' || legajo.estado === 'OBSERVADO')
  )
}
