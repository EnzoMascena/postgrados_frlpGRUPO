/* ═══════════════════════════════════════════════════════════════
   api.ts — LOS PEDIDOS DEL DASHBOARD A LA API
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Tres endpoints del coordinador (plan §10), todos con JWT (lo
   pone apiFetch):
     GET   /legajos?q=&estado=&…         → una página de la tabla
                                           (L4, Luca)
     GET   /legajos/resumen?cohorte=<id> → los conteos de las 4
                                           tarjetas (L4, Luca)
     PATCH /cohortes/{id}/inscripcion    → abre o cierra el período
                                           de una cohorte (F2, Fran)

   Ni la tabla ni las tarjetas filtran o cuentan en el front: el
   back lo hace en la base y nos manda solo lo que se ve. Así no
   hace falta traer todos los legajos para mostrar 20.

   Los componentes no llaman a estas funciones directo: usan los
   hooks de hooks/useDashboard.ts (TanStack Query).
   ═══════════════════════════════════════════════════════════════ */

import { apiFetch } from '../shared/api/client'
import type {
  Cohorte,
  EstadoLegajo,
  LegajoItem,
  Paginado,
  ResumenLegajos,
} from '../shared/api/tipos'

/** Lo que manda la tabla. null o '' = sin ese filtro. */
export type FiltrosLegajos = {
  cohorte: string
  q: string | null
  estado: EstadoLegajo | ''
  carrera: string
  beca: '' | 'true' | 'false'
  page: number
  size: number
}

/** GET /legajos: los más nuevos primero. Solo van los filtros que tienen valor. */
export function listarLegajos(filtros: FiltrosLegajos): Promise<Paginado<LegajoItem>> {
  const params = new URLSearchParams()
  for (const [clave, valor] of Object.entries(filtros)) {
    if (valor !== null && valor !== '') params.set(clave, String(valor))
  }
  return apiFetch<Paginado<LegajoItem>>(`/legajos?${params}`)
}

/** GET /legajos/resumen: total, cantidad por estado y becas de la cohorte. */
export function obtenerResumen(cohorteId: string): Promise<ResumenLegajos> {
  return apiFetch<ResumenLegajos>(`/legajos/resumen?cohorte=${encodeURIComponent(cohorteId)}`)
}

export type CambioDePeriodo = {
  cohorteId: string
  abierta: boolean
  /** "AAAA-MM-DD". Solo cuenta al cerrar: al abrir, el back la borra. */
  proximaApertura: string | null
}

/** PATCH /cohortes/{id}/inscripcion: devuelve la cohorte ya cambiada. */
export function cambiarPeriodo({
  cohorteId,
  abierta,
  proximaApertura,
}: CambioDePeriodo): Promise<Cohorte> {
  return apiFetch<Cohorte>(`/cohortes/${encodeURIComponent(cohorteId)}/inscripcion`, {
    method: 'PATCH',
    json: { abierta, proximaApertura },
  })
}
