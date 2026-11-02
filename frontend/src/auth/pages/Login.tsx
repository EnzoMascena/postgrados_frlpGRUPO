/* ═══════════════════════════════════════════════════════════════
   Login.tsx — PANTALLA DE INICIO DE SESIÓN
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Primera pantalla que ve el coordinador. Ahora sí valida contra
   el back: manda email y contraseña a POST /auth/login y, si
   están bien, guarda el token (JWT) y entra al sistema.

   EL RECORRIDO DE UN LOGIN:
     1) El formulario controla email, clave y "Recordarme" con
        useState (como cualquier input controlado de React).
     2) Al enviar, useMutation de TanStack Query llama a
        iniciarSesion (useAuth) → apiFetch → POST /auth/login.
        La mutación nos da isPending (el botón dice "Ingresando…")
        y error (el mensaje del back en una Alerta).
     3) Si sale bien, AuthProvider guarda la sesión y actualiza el
        usuario. Esta pantalla ve que ya hay usuario y redirige
        sola a donde quería ir (o al dashboard).

   POR QUÉ NO HACE navigate() DESPUÉS DEL LOGIN:
   React Router aplica los cambios de URL como "transición" (con
   menos prioridad) y el usuario nuevo se aplica enseguida. Si
   hubiera dos caminos para redirigir, competirían. Con uno solo
   (el <Navigate> de abajo) el resultado es siempre el mismo, y
   además cubre al que entra a /login con la sesión ya iniciada.

   DISEÑO: tarjeta partida en dos paneles → izquierda la marca
   institucional (UTN · FRLP), derecha el formulario. En el
   celular se ve solo el formulario.
   ═══════════════════════════════════════════════════════════════ */

import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useSearchParams } from 'react-router'
import { useMutation } from '@tanstack/react-query'
import { IconSchool, IconEye, IconEyeOff } from '@tabler/icons-react'
import Button from '../../shared/components/Button'
import Alerta from '../../shared/components/Alerta'
import ThemeToggle from '../../shared/components/ThemeToggle'
import { controlClass } from '../../shared/components/controls'
import { ApiError } from '../../shared/api/client'
import { useAuth } from '../../shared/auth/useAuth'

