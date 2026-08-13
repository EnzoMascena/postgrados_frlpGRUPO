import type { BarraDato, CohorteStats } from '../type'
 
// ── Datos ficticios para la demo ──────────────────────────────
// En la Entrega 3 esto se reemplaza por la respuesta de la API.
 
// Fuente única de verdad: de acá salen las stat cards, el gráfico
// de inscriptos y la tabla. Si cambiás un número, todo se actualiza.
// Regla que se cumple en cada fila:
//   inscriptos = graduados + desgranados + activos
export const cohortesMock: CohorteStats[] = [
  { anio: 2026, inscriptos: 47, graduados: 0, desgranados: 0, activos: 47, ralentizados: 3 },
  { anio: 2025, inscriptos: 41, graduados: 3, desgranados: 6, activos: 32, ralentizados: 5 },
  { anio: 2024, inscriptos: 38, graduados: 20, desgranados: 8, activos: 10, ralentizados: 4 },
  { anio: 2023, inscriptos: 36, graduados: 26, desgranados: 7, activos: 3, ralentizados: 2 },
  { anio: 2022, inscriptos: 22, graduados: 18, desgranados: 3, activos: 1, ralentizados: 0 },
]
 
export const seminariosCohorteActual: BarraDato[] = [
  { label: 'Aprobados', valor: 62, color: 'ok' },
  { label: 'En cursada', valor: 24, color: 'warn' },
  { label: 'Pendientes', valor: 14, color: 'neutral' },
]
 
export const trabajosFinales: BarraDato[] = [
  { label: 'Aprobados', valor: 36, color: 'ok' },
  { label: 'En elaboración', valor: 31, color: 'warn' },
  { label: 'Sin iniciar', valor: 33, color: 'neutral' },
]
 
export const cohortesDisponibles = [
  'Todas las cohortes',
  '2026',
  '2025',
  '2024',
  '2023',
  '2022',
]
 