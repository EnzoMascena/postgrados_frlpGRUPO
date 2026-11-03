/* ═══════════════════════════════════════════════════════════════
   useAuth.ts — CÓMO UN COMPONENTE LEE LA SESIÓN
   ───────────────────────────────────────────────────────────────
   Uso: const { usuario, iniciarSesion, cerrarSesion } = useAuth()
   ═══════════════════════════════════════════════════════════════ */

import { useContext } from 'react'
import { AuthContext, type ValorAuth } from './AuthContext'

export function useAuth(): ValorAuth {
  const valor = useContext(AuthContext)
  if (!valor) throw new Error('useAuth tiene que usarse dentro de <AuthProvider>')
  return valor
}
