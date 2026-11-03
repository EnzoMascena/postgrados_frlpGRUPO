/* ═══════════════════════════════════════════════════════════════
   AuthContext.ts — QUÉ COMPARTE LA SESIÓN CON TODA LA APP
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Un "contexto" de React es una forma de pasarle un dato a
   cualquier componente sin ir pasándolo por props de padre a
   hijo. Acá definimos la forma de ese dato: quién es el usuario
   y las funciones para entrar y salir. Quien lo llena es
   AuthProvider y quien lo lee es el hook useAuth.

   Está en su propio archivo (y no junto al Provider) por la regla
   de Fast Refresh del lint: un .tsx que exporta un componente no
   debería exportar otras cosas.
   ═══════════════════════════════════════════════════════════════ */

import { createContext } from 'react'
import type { Usuario } from '../api/tipos'

export type ValorAuth = {
  usuario: Usuario | null
  estaAutenticado: boolean
  iniciarSesion: (email: string, password: string, recordarme: boolean) => Promise<Usuario>
  cerrarSesion: () => void
}

// Arranca en null: si alguien usa useAuth fuera del Provider, el
// hook lo detecta y avisa con un error claro.
export const AuthContext = createContext<ValorAuth | null>(null)
