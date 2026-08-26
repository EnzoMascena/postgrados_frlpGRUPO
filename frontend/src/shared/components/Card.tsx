/* ═══════════════════════════════════════════════════════════════
   Card.tsx — TARJETA CONTENEDORA (el bloque blanco con borde)
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Cada sección que ven en pantalla (Datos personales, Documentación,
   la tabla de inscriptos...) es una Card. Recibe un título, un
   ícono opcional y adentro lo que sea (`children`).

   POR QUÉ IMPORTA: si mañana queremos cambiar el borde, la sombra
   o el espaciado de TODAS las secciones del sistema, se toca este
   único archivo. Eso es reutilización real, no copiar y pegar.
   ═══════════════════════════════════════════════════════════════ */

import type { ElementType, ReactNode } from 'react'

type Props = {
  title?: string
  icon?: ElementType
  children: ReactNode
  className?: string
}

export default function Card({ title, icon: Icon, children, className = '' }: Props) {
  return (
    <div className={'bg-card border border-line rounded-card shadow-card p-5 mb-4 ' + className}>
      {title && (
        <div className="flex items-center gap-1.5 text-[13px] font-medium text-ink mb-3.5">
          {Icon && <Icon size={15} stroke={1.5} />}
          {title}
        </div>
      )}
      {children}
    </div>
  )
}