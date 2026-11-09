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
   Y los del detalle de un legajo:
     GET   /legajos/{id}                 → datos, documentos, historial
                                           y acciones permitidas (L3)
     PATCH /legajos/{id}/estado          → aprueba, observa, etc. (L3)
     GET   /documentos/{id}/download     → el PDF, con el token (F5)

   Ni la tabla ni las tarjetas filtran o cuentan en el front: el
   back lo hace en la base y nos manda solo lo que se ve. Así no
   hace falta traer todos los legajos para mostrar 20.

   Los componentes no llaman a estas funciones directo: usan los
   hooks de hooks/useDashboard.ts (TanStack Query).
   ═══════════════════════════════════════════════════════════════ */

import { apiDescargar, apiFetch } from '../shared/api/client'
import type {
  AccionLegajo,
  Cohorte,
  EstadoLegajo,
  LegajoDetalle,
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

/** Los filtros como query string. Solo van los que tienen valor. */
function aParametros(filtros: Partial<FiltrosLegajos>): URLSearchParams {
  const params = new URLSearchParams()
  for (const [clave, valor] of Object.entries(filtros)) {
    if (valor !== null && valor !== undefined && valor !== '') params.set(clave, String(valor))
  }
  return params
}

/** GET /legajos: los más nuevos primero. */
export function listarLegajos(filtros: FiltrosLegajos): Promise<Paginado<LegajoItem>> {
  return apiFetch<Paginado<LegajoItem>>(`/legajos?${aParametros(filtros)}`)
}

/** Lo que manda Exportar: los mismos filtros que la tabla, sin página. */
export type FiltrosExportar = Omit<FiltrosLegajos, 'page' | 'size'>

/** GET /legajos/exportar (L5, Luca): el .xlsx con TODOS los legajos que
    cumplen los filtros, no solo los 20 de la página. Devuelve el archivo
    y el nombre que manda el back (inscriptos-cohorte2026-2026-11-08.xlsx). */
export function exportarLegajos(filtros: FiltrosExportar) {
  return apiDescargar(`/legajos/exportar?${aParametros(filtros)}`)
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

/** GET /legajos/{id}: la vista del coordinador (con historial y acciones). */
export function obtenerLegajo(id: string): Promise<LegajoDetalle> {
  return apiFetch<LegajoDetalle>(`/legajos/${encodeURIComponent(id)}`)
}

export type CambioDeEstado = {
  accion: AccionLegajo
  /** Obligatorio para OBSERVAR (5 caracteres o más); opcional en las demás. */
  comentario: string | null
}

/** PATCH /legajos/{id}/estado: devuelve el legajo ya cambiado. */
export function cambiarEstado(id: string, cambio: CambioDeEstado): Promise<LegajoDetalle> {
  return apiFetch<LegajoDetalle>(`/legajos/${encodeURIComponent(id)}/estado`, {
    method: 'PATCH',
    json: cambio,
  })
}

/** GET /documentos/{id}/download: el PDF como Blob. Viaja con el token,
    por eso no se puede abrir con un <a href> común. */
export function descargarDocumento(documentoId: string) {
  return apiDescargar(`/documentos/${encodeURIComponent(documentoId)}/download`)
}
