// Tipos de la pantalla de estadísticas.
// En la Entrega 3 estos mismos tipos describen la respuesta de la API.
 
/** Una fila de la tabla de cohortes. Los totales se derivan de acá. */
export type CohorteStats = {
  anio: number
  inscriptos: number
  graduados: number
  desgranados: number
  activos: number
  /** Estudiantes que siguen activos pero atrasados respecto del plan. */
  ralentizados: number
}
 
/** Una barra de un gráfico: etiqueta, valor y color semántico. */
export type BarraDato = {
  label: string
  valor: number
  color: 'primary' | 'ok' | 'warn' | 'neutral'
}
 