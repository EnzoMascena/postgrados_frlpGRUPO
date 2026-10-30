/* ═══════════════════════════════════════════════════════════════
   Login.tsx — PANTALLA DE INICIO DE SESIÓN
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Primera pantalla que ve el usuario. Es la puerta de entrada
   al sistema y separa los tres perfiles del sistema (aspirante,
   conducción y docentes).

   IMPORTANTE ACLARARLE AL PROFESOR:
   Todavía NO valida usuario ni contraseña: "Ingresar" lleva
   directo al dashboard. La autenticación real (usuario,
   contraseña, token) entra cuando conectemos el login del back.

   CÓMO NAVEGA:
   Antes recibía de App una función `onLogin` y App cambiaba su
   useState. Ahora cambia la URL con `useNavigate()` de React
   Router, y App muestra la pantalla de esa ruta.

   DISEÑO: tarjeta partida en dos paneles → izquierda la marca
   institucional (UTN · FRLP), derecha el formulario.
   ═══════════════════════════════════════════════════════════════ */

import { Link, useNavigate } from 'react-router'
import { IconSchool, IconEye } from '@tabler/icons-react'
import Button from '../../shared/components/Button'
import ThemeToggle from '../../shared/components/ThemeToggle'
import { controlClass } from '../../shared/components/controls'

export default function Login() {
  const navigate = useNavigate()

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-white dark:bg-page p-6">
      {/* Botón de tema, arriba a la derecha */}
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>

      <div className="flex w-full max-w-[500px] rounded-xl overflow-hidden border border-line-strong shadow-[0_18px_40px_rgba(15,23,42,0.18),0_6px_14px_rgba(15,23,42,0.10)]">

        {/* Panel izquierdo — marca */}
        <div className="w-2/5 bg-sidebar p-6 flex flex-col justify-between">
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
        <div className="flex-1 bg-card border-l border-line-strong p-6">
          <div className="text-[18px] font-medium text-ink">Iniciar sesión</div>
          <div className="text-[12.5px] text-muted mt-1 mb-6">
            Ingresá con tu cuenta institucional.
          </div>

          <div className="mb-4">
            <label className="block text-[12.5px] text-muted mb-1.5">Correo electrónico</label>
            <input type="email" placeholder="nombre@frlp.utn.edu.ar" className={controlClass} />
          </div>

          <div className="mb-3">
            <label className="block text-[12.5px] text-muted mb-1.5">Contraseña</label>
            <div className="relative">
              <input
                type="password"
                placeholder="Ingresá tu contraseña"
                className="w-full pl-3 pr-10 py-2 rounded-input border border-line-strong bg-surface text-ink text-[13px] placeholder:text-faint focus:outline-none focus:border-primary transition-colors"
              />
              <IconEye
                size={16}
                stroke={1.5}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-faint"
              />
            </div>
          </div>

          <div className="flex items-center justify-between mb-5">
            <label className="flex items-center gap-1.5 text-[12.5px] text-ink cursor-pointer">
              <input type="checkbox" className="w-3.5 h-3.5" /> Recordarme
            </label>
            <a
              href="#"
              onClick={(e) => e.preventDefault()}
              className="text-[12.5px] text-primary hover:underline"
            >
              ¿Olvidaste tu contraseña?
            </a>
          </div>

          {/* Botón principal: por ahora va al dashboard sin validar. */}
          <Button variant="primary" className="w-full" onClick={() => navigate('/coordinador')}>
            Ingresar
          </Button>

          <div className="h-px bg-line my-[18px]" />

          {/* Atajo para el aspirante que todavía no tiene cuenta:
              entra directo al formulario de preinscripción. */}
          <div className="text-[12.5px] text-muted text-center">
            ¿Sos aspirante?{' '}
            <Link to="/inscripcion" className="text-primary hover:underline">
              Preinscribite acá
            </Link>
          </div>
        </div>

      </div>
    </div>
  )
}