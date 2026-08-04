import type { EstudiantePlanilla, FechaCursada, Seminario } from '../types'

// ── Datos ficticios para la demo ──────────────────────────────
// En la Entrega 3 esto se reemplaza por la respuesta de la API.

export const seminarioMock: Seminario = {
  nombre: 'Gestión de Proyectos de Software',
  docente: 'Ing. Rodríguez, Ana',
  carrera: 'Esp. Ing. Sistemas',
  cohorte: '2026',
  asistenciaMinima: 75,
}

// Todas las fechas registradas (se muestran como chips arriba).
export const fechasRegistradas: FechaCursada[] = [
  { fecha: '12/03', dictada: true },
  { fecha: '19/03', dictada: true },
  { fecha: '26/03', dictada: true },
  { fecha: '02/04', dictada: true },
  { fecha: '09/04', dictada: true },
  { fecha: '16/04', dictada: true },
  { fecha: '23/04', dictada: false },
]

// Las fechas que aparecen como COLUMNAS de la grilla.
// Se derivan de las clases YA DICTADAS: no se puede cargar asistencia
// de una clase que todavía no ocurrió. Al derivarlas evitamos que la
// grilla y los chips de arriba queden desincronizados.
// El orden acá define el orden de las columnas y tiene que
// coincidir con el array `asistencias` de cada estudiante.
export const fechasGrilla: string[] = fechasRegistradas
  .filter((f) => f.dictada)
  .map((f) => f.fecha)

// Cada array `asistencias` tiene una entrada por cada fecha de
// `fechasGrilla`, en el mismo orden: 12/03, 19/03, 26/03, 02/04,
// 09/04 y 16/04.
export const estudiantesMock: EstudiantePlanilla[] = [
  {
    id: 'e1',
    nombre: 'Mascena, Enzo',
    email: 'enzo@mail.com',
    carreraGrado: 'Ing. Sistemas',
    asistencias: ['P', 'P', 'A', 'P', 'P', 'P'],
    nota: '',
  },
  {
    id: 'e2',
    nombre: 'García, María',
    email: 'mgarcia@mail.com',
    carreraGrado: 'Ing. Civil',
    asistencias: ['P', 'P', 'P', 'P', 'P', 'P'],
    nota: '9',
  },
  {
    id: 'e3',
    nombre: 'López, Tomás',
    email: 'tlopez@mail.com',
    carreraGrado: 'Ing. Eléctrica',
    asistencias: ['A', 'A', 'P', 'A', 'P', 'A'],
    nota: '',
  },
]