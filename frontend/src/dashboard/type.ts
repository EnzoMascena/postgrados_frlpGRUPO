// Tipos del dashboard de conducción.
// En la Entrega 3 estos mismos tipos describen la respuesta de la API.

/** Beca solicitada por el aspirante. */
export type Beca = 'sin' | '30' | '100'

/** Una fila de la tabla de inscriptos. */
export type Inscripto = {
  id: string
  apellidoNombre: string
  dni: string
  carrera: string
  cohorte: string
  beca: Beca
  /** Cuántos de los documentos obligatorios entregó. */
  documentosPresentados: number
}

/** Total de documentos obligatorios del legajo. */
export const DOCUMENTOS_REQUERIDOS = 6