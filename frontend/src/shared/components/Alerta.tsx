/* ═══════════════════════════════════════════════════════════════
   Alerta.tsx — MENSAJE DE ÉXITO, AVISO O ERROR
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Es donde mostramos el mensaje del back cuando algo sale mal
   ("Email o contraseña incorrectos") o bien ("Legajo aprobado:
   26-001-003"). Tiene las mismas 4 variantes que Badge, cada una
   con su ícono, así el estado no depende solo del color.

   ACCESIBILIDAD: los errores y avisos llevan role="alert", que
   hace que el lector de pantalla los lea apenas aparecen; los
   de éxito o información, role="status", que espera a que
   termine lo que estaba leyendo.

   El texto va en `text-ink` para que se lea bien (contraste
   WCAG); el color de la variante va en el borde y el ícono.
   ═══════════════════════════════════════════════════════════════ */

import type { ElementType, ReactNode } from 'react'
import {
  IconAlertCircle,
  IconAlertTriangle,
  IconCircleCheck,
  IconInfoCircle,
} from '@tabler/icons-react'
import type { Variante } from '../api/tipos'

const estilos: Record<Variante, { caja: string; icono: string; Icono: ElementType }> = {
  info: { caja: 'bg-primary-light border-primary', icono: 'text-primary', Icono: IconInfoCircle },
  success: { caja: 'bg-ok-bg border-ok-border', icono: 'text-ok', Icono: IconCircleCheck },
  warn: { caja: 'bg-warn-bg border-warn-border', icono: 'text-warn', Icono: IconAlertTriangle },
  danger: { caja: 'bg-danger-bg border-danger-border', icono: 'text-danger', Icono: IconAlertCircle },
}

type Props = {
  variant?: Variante
  children: ReactNode
  className?: string
}

export default function Alerta({ variant = 'info', children, className = '' }: Props) {
  const { caja, icono, Icono } = estilos[variant]
  const urgente = variant === 'danger' || variant === 'warn'

  return (
    <div
      role={urgente ? 'alert' : 'status'}
      // En oscuro los fondos de color siguen siendo claros: usamos
      // el de la tarjeta y dejamos el color en el borde y el ícono.
      className={
        'flex items-start gap-2 px-3 py-2.5 rounded-input border text-[12.5px] text-ink dark:bg-card ' +
        caja +
        ' ' +
        className
      }
    >
      <Icono size={16} stroke={1.5} className={'flex-shrink-0 mt-px ' + icono} />
      <div className="min-w-0">{children}</div>
    </div>
  )
}
