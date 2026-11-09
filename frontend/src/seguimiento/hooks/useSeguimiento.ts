/* ═══════════════════════════════════════════════════════════════
   useSeguimiento.ts — EL LEGAJO DEL ASPIRANTE, CON TANSTACK QUERY
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   La clave ['seguimiento', token] es el nombre de este dato en la
   caché. Cuando el aspirante sube un PDF (useSubirDocumento) o
   envía a revisión (G4), esas mutaciones invalidan esta clave y
   TanStack Query vuelve a pedir el legajo solo: la pantalla se
   actualiza sin que escribamos un refetch a mano.

   Un 404 no se reintenta: el link no vale y reintentar no lo
   arregla. Cualquier otro error (sin conexión, 500) se reintenta
   una vez, como el resto de la app.
   ═══════════════════════════════════════════════════════════════ */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { TipoDocumento } from '../../shared/api/tipos'
import type { DatosLegajoPayload } from '../../inscripcion/types'
import {
  actualizarDatos,
  enviarARevision,
  esLinkInvalido,
  obtenerSeguimiento,
  subirDocumento,
} from '../api'

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

/**
 * POST /seguimiento/{token}/documentos. Al terminar (bien o mal) invalida
 * ['seguimiento', token]: el checklist se vuelve a pedir y muestra el PDF
 * nuevo como Cargado. Si falló porque el legajo ya no es editable o el link
 * venció, el refetch también trae ese estado nuevo.
 *
 * onSettled devuelve la promesa del refetch: la mutación sigue en
 * isPending hasta que llega el legajo actualizado, así la caja no pasa
 * de "Subiendo…" a "Pendiente" por un instante antes de "Cargado".
 */
export function useSubirDocumento(token: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ tipo, archivo }: { tipo: TipoDocumento; archivo: File }) =>
      subirDocumento(token, tipo, archivo),
    onSettled: () => queryClient.invalidateQueries({ queryKey: claveSeguimiento(token) }),
  })
}

/**
 * POST /seguimiento/{token}/enviar. Si sale bien, el back devuelve el legajo
 * ya en PENDIENTE: lo ponemos directo en la caché para que la página cambie
 * al toque, y después invalidamos igual para quedar alineados con el back.
 * Si falla (422 DOCUMENTOS_FALTANTES, 409 TRANSICION_INVALIDA), el refetch
 * trae los `documentosFaltantes` y el estado actualizados.
 */
export function useEnviar(token: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => enviarARevision(token),
    onSuccess: (legajo) => queryClient.setQueryData(claveSeguimiento(token), legajo),
    onSettled: () => queryClient.invalidateQueries({ queryKey: claveSeguimiento(token) }),
  })
}

/**
 * PUT /seguimiento/{token}. Igual que enviar: la respuesta (el legajo
 * actualizado) va directo a la caché y después se invalida. Cambiar el
 * título de posgrado o la beca cambia los documentos que le tocan, y el
 * refetch los trae.
 */
export function useActualizarDatos(token: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (cuerpo: DatosLegajoPayload) => actualizarDatos(token, cuerpo),
    onSuccess: (legajo) => queryClient.setQueryData(claveSeguimiento(token), legajo),
    onSettled: () => queryClient.invalidateQueries({ queryKey: claveSeguimiento(token) }),
  })
}
