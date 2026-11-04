/* ═══════════════════════════════════════════════════════════════
   useInscripcion.ts — GUARDAR Y RECUPERAR, CON TANSTACK QUERY
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Leer datos (cohortes, carreras) es un useQuery; mandar datos que
   cambian algo en el servidor es un useMutation. La mutación nos da
   el estado del envío sin escribir un solo useState a mano:
     isPending → está guardando (el botón dice "Guardando…")
     error     → el ApiError del back, con su mensaje y su campo
     data      → la respuesta (el token, o el mensaje de recuperar)
     reset()   → vuelve todo a cero
   Qué hacer cuando sale bien (navegar, mostrar una Alerta) lo
   decide la pantalla, con el onSuccess de mutate().
   ═══════════════════════════════════════════════════════════════ */

import { useMutation } from '@tanstack/react-query'
import { inscribir, recuperarAcceso } from '../api'

/** POST /legajos. */
export function useInscribir() {
  return useMutation({ mutationFn: inscribir })
}

/** POST /legajos/recuperar-acceso. */
export function useRecuperarAcceso() {
  return useMutation({ mutationFn: recuperarAcceso })
}
