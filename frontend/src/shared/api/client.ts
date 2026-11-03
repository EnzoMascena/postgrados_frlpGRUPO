/* ═══════════════════════════════════════════════════════════════
   client.ts — EL ÚNICO LUGAR QUE HABLA CON LA API
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Ningún componente hace fetch suelto: todos los pedidos pasan
   por apiFetch (o apiDescargar, para archivos). Así hay un solo
   lugar donde se resuelve lo que se repite en cada pedido:
     1) Le pone el prefijo /api/v1 a la ruta.
     2) Si hay sesión, agrega "Authorization: Bearer <token>".
     3) Si le pasamos `json`, lo convierte a texto y avisa que
        manda JSON. Un FormData (subir un PDF) pasa sin tocar: el
        navegador arma solo el Content-Type multipart.
     4) Si la respuesta no es 2xx, lee el error del back (formato
        del plan §10) y lo tira como ApiError, con el mensaje en
        español listo para mostrar en pantalla.
     5) Si es un 401 y había sesión, el token venció: borra la
        sesión y vuelve al login con un aviso.

   CAMINO DE UN PEDIDO: componente → hook de TanStack Query →
   apiFetch → proxy de Vite (/api) → FastAPI → base de datos, y
   la respuesta vuelve por el mismo camino.
   ═══════════════════════════════════════════════════════════════ */

import { borrarSesion, leerSesion } from '../auth/sesion'

const PREFIJO = '/api/v1'

const MENSAJE_GENERICO = 'Ocurrió un error inesperado. Probá de nuevo en unos minutos.'
const MENSAJE_SIN_CONEXION =
  'No pudimos conectarnos con el servidor. Revisá tu conexión y probá de nuevo.'

/** Error de la API, con los datos del cuerpo de error del back. */
export class ApiError extends Error {
  status: number // código HTTP (0 si ni siquiera hubo respuesta)
  codigo: string // el campo `error`: "CONFLICT", "TRANSICION_INVALIDA"...
  mensaje: string // el campo `message`, en español
  campo: string | null // el campo `field`: qué input marcar en rojo

  constructor(status: number, codigo: string, mensaje: string, campo: string | null = null) {
    super(mensaje)
    this.name = 'ApiError'
    this.status = status
    this.codigo = codigo
    this.mensaje = mensaje
    this.campo = campo
  }
}

// Lo mismo que acepta fetch, más `json` para mandar un objeto.
export type OpcionesApi = RequestInit & { json?: unknown }

// Cuerpo de error del plan §10.
type CuerpoError = {
  statusCode: number
  error: string
  message: string
  field: string | null
}

async function leerError(respuesta: Response): Promise<ApiError> {
  try {
    const cuerpo = (await respuesta.json()) as Partial<CuerpoError>
    if (cuerpo.message) {
      return new ApiError(
        respuesta.status,
        cuerpo.error ?? 'ERROR',
        cuerpo.message,
        cuerpo.field ?? null,
      )
    }
  } catch {
    // Sin cuerpo o no es JSON: usamos el mensaje genérico.
  }
  return new ApiError(respuesta.status, 'ERROR', MENSAJE_GENERICO)
}

// Hace el pedido y devuelve la respuesta solo si salió bien.
async function pedir(ruta: string, opciones: OpcionesApi = {}): Promise<Response> {
  const { json, headers, ...resto } = opciones
  const encabezados = new Headers(headers)

  const sesion = leerSesion()
  if (sesion) encabezados.set('Authorization', `Bearer ${sesion.token}`)

  if (json !== undefined) {
    encabezados.set('Content-Type', 'application/json')
    resto.body = JSON.stringify(json)
  }

  let respuesta: Response
  try {
    respuesta = await fetch(PREFIJO + ruta, { ...resto, headers: encabezados })
  } catch {
    // fetch solo falla así si no hubo respuesta (sin red, back caído).
    throw new ApiError(0, 'SIN_CONEXION', MENSAJE_SIN_CONEXION)
  }

  if (!respuesta.ok) {
    // 401 con sesión = el token venció o es inválido. Recargamos la
    // app en el login: así también se vacía la caché de TanStack
    // Query y no queda nada del usuario anterior en memoria.
    if (respuesta.status === 401 && sesion) {
      borrarSesion()
      window.location.assign('/login?vencida=1')
    }
    throw await leerError(respuesta)
  }
  return respuesta
}

/** Pide JSON a la API. Ej.: apiFetch<Cohorte[]>('/cohortes') */
export async function apiFetch<T>(ruta: string, opciones?: OpcionesApi): Promise<T> {
  const respuesta = await pedir(ruta, opciones)
  if (respuesta.status === 204) return undefined as T // sin contenido
  return (await respuesta.json()) as T
}

/** Baja un archivo (PDF o Excel) con el token, sin URL directa. */
export async function apiDescargar(ruta: string): Promise<{ blob: Blob; nombreArchivo: string }> {
  const respuesta = await pedir(ruta)
  return {
    blob: await respuesta.blob(),
    nombreArchivo: nombreDesdeDisposition(respuesta.headers.get('Content-Disposition')),
  }
}

// Saca el nombre de un encabezado como
//   attachment; filename="inscriptos-cohorte2026-2026-11-08.xlsx"
//   attachment; filename*=utf-8''t%C3%ADtulo.pdf  (con acentos)
function nombreDesdeDisposition(valor: string | null): string {
  if (valor) {
    const conAcentos = /filename\*=utf-8''([^;]+)/i.exec(valor)
    if (conAcentos) return decodeURIComponent(conAcentos[1])
    const simple = /filename="?([^";]+)"?/i.exec(valor)
    if (simple) return simple[1]
  }
  return 'descarga'
}
