/* ═══════════════════════════════════════════════════════════════
   AuthProvider.tsx — EL QUE MANEJA LA SESIÓN
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Envuelve a toda la app (en main.tsx) y guarda en un useState
   quién es el usuario. Al arrancar lo lee de lo que dejó
   sesion.ts, así recargar la página no te saca del sistema.

     · iniciarSesion → POST /auth/login. Si sale bien, guarda el
       token y el usuario y actualiza el estado; si sale mal, el
       ApiError (401 "Email o contraseña incorrectos") llega al
       Login, que lo muestra.
     · cerrarSesion → borra lo guardado y vacía la caché de
       TanStack Query, para que el próximo que entre no vea datos
       del anterior. El back no hace nada: sin token no hay sesión.
   ═══════════════════════════════════════════════════════════════ */

import { useState, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../api/client'
import type { RespuestaLogin, Usuario } from '../api/tipos'
import { AuthContext } from './AuthContext'
import { borrarSesion, guardarSesion, leerSesion } from './sesion'

export default function AuthProvider({ children }: { children: ReactNode }) {
  // La función adentro de useState corre una sola vez, al montar.
  const [usuario, setUsuario] = useState<Usuario | null>(() => leerSesion()?.usuario ?? null)
  const queryClient = useQueryClient()

  async function iniciarSesion(email: string, password: string, recordarme: boolean) {
    const respuesta = await apiFetch<RespuestaLogin>('/auth/login', {
      method: 'POST',
      json: { email, password },
    })
    guardarSesion({ token: respuesta.accessToken, usuario: respuesta.usuario }, recordarme)
    setUsuario(respuesta.usuario)
    return respuesta.usuario
  }

  function cerrarSesion() {
    borrarSesion()
    queryClient.clear()
    setUsuario(null)
  }

  return (
    <AuthContext value={{ usuario, estaAutenticado: usuario !== null, iniciarSesion, cerrarSesion }}>
      {children}
    </AuthContext>
  )
}
