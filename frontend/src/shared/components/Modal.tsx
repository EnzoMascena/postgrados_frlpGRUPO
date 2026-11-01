/* ═══════════════════════════════════════════════════════════════
   Modal.tsx — VENTANA EMERGENTE (confirmar, observar, ver un PDF)
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Usamos el elemento <dialog> del navegador con showModal(). Nos
   da gratis lo que pide la accesibilidad (WCAG):
     · Es un diálogo modal para los lectores de pantalla.
     · El foco entra al modal y el resto de la página queda
       inactivo: con Tab no te podés ir "atrás" del modal.
     · Escape lo cierra, y al cerrar el foco vuelve al botón que
       lo abrió.
   Nosotros sumamos el título (aria-labelledby) y cerrar con un
   click en el fondo oscuro.

   Lo controla el padre con `abierto`, igual que un input
   controlado: el modal no decide solo cuándo abrirse.
   ═══════════════════════════════════════════════════════════════ */

import { useEffect, useId, useRef, type ReactNode } from 'react'
import { IconX } from '@tabler/icons-react'

type Props = {
  abierto: boolean
  titulo: string
  onCerrar: () => void
  children: ReactNode
  grande?: boolean // para la vista previa de un PDF
}

export default function Modal({ abierto, titulo, onCerrar, children, grande = false }: Props) {
  const ref = useRef<HTMLDialogElement>(null)
  const idTitulo = useId()
  // Para cerrar con el fondo, el click tiene que EMPEZAR en el fondo:
  // si seleccionás texto adentro y soltás afuera, no se cierra.
  const presionoFondo = useRef(false)

  // Sincroniza el <dialog> con la prop: showModal() lo abre como
  // modal y close() lo cierra.
  useEffect(() => {
    const dialogo = ref.current
    if (!dialogo) return
    if (abierto && !dialogo.open) dialogo.showModal()
    if (!abierto && dialogo.open) dialogo.close()
  }, [abierto])

  return (
    <dialog
      ref={ref}
      aria-labelledby={idTitulo}
      aria-modal="true"
      // Escape lo cierra el navegador; acá le avisamos al padre.
      onClose={() => {
        if (abierto) onCerrar()
      }}
      onMouseDown={(e) => {
        presionoFondo.current = e.target === e.currentTarget
      }}
      onClick={(e) => {
        if (presionoFondo.current && e.target === e.currentTarget) onCerrar()
      }}
      className={
        'm-auto p-0 w-[calc(100%-32px)] rounded-card border border-line bg-card text-ink shadow-card backdrop:bg-sidebar/60 ' +
        (grande ? 'max-w-[900px]' : 'max-w-[440px]')
      }
    >
      <div className="p-5">
        <div className="flex items-center justify-between gap-3 mb-3.5">
          <h2 id={idTitulo} className="text-[14px] font-medium text-ink">
            {titulo}
          </h2>
          <button
            type="button"
            onClick={onCerrar}
            aria-label="Cerrar"
            className="p-1 rounded-input text-faint hover:text-ink hover:bg-surface transition-colors"
          >
            <IconX size={16} stroke={1.5} />
          </button>
        </div>
        {/* El contenido existe solo mientras está abierto: así un
            formulario vuelve a arrancar vacío cada vez. */}
        {abierto && children}
      </div>
    </dialog>
  )
}
