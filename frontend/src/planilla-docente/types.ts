// Tipos de la planilla docente.
// En la Entrega 3 estos mismos tipos describen la respuesta de la API.

// Estado de una celda de la grilla: sin marcar, Presente o Ausente.
export type Asistencia = '' | 'P' | 'A'

export type Seminario = {
  nombre: string
  docente: string
  carrera: string
  cohorte: string
  /** Porcentaje mínimo de asistencia para no quedar libre. */
  asistenciaMinima: number
}

export type FechaCursada = {
  fecha: string
  dictada: boolean
}

export type EstudiantePlanilla = {
  id: string
  nombre: string
  email: string
  carreraGrado: string
  /** Una entrada por cada fecha de `fechasGrilla`, en el mismo orden. */
  asistencias: Asistencia[]
  /** Se guarda como texto porque viene de un input. */
  nota: string
}