export default function Login() {
  const { usuario, iniciarSesion } = useAuth()
  const location = useLocation()
  const [params] = useSearchParams()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [recordarme, setRecordarme] = useState(false)
  const [verClave, setVerClave] = useState(false)
  const [mostrarAyuda, setMostrarAyuda] = useState(false)

  const ingresar = useMutation({
    mutationFn: () => iniciarSesion(email.trim(), password, recordarme),
  })

  // Con sesión iniciada no hay nada que hacer acá: va a la pantalla
  // que quería ver (RutaProtegida la guardó en `desde`) o al dashboard.
  if (usuario) {
    const desde = (location.state as { desde?: string } | null)?.desde
    return <Navigate to={desde ?? '/coordinador'} replace />
  }

  function enviar(e: FormEvent<HTMLFormElement>) {
    e.preventDefault() // sin esto, el navegador recargaría la página
    ingresar.mutate()
  }

  // El cliente de la API mandó acá con ?vencida=1 porque el token
  // venció. El aviso se va cuando vuelve a intentar.
  const sesionVencida = params.get('vencida') === '1' && ingresar.isIdle
  const mensajeDeError =
    ingresar.error instanceof ApiError
      ? ingresar.error.mensaje
      : 'Ocurrió un error inesperado. Probá de nuevo en unos minutos.'

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-white dark:bg-page p-6">
      {/* Botón de tema, arriba a la derecha */}
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>

      <div className="flex w-full max-w-[500px] rounded-xl overflow-hidden border border-line-strong shadow-[0_18px_40px_rgba(15,23,42,0.18),0_6px_14px_rgba(15,23,42,0.10)]">

        {/* Panel izquierdo — marca (se oculta en pantallas chicas) */}
        <div className="hidden sm:flex w-2/5 bg-sidebar p-6 flex-col justify-between">
          <div>
            <div className="text-[11px] uppercase tracking-wider text-faint mb-2">UTN · FRLP</div>
            <div className="text-[19px] font-medium text-on-dark leading-tight">
              Sistema de Posgrado
            </div>
            <div className="text-[12.5px] text-faint mt-3 leading-relaxed">
              Preinscripción, cursado y graduación en un solo lugar.
            </div>
          </div>
          <div className="w-10 h-10 rounded-[10px] bg-primary flex items-center justify-center mt-6">
            <IconSchool size={22} stroke={1.5} className="text-on-dark" />
          </div>
        </div>

        {/* Panel derecho — formulario */}
        <form onSubmit={enviar} className="flex-1 bg-card sm:border-l border-line-strong p-6">
          <h1 className="text-[18px] font-medium text-ink">Iniciar sesión</h1>
          <div className="text-[12.5px] text-muted mt-1 mb-6">
            Ingresá con tu cuenta institucional.
          </div>

          {sesionVencida && (
            <Alerta variant="warn" className="mb-4">
              Tu sesión venció, volvé a ingresar.
            </Alerta>
          )}
          {ingresar.isError && (
            <Alerta variant="danger" className="mb-4">
              {mensajeDeError}
            </Alerta>
          )}

          <div className="mb-4">
            <label htmlFor="login-email" className="block text-[12.5px] text-muted mb-1.5">
              Correo electrónico
            </label>
            <input
              id="login-email"
              type="email"
              required
              autoComplete="username"
              placeholder="nombre@frlp.utn.edu.ar"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={controlClass}
            />
          </div>

          <div className="mb-3">
            <label htmlFor="login-clave" className="block text-[12.5px] text-muted mb-1.5">
              Contraseña
            </label>
            <div className="relative">
              {/* Mismo estilo que los demás campos (controlClass), con
                  lugar a la derecha para el ojito. */}
              <input
                id="login-clave"
                type={verClave ? 'text' : 'password'}
                required
                autoComplete="current-password"
                placeholder="Ingresá tu contraseña"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={controlClass + ' pr-10'}
              />
              <button
                type="button"
                onClick={() => setVerClave((v) => !v)}
                aria-label={verClave ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded-input text-faint hover:text-ink transition-colors"
              >
                {verClave ? <IconEyeOff size={16} stroke={1.5} /> : <IconEye size={16} stroke={1.5} />}
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between gap-3 mb-5">
            <label
              htmlFor="login-recordarme"
              className="flex items-center gap-1.5 text-[12.5px] text-ink cursor-pointer"
            >
              <input
                id="login-recordarme"
                type="checkbox"
                checked={recordarme}
                onChange={(e) => setRecordarme(e.target.checked)}
                className="w-3.5 h-3.5"
              />
              Recordarme
            </label>
            {/* En el Core no hay recuperación de contraseña: la da la
                Secretaría. Es un botón (no un link) porque no navega. */}
            <button
              type="button"
              onClick={() => setMostrarAyuda((v) => !v)}
              aria-expanded={mostrarAyuda}
              className="text-[12.5px] text-primary hover:underline"
            >
              ¿Olvidaste tu contraseña?
            </button>
          </div>

          {mostrarAyuda && (
            <Alerta variant="info" className="mb-5">
              Pedile una nueva a la Secretaría de Posgrado.
            </Alerta>
          )}

          <Button
            type="submit"
            variant="primary"
            disabled={ingresar.isPending}
            className="w-full disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {ingresar.isPending ? 'Ingresando…' : 'Ingresar'}
          </Button>

          <div className="h-px bg-line my-[18px]" />

          {/* Atajo para el aspirante, que no tiene cuenta: va directo
              al formulario de preinscripción. */}
          <div className="text-[12.5px] text-muted text-center">
            ¿Sos aspirante?{' '}
            <Link to="/inscripcion" className="text-primary hover:underline">
              Preinscribite acá
            </Link>
          </div>
        </form>

      </div>
    </div>
  )
}
