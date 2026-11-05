/* ═══════════════════════════════════════════════════════════════
   useSeguimiento.ts — EL LEGAJO DEL ASPIRANTE, CON TANSTACK QUERY
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   La clave ['seguimiento', token] es el nombre de este dato en la
   caché. Cuando el aspirante suba un PDF (checkpoint 3.2) o envíe
   a revisión (G4), esas mutaciones invalidan esta clave y TanStack
   Query vuelve a pedir el legajo solo: la pantalla se actualiza
   sin que escribamos un refetch a mano.

   Un 404 no se reintenta: el link no vale y reintentar no lo
   arregla. Cualquier otro error (sin conexión, 500) se reintenta
   una vez, como el resto de la app.
   ═══════════════════════════════════════════════════════════════ */

import { useQuery } from '@tanstack/react-query'
import { esLinkInvalido, obtenerSeguimiento } from '../api'

/** La clave de la caché: la usan también las mutaciones para invalidar. */
export const claveSeguimiento = (token: string) => ['seguimiento', token] as const

/** GET /seguimiento/{token}. */
export function useSeguimiento(token: string) {
  return useQuery({
    queryKey: claveSeguimiento(token),
    queryFn: () => obtenerSeguimiento(token),
    retry: (intentos, error) => !esLinkInvalido(error) && intentos < 1,
  })
}
