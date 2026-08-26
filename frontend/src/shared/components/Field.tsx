/* ═══════════════════════════════════════════════════════════════
   Field.tsx — ETIQUETA + CAMPO DE FORMULARIO
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Envuelve cualquier campo (input, select, textarea) y le pone
   arriba su etiqueta, con el asterisco rojo si es obligatorio.

   Gracias a este componente, el formulario de inscripción, que
   tiene más de 20 campos, se escribe sin repetir el mismo bloque
   de HTML una y otra vez, y todos los campos quedan alineados
   exactamente igual.
   ═══════════════════════════════════════════════════════════════ */

import type { ReactNode } from 'react'

type Props = {
  label: string
  required?: boolean
  children: ReactNode
  className?: string
}

export default function Field({ label, required, children, className = '' }: Props) {
  return (
    <div className={'flex flex-col gap-1.5 ' + className}>
      <label className="text-[13px] text-muted">
        {label} {required && <span className="text-danger">*</span>}
      </label>
      {children}
    </div>
  )
}