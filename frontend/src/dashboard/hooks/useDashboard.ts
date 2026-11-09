/* ═══════════════════════════════════════════════════════════════
   useDashboard.ts — RESUMEN Y PERÍODO, CON TANSTACK QUERY
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   useResumen y useLegajos son useQuery: los guardan en la caché
   con su clave (['resumen', cohorteId] y ['legajos', filtros]),
   así cada cohorte y cada combinación de filtros tiene lo suyo, y
   volver a una que ya se miró no la vuelve a pedir al instante.

   useLegajos usa placeholderData: keepPreviousData. Mientras llega
   la página nueva se sigue viendo la anterior, en vez de que la
   tabla se vacíe en cada letra que se escribe o en cada "Sig.".

   useCambiarPeriodo es un useMutation. Cuando sale bien, invalida
   ['cohortes']: TanStack Query vuelve a pedir GET /cohortes y todo
   lo que lo usa (el interruptor, el formulario de inscripción) ve
   el período nuevo sin que nadie lo actualice a mano.
   ═══════════════════════════════════════════════════════════════ */

import {
  keepPreviousData,
  skipToken,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import { cambiarPeriodo, listarLegajos, obtenerResumen, type FiltrosLegajos } from '../api'

/** GET /legajos. Sin cohorte (todavía cargando) no pide nada. */
export function useLegajos(filtros: FiltrosLegajos | undefined) {
  return useQuery({
    queryKey: ['legajos', filtros],
    queryFn: filtros ? () => listarLegajos(filtros) : skipToken,
    placeholderData: keepPreviousData,
  })
}

/** GET /legajos/resumen. Sin cohorte (todavía cargando) no pide nada. */
export function useResumen(cohorteId: string | undefined) {
  return useQuery({
    queryKey: ['resumen', cohorteId],
    queryFn: cohorteId ? () => obtenerResumen(cohorteId) : skipToken,
  })
}

/** PATCH /cohortes/{id}/inscripcion. */
export function useCambiarPeriodo() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: cambiarPeriodo,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['cohortes'] }),
  })
}
