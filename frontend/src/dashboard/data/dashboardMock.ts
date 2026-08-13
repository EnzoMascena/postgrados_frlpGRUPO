import type { Inscripto } from '../type'

// ── Datos ficticios para la demo ──────────────────────────────
// En la Entrega 3 esto se reemplaza por la respuesta de la API.
// Las stat cards y la completitud se derivan de esta lista:
// no hay ningún total ni porcentaje escrito a mano.

export const inscriptosMock: Inscripto[] = [
  { id: 'i1', apellidoNombre: 'Mascena, Enzo',     dni: '38.500.000', carrera: 'Esp. Ing. Sistemas', cohorte: '2026', beca: 'sin', documentosPresentados: 6 },
  { id: 'i2', apellidoNombre: 'García, María',     dni: '41.200.111', carrera: 'Maestría',           cohorte: '2026', beca: '30',  documentosPresentados: 4 },
  { id: 'i3', apellidoNombre: 'López, Tomás',      dni: '39.800.444', carrera: 'Doctorado',          cohorte: '2026', beca: '100', documentosPresentados: 2 },
  { id: 'i4', apellidoNombre: 'Ramírez, Lucía',    dni: '40.500.222', carrera: 'Esp. Ing. Sistemas', cohorte: '2026', beca: 'sin', documentosPresentados: 6 },
  { id: 'i5', apellidoNombre: 'Fernández, Diego',  dni: '37.910.333', carrera: 'Maestría',           cohorte: '2026', beca: 'sin', documentosPresentados: 5 },
  { id: 'i6', apellidoNombre: 'Sosa, Valentina',   dni: '42.115.678', carrera: 'Esp. Ing. Sistemas', cohorte: '2026', beca: '30',  documentosPresentados: 6 },
  { id: 'i7', apellidoNombre: 'Benítez, Martín',   dni: '36.400.900', carrera: 'Doctorado',          cohorte: '2026', beca: 'sin', documentosPresentados: 3 },
  { id: 'i8', apellidoNombre: 'Quiroga, Sofía',    dni: '43.020.155', carrera: 'Maestría',           cohorte: '2026', beca: '100', documentosPresentados: 6 },

  { id: 'i9',  apellidoNombre: 'Álvarez, Nicolás', dni: '35.700.480', carrera: 'Maestría',           cohorte: '2025', beca: 'sin', documentosPresentados: 6 },
  { id: 'i10', apellidoNombre: 'Molina, Camila',   dni: '38.045.712', carrera: 'Esp. Ing. Sistemas', cohorte: '2025', beca: '30',  documentosPresentados: 6 },
  { id: 'i11', apellidoNombre: 'Herrera, Pablo',   dni: '34.220.865', carrera: 'Doctorado',          cohorte: '2025', beca: 'sin', documentosPresentados: 5 },

  { id: 'i12', apellidoNombre: 'Cabrera, Julieta', dni: '33.980.041', carrera: 'Maestría',           cohorte: '2024', beca: 'sin', documentosPresentados: 6 },
  { id: 'i13', apellidoNombre: 'Duarte, Iván',     dni: '32.560.777', carrera: 'Esp. Ing. Sistemas', cohorte: '2024', beca: '100', documentosPresentados: 6 },
]

export const cohortesDisponibles = ['2026', '2025', '2024']