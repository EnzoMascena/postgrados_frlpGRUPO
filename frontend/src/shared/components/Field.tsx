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

   DOS PROPS OPCIONALES (si no se pasan, se ve igual que antes):
     htmlFor → el id del input. Une la etiqueta con su campo: al
               tocar la etiqueta se enfoca el input, y el lector de
               pantalla lee "Apellido, obligatorio" (NFR-U03).
     error   → el mensaje en rojo debajo del campo. role="alert"
               hace que el lector de pantalla lo anuncie apenas
               aparece. Su id es "{htmlFor}-error", para que el
               input lo apunte con aria-describedby.
   ═══════════════════════════════════════════════════════════════ */

import type { ReactNode } from 'react'

type Props = {
  label: string
  required?: boolean
  children: ReactNode
  className?: string
  htmlFor?: string
  error?: string | null
}

export default function Field({ label, required, children, className = '', htmlFor, error }: Props) {
  return (
    <div className={'flex flex-col gap-1.5 ' + className}>
      <label htmlFor={htmlFor} className="text-[13px] text-muted">
        {label} {required && <span className="text-danger">*</span>}
      </label>
      {children}
      {error && (
        <p id={htmlFor ? `${htmlFor}-error` : undefined} role="alert" className="text-[12px] text-danger">
          {error}
        </p>
      )}
    </div>
  )
}
