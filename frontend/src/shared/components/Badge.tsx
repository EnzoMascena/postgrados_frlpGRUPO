/* ═══════════════════════════════════════════════════════════════
   Badge.tsx — ETIQUETA DE ESTADO (las píldoras de colores)
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Son las etiquetas redondeadas que muestran estados: "Completo",
   "Incompleto", "Aprobado", "Libre", "Período abierto".

   El color transmite el significado y es el MISMO en todo el
   sistema, así el usuario aprende el código de una sola vez:
     info (azul) · success (verde) · warn (amarillo) · danger (rojo)
   ═══════════════════════════════════════════════════════════════ */

import type { ReactNode } from 'react'

type Variant = 'info' | 'success' | 'warn' | 'danger'

const styles: Record<Variant, string> = {
  info: 'bg-primary-light text-primary',
  success: 'bg-ok-bg text-ok',
  warn: 'bg-warn-bg text-warn',
  danger: 'bg-danger-bg text-danger',
}

export default function Badge({
  variant = 'info',
  children,
}: {
  variant?: Variant
  children: ReactNode
}) {
  return (
    <span
      className={
        'inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium whitespace-nowrap ' +
        styles[variant]
      }
    >
      {children}
    </span>
  )
}