// Tipos del legajo académico.
// En la Entrega 3 estos mismos tipos describen la respuesta de la API.
 
/** Situación de un seminario dentro del plan de estudios. */
export type CondicionSeminario =
  | 'aprobado'
  | 'cursando'
  | 'pendiente'
  | 'en-elaboracion'
 
export type Seminario = {
  id: string
  nombre: string
  condicion: CondicionSeminario
  /** Porcentaje de asistencia. null cuando todavía no corresponde. */
  asistencia: number | null
  /** Calificación final. null si aún no se calificó. */
  calificacion: number | null
  fechaActa: string | null
  vencimiento: string | null
  /** Marca los vencimientos próximos que requieren atención. */
  vencimientoProximo?: boolean
}
 
export type Estudiante = {
  apellidoNombre: string
  carrera: string
  cohorte: string
  dni: string
  correo: string
  tituloGrado: string
  legajoCompleto: boolean
}
 
export type TrabajoFinal = {
  titulo: string
  director: string
  aprobacionCPR: string
  numeroResolucion: string
}
 
export type Tutoria = {
  id: string
  fecha: string
  titulo: string
  detalle: string
}