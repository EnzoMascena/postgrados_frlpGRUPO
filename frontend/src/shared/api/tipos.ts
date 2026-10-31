/* ═══════════════════════════════════════════════════════════════
   tipos.ts — LOS TIPOS DEL CONTRATO DE LA API (plan §10)
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Describe con TypeScript lo que manda y recibe el back. Los
   nombres de los campos son los mismos que en el JSON (camelCase),
   así si el back cambia un campo, el editor marca en rojo todos
   los lugares del front que lo usan, antes de ejecutar nada.

   También están las etiquetas en español de cada estado, acción
   y documento: el back manda "EN_REVISION" y la pantalla muestra
   "En revisión". Lo usamos Gero y yo, así las dos pantallas dicen
   lo mismo.
   ═══════════════════════════════════════════════════════════════ */

// ── Valores fijos (enums del back) ─────────────────────────────

export type EstadoLegajo =
  | 'BORRADOR'
  | 'PENDIENTE'
  | 'EN_REVISION'
  | 'OBSERVADO'
  | 'COMPLETADO'
  | 'ACTIVO'
  | 'VENCIDO'
  | 'RECHAZADO'
  | 'BAJA'
  | 'GRADUADO'

export type AccionLegajo =
  | 'ENVIAR'
  | 'REVISAR'
  | 'OBSERVAR'
  | 'CORREGIR'
  | 'APROBAR'
  | 'RECHAZAR'
  | 'MATRICULAR'
  | 'VENCER'
  | 'DAR_DE_BAJA'
  | 'GRADUAR'

export type TipoDocumento =
  | 'FORM_INSCRIPCION'
  | 'DNI'
  | 'TITULO_GRADO'
  | 'PARTIDA'
  | 'CUIT_CUIL'
  | 'TITULO_POSGRADO'
  | 'FORM_BECA'

// Roles de los usuarios con login.
export type Rol = 'COORDINADOR' | 'DOCENTE' | 'CPR' | 'ADMIN'

// Quién hizo un cambio en el historial: además de los usuarios,
// el aspirante (ENVIAR, CORREGIR) y el sistema (VENCER).
export type RolActor = Rol | 'ASPIRANTE' | 'SISTEMA'

export type TipoCarrera = 'Especializacion' | 'Maestria' | 'Doctorado'
export type TipoBeca = '30' | '100'
export type ComoConocio = 'SITIO_WEB_UTN' | 'OTROS_SITIOS' | 'EGRESADOS' | 'COLEGAS' | 'OTROS'

// ── Respuestas de la API ───────────────────────────────────────
// Las fechas llegan como texto ISO en UTC ("2026-11-03T14:20:00Z").

export type Usuario = {
  id: string
  email: string
  nombre: string
  rol: Rol
}

export type RespuestaLogin = {
  accessToken: string
  tokenType: string
  expiraEn: number
  usuario: Usuario
}

export type Cohorte = {
  id: string
  anio: number
  numero: number
  nombre: string
  inscripcionAbierta: boolean
  fechaInicio: string | null
  proximaApertura: string | null
}

export type Carrera = {
  id: string
  nombre: string
  tipo: TipoCarrera
}

export type ItemDocumento = {
  tipo: TipoDocumento
  nombre: string
  obligatorio: boolean
  cargado: boolean
  documentoId: string | null
  nombreOriginal: string | null
  tamanioBytes: number | null
  fechaSubida: string | null
}

export type ItemHistorial = {
  fecha: string
  accion: AccionLegajo
  estadoAnterior: EstadoLegajo
  estadoNuevo: EstadoLegajo
  comentario: string | null
  rol: RolActor
  usuarioEmail: string | null
}

// GET /legajos/{id} (coordinador) y GET /seguimiento/{token}
// (aspirante) devuelven el mismo cuerpo; los últimos tres campos
// vienen solo en una de las dos vistas, por eso son opcionales.
export type LegajoDetalle = {
  id: string
  codigoSeguimiento: string
  numeroLegajo: string | null
  estado: EstadoLegajo
  cohorte: Pick<Cohorte, 'id' | 'nombre' | 'anio'>
  carreras: Carrera[]
  apellido: string
  nombre: string
  nacionalidad: string
  dni: string
  telefonoMovil: string
  telefonoFijo: string | null
  email: string
  emailAlternativo: string
  domicilio: string
  ciudad: string
  provincia: string
  pais: string
  tituloGrado: string
  tituloPosgrado: string | null
  comoConocio: ComoConocio
  motivacion: string
  solicitaBeca: boolean
  tipoBeca: TipoBeca | null
  fechaInscripcion: string | null
  fechaAprobacion: string | null
  fechaActivacion: string | null
  createdAt: string
  documentos: ItemDocumento[]
  documentosFaltantes: TipoDocumento[]
  ultimaObservacion: string | null
  historial?: ItemHistorial[] // solo coordinador
  accionesPermitidas?: AccionLegajo[] // solo coordinador
  puedeEditar?: boolean // solo aspirante
}

// Una fila del listado GET /legajos.
export type LegajoItem = {
  id: string
  codigoSeguimiento: string
  numeroLegajo: string | null
  apellido: string
  nombre: string
  dni: string
  email: string
  estado: EstadoLegajo
  cohorte: string
  carreras: string[]
  solicitaBeca: boolean
  tipoBeca: TipoBeca | null
  documentosCargados: number
  documentosRequeridos: number
  fechaInscripcion: string | null
}

export type ResumenLegajos = {
  total: number
  porEstado: Record<EstadoLegajo, number>
  conBeca: number
  beca30: number
  beca100: number
}

// Cualquier listado paginado: Paginado<LegajoItem>, por ejemplo.
export type Paginado<T> = {
  items: T[]
  total: number
  page: number
  size: number
}

// ── Etiquetas para mostrar en pantalla ─────────────────────────
// Record<EstadoLegajo, ...> obliga a cubrir los 10 estados: si el
// back agrega uno y no lo sumamos acá, no compila.

// Mismos colores que Badge y Alerta.
export type Variante = 'info' | 'success' | 'warn' | 'danger'

export const ETIQUETA_ESTADO: Record<EstadoLegajo, string> = {
  BORRADOR: 'Borrador',
  PENDIENTE: 'Pendiente',
  EN_REVISION: 'En revisión',
  OBSERVADO: 'Observado',
  COMPLETADO: 'Completado',
  ACTIVO: 'Activo',
  VENCIDO: 'Vencido',
  RECHAZADO: 'Rechazado',
  BAJA: 'Baja',
  GRADUADO: 'Graduado',
}

export const VARIANTE_ESTADO: Record<EstadoLegajo, Variante> = {
  BORRADOR: 'info',
  PENDIENTE: 'warn',
  EN_REVISION: 'info',
  OBSERVADO: 'danger',
  COMPLETADO: 'success',
  ACTIVO: 'success',
  VENCIDO: 'danger',
  RECHAZADO: 'danger',
  BAJA: 'danger',
  GRADUADO: 'success',
}

// Las 6 del coordinador son el texto de sus botones; las otras 4
// solo aparecen en el historial.
export const ETIQUETA_ACCION: Record<AccionLegajo, string> = {
  ENVIAR: 'Enviar',
  REVISAR: 'Pasar a revisión',
  OBSERVAR: 'Observar',
  CORREGIR: 'Corregir',
  APROBAR: 'Aprobar',
  RECHAZAR: 'Rechazar',
  MATRICULAR: 'Matricular',
  VENCER: 'Vencer',
  DAR_DE_BAJA: 'Dar de baja',
  GRADUAR: 'Graduar',
}

// DNI y TITULO_GRADO son los del plan §10; el resto sale de la
// tabla de documentos del SRS (RF-CORE-002) con el mismo estilo.
export const ETIQUETA_DOCUMENTO: Record<TipoDocumento, string> = {
  FORM_INSCRIPCION: 'Formulario de preinscripción firmado',
  DNI: 'Copia del DNI o pasaporte',
  TITULO_GRADO: 'Copia del título de grado',
  PARTIDA: 'Partida de nacimiento',
  CUIT_CUIL: 'Constancia de CUIT/CUIL',
  TITULO_POSGRADO: 'Copia del título de posgrado',
  FORM_BECA: 'Formulario de beca firmado',
}
