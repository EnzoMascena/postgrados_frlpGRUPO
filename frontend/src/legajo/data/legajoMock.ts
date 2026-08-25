import type { Estudiante, Seminario, TrabajoFinal, Tutoria } from '../types'

// ── Datos ficticios para la demo ──────────────────────────────
// En la Entrega 3 esto se reemplaza por la respuesta de la API.
// El semáforo, los contadores y la asistencia promedio se derivan
// de esta lista de seminarios: no hay nada escrito a mano.

export const estudianteMock: Estudiante = {
  apellidoNombre: 'Mascena, Enzo',
  carrera: 'Especialización en Ing. Sistemas',
  cohorte: '2026',
  dni: '38.500.000',
  correo: 'enzo@email.com',
  tituloGrado: 'Ing. en Sistemas',
  legajoCompleto: true,
}

export const seminariosMock: Seminario[] = [
  {
    id: 's1',
    nombre: 'Gestión de Proyectos de Software',
    condicion: 'aprobado',
    asistencia: 93,
    calificacion: 8,
    fechaActa: '15/03/2026',
    vencimiento: null,
  },
  {
    id: 's2',
    nombre: 'Arquitecturas de Software',
    condicion: 'aprobado',
    asistencia: 88,
    calificacion: 9,
    fechaActa: '20/04/2026',
    vencimiento: null,
  },
  {
    id: 's3',
    nombre: 'Seguridad Informática',
    condicion: 'aprobado',
    asistencia: 80,
    calificacion: 7,
    fechaActa: '10/05/2026',
    vencimiento: null,
  },
  {
    id: 's4',
    nombre: 'Métodos Cuantitativos',
    condicion: 'cursando',
    asistencia: 72,
    calificacion: null,
    fechaActa: null,
    vencimiento: '30/06/2026',
    vencimientoProximo: true,
  },
  {
    id: 's5',
    nombre: 'Innovación y Tecnología',
    condicion: 'pendiente',
    asistencia: null,
    calificacion: null,
    fechaActa: null,
    vencimiento: '31/10/2026',
  },
  {
    id: 's6',
    nombre: 'Trabajo Final Integrador',
    condicion: 'en-elaboracion',
    asistencia: null,
    calificacion: null,
    fechaActa: null,
    vencimiento: '30/11/2026',
  },
]

export const trabajoFinalMock: TrabajoFinal = {
  titulo: 'Sistema de gestión académica para posgrado',
  director: 'Dr. Pérez, Juan',
  aprobacionCPR: '',
  numeroResolucion: '',
}

export const tutoriasMock: Tutoria[] = [
  {
    id: 't1',
    fecha: '15/04/2026',
    titulo: 'Tutoría inicial',
    detalle: 'Se definió enfoque del TFI. Próxima entrega: borrador cap. 1.',
  },
  {
    id: 't2',
    fecha: '10/05/2026',
    titulo: 'Revisión capítulo 1',
    detalle: 'Observaciones menores. Se aprueba avance hacia cap. 2.',
  },
]