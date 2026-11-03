/* ═══════════════════════════════════════════════════════════════
   sesion.ts — DÓNDE SE GUARDA LA SESIÓN DEL COORDINADOR
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Después del login guardamos el token (JWT) y los datos del
   usuario en el navegador:
     · Con "Recordarme" → localStorage: sobrevive aunque cierres
       el navegador.
     · Sin "Recordarme" → sessionStorage: se borra al cerrar la
       pestaña.
   No hay refresh token: el JWT dura 8 horas y, cuando vence, la
   API responde 401 y el cliente nos manda de vuelta al login.
   ═══════════════════════════════════════════════════════════════ */

import type { Usuario } from '../api/tipos'

export type Sesion = {
  token: string
  usuario: Usuario
}

const CLAVE = 'posgrado.sesion'

export function guardarSesion(sesion: Sesion, recordarme: boolean): void {
  // Primero borramos la anterior, así nunca quedan dos sesiones
  // (una en cada almacenamiento).
  borrarSesion()
  const almacen = recordarme ? localStorage : sessionStorage
  almacen.setItem(CLAVE, JSON.stringify(sesion))
}

export function leerSesion(): Sesion | null {
  const texto = localStorage.getItem(CLAVE) ?? sessionStorage.getItem(CLAVE)
  if (!texto) return null
  try {
    return JSON.parse(texto) as Sesion
  } catch {
    // Si alguien tocó el valor a mano y no es JSON, lo descartamos.
    borrarSesion()
    return null
  }
}

export function borrarSesion(): void {
  localStorage.removeItem(CLAVE)
  sessionStorage.removeItem(CLAVE)
}
