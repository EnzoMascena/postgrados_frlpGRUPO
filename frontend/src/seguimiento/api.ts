/* ═══════════════════════════════════════════════════════════════
   api.ts — LOS PEDIDOS DEL SEGUIMIENTO A LA API
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   El aspirante no tiene usuario: entra con el link que le llegó
   por email, /seguimiento/{token}. Ese token es su "llave" y va
   en la ruta de cada pedido, así que no hace falta JWT:
     GET  /seguimiento/{token}                 → su legajo
     POST /seguimiento/{token}/documentos      → sube un PDF
     GET  /seguimiento/{token}/documentos/{id}/download → lo ve
   Si el link no existe o venció (60 días), el back responde 404.

   El token se pasa por encodeURIComponent: viene de la URL y
   puede traer caracteres que romperían la ruta (- y _ no, pero
   así no dependemos de cómo lo arme el back).
   ═══════════════════════════════════════════════════════════════ */

import { ApiError, apiFetch } from '../shared/api/client'
import type { LegajoDetalle, TipoDocumento } from '../shared/api/tipos'
import type { DatosLegajoPayload } from '../inscripcion/types'

/** La ruta base de todos los pedidos de este aspirante. */
export function rutaSeguimiento(token: string): string {
  return `/seguimiento/${encodeURIComponent(token)}`
}

/** GET /seguimiento/{token}. */
export function obtenerSeguimiento(token: string): Promise<LegajoDetalle> {
  return apiFetch<LegajoDetalle>(rutaSeguimiento(token))
}

/** Respuesta 201 de POST /seguimiento/{token}/documentos (plan §10). */
export type DocumentoSubido = {
  documentoId: string
  tipo: TipoDocumento
  nombreOriginal: string
  tamanioBytes: number
  checksumSha256: string
  fechaSubida: string
}

/**
 * POST /seguimiento/{token}/documentos, multipart con `tipo` y `archivo`.
 * No se pone Content-Type: el navegador lo arma con el boundary del FormData.
 */
export function subirDocumento(
  token: string,
  tipo: TipoDocumento,
  archivo: File,
): Promise<DocumentoSubido> {
  const formulario = new FormData()
  formulario.append('tipo', tipo)
  formulario.append('archivo', archivo)
  return apiFetch<DocumentoSubido>(`${rutaSeguimiento(token)}/documentos`, {
    method: 'POST',
    body: formulario,
  })
}

/**
 * POST /seguimiento/{token}/enviar, sin cuerpo (plan §10). El back decide
 * la acción según el estado: en BORRADOR hace ENVIAR y en OBSERVADO,
 * CORREGIR. Responde el detalle con el estado PENDIENTE. Si falta un
 * documento obligatorio: 422 DOCUMENTOS_FALTANTES y el estado no cambia.
 */
export function enviarARevision(token: string): Promise<LegajoDetalle> {
  return apiFetch<LegajoDetalle>(`${rutaSeguimiento(token)}/enviar`, { method: 'POST' })
}

/**
 * PUT /seguimiento/{token} (plan §10): el mismo cuerpo de POST /legajos sin
 * `cohorteId`, con las mismas reglas (DNI y email únicos sin contar al
 * propio legajo). Solo en BORRADOR u OBSERVADO; si no, 409 LEGAJO_NO_EDITABLE.
 * Responde el detalle actualizado.
 */
export function actualizarDatos(
  token: string,
  cuerpo: DatosLegajoPayload,
): Promise<LegajoDetalle> {
  return apiFetch<LegajoDetalle>(rutaSeguimiento(token), { method: 'PUT', json: cuerpo })
}

/** true si el back frenó el envío porque falta algún documento obligatorio. */
export function esDocumentosFaltantes(error: Error | null): boolean {
  return error instanceof ApiError && error.codigo === 'DOCUMENTOS_FALTANTES'
}

/**
 * La URL para ver un PDF subido, en una pestaña nueva. Es un link común
 * (no pasa por apiFetch) porque el token ya va en la ruta: no hace falta
 * ningún encabezado, y así el navegador muestra el PDF con su visor.
 */
export function urlDescarga(token: string, documentoId: string): string {
  return `/api/v1${rutaSeguimiento(token)}/documentos/${encodeURIComponent(documentoId)}/download`
}

/** true si el link no vale: no existe o venció. */
export function esLinkInvalido(error: Error | null): boolean {
  return error instanceof ApiError && error.status === 404
}
