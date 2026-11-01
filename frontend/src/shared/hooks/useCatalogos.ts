/* ═══════════════════════════════════════════════════════════════
   useCatalogos.ts — COHORTES Y CARRERAS (los usan Gero y Loli)
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Antes estos datos salían de un mock; ahora los pide TanStack
   Query a la API. Cada hook devuelve { data, isPending, error }:
   la pantalla muestra "Cargando", el error o los datos.

   La clave (queryKey) es el nombre del dato en la caché: si dos
   pantallas piden ['cohortes'], la API se llama una sola vez y
   las dos usan la misma respuesta. Cuando el coordinador abre o
   cierra el período, se invalida ['cohortes'] y se vuelve a pedir.
   ═══════════════════════════════════════════════════════════════ */

import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../api/client'
import type { Carrera, Cohorte } from '../api/tipos'

/** GET /cohortes: de la más nueva a la más vieja. */
export function useCohortes() {
  return useQuery({
    queryKey: ['cohortes'],
    queryFn: () => apiFetch<Cohorte[]>('/cohortes'),
  })
}

/** GET /carreras: solo las activas. */
export function useCarreras() {
  return useQuery({
    queryKey: ['carreras'],
    queryFn: () => apiFetch<Carrera[]>('/carreras'),
  })
}
