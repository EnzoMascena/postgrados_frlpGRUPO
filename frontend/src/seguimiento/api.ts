/* ═══════════════════════════════════════════════════════════════
   api.ts — LOS PEDIDOS DEL SEGUIMIENTO A LA API
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   El aspirante no tiene usuario: entra con el link que le llegó
   por email, /seguimiento/{token}. Ese token es su "llave" y va
   en la ruta de cada pedido, así que no hace falta JWT:
     GET /seguimiento/{token} → su legajo (vista aspirante)
   Si el link no existe o venció (60 días), el back responde 404.

   El token se pasa por encodeURIComponent: viene de la URL y
   puede traer caracteres que romperían la ruta (- y _ no, pero
   así no dependemos de cómo lo arme el back).
   ═══════════════════════════════════════════════════════════════ */

import { ApiError, apiFetch } from '../shared/api/client'
import type { LegajoDetalle } from '../shared/api/tipos'

/** La ruta base de todos los pedidos de este aspirante. */
export function rutaSeguimiento(token: string): string {
  return `/seguimiento/${encodeURIComponent(token)}`
}

/** GET /seguimiento/{token}. */
export function obtenerSeguimiento(token: string): Promise<LegajoDetalle> {
  return apiFetch<LegajoDetalle>(rutaSeguimiento(token))
}

/** true si el link no vale: no existe o venció. */
export function esLinkInvalido(error: Error | null): boolean {
  return error instanceof ApiError && error.status === 404
}
