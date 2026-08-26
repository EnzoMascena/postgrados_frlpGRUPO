/* ═══════════════════════════════════════════════════════════════
   Topbar.tsx — BARRA SUPERIOR (la usan las 5 pantallas)
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   La franja de arriba con el título de la pantalla y sus acciones.
   Está en shared/ porque la reutilizan TODAS las pantallas: así
   la app se ve consistente y si cambiamos algo, cambia en todas.

   EL CONCEPTO A NOMBRAR — `children`:
   Cada pantalla le pasa adentro los controles que necesita
   (un botón de exportar, un selector de cohorte, una etiqueta) y
   el Topbar los coloca a la derecha sin saber qué son. Es como
   dejar un "hueco" para que el que lo usa lo rellene. En React
   eso se llama composición.

   El botón de cambiar tema (claro/oscuro) lo agrega el Topbar
   siempre, así no hay que acordarse de ponerlo en cada pantalla.
   ═══════════════════════════════════════════════════════════════ */

import type { ElementType, ReactNode } from 'react'
import ThemeToggle from '../components/ThemeToggle'

type Props = {
  title: string
  icon?: ElementType
  children?: ReactNode
}

export default function Topbar({ title, icon: Icon, children }: Props) {
  return (
    <div className="h-14 flex items-center justify-between gap-3 px-5 bg-card border-b border-line flex-shrink-0">
      <div className="flex items-center gap-1.5 font-medium text-[15px] text-ink truncate">
        {Icon && <Icon size={15} stroke={1.5} />}
        {title}
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        {/* Acá entra lo que cada pantalla haya puesto adentro
            de <Topbar> ... </Topbar>. */}
        {children}
        <ThemeToggle />
      </div>
    </div>
  )
}