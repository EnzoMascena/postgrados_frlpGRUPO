/* ═══════════════════════════════════════════════════════════════
   UploadBox.tsx — CAJA PARA SUBIR UN PDF
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   El recuadro punteado del wireframe, uno por cada documento que
   pide el reglamento. Acepta solo PDF y avisa el límite de tamaño.

   TRUCO DE MAQUETACIÓN: el <input type="file"> real está oculto
   a la vista (sr-only, no display:none: así se llega con Tab y el
   lector de pantalla lo anuncia) y todo el recuadro es un <label>.
   Al hacer click en cualquier parte se abre el explorador de
   archivos. Se hace así porque el input nativo no se puede estilar.

   PROPS OPCIONALES (sin ellas se ve igual que en la entrega 2):
     onArchivo(file) → qué hacer con el archivo elegido. La caja no
                       sube nada: eso lo decide quien la usa.
     estado          → pendiente · subiendo · cargado · error
     nombreArchivo   → el que ya está subido (en "cargado")
     error           → mensaje en rojo debajo, con role="alert"
     deshabilitado   → no deja elegir (legajo de solo lectura)
     faltante        → borde rojo (falta para enviar a revisión)
     id              → para asociar el mensaje de error al input
     acciones        → lo que va al lado del título (estado, "Ver")
   ═══════════════════════════════════════════════════════════════ */

import { useId, type ChangeEvent, type ReactNode } from 'react'
import { IconCircleCheck, IconLoader2, IconUpload } from '@tabler/icons-react'

export type EstadoUpload = 'pendiente' | 'subiendo' | 'cargado' | 'error'

type Props = {
  label: string
  optional?: boolean
  hint?: string
  onArchivo?: (archivo: File) => void
  estado?: EstadoUpload
  nombreArchivo?: string | null
  error?: string | null
  deshabilitado?: boolean
  faltante?: boolean
  id?: string
  acciones?: ReactNode
}

export default function UploadBox({
  label,
  optional,
  hint = 'máx 5 MB',
  onArchivo,
  estado = 'pendiente',
  nombreArchivo,
  error,
  deshabilitado = false,
  faltante = false,
  id,
  acciones,
}: Props) {
  const idAuto = useId()
  const inputId = id ?? idAuto
  const errorId = `${inputId}-error`

  const subiendo = estado === 'subiendo'
  const bloqueado = deshabilitado || subiendo
  const conError = Boolean(error) || estado === 'error'

  function elegir(e: ChangeEvent<HTMLInputElement>) {
    const archivo = e.target.files?.[0]
    // Se vacía para que elegir otra vez el mismo archivo vuelva a disparar onChange.
    e.target.value = ''
    if (archivo) onArchivo?.(archivo)
  }

  const borde = conError || faltante ? 'border-danger-border' : 'border-line-strong'
  const interaccion = bloqueado
    ? 'cursor-not-allowed opacity-70'
    : 'cursor-pointer hover:border-primary focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/30'

  function contenido() {
    if (subiendo) {
      return (
        <>
          <IconLoader2 size={20} stroke={1.5} className="mx-auto mb-1 text-primary animate-spin" />
          <span className="block text-[13px] text-muted">Subiendo…</span>
        </>
      )
    }
    if (estado === 'cargado' && nombreArchivo) {
      return (
        <>
          <IconCircleCheck size={20} stroke={1.5} className="mx-auto mb-1 text-ok" />
          <span className="block text-[13px] text-ink break-all">{nombreArchivo}</span>
          {!deshabilitado && (
            <span className="block text-[11px] text-faint mt-0.5">Elegir otro PDF para reemplazarlo</span>
          )}
        </>
      )
    }
    // Solo lectura y sin archivo: nada que invite a subir.
    if (deshabilitado) return <span className="block text-[13px] text-faint">Sin archivo</span>
    return (
      <>
        <IconUpload size={20} stroke={1.5} className="mx-auto mb-1 text-faint" />
        <span className="block text-[13px] text-muted">Seleccionar archivo PDF</span>
        <span className="block text-[11px] text-faint mt-0.5">{hint}</span>
      </>
    )
  }

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between gap-2 min-h-5">
        <span className="text-[13px] text-muted">
          {label} {optional && <span className="text-faint">(opcional)</span>}
        </span>
        {acciones && <div className="flex items-center gap-2 flex-shrink-0">{acciones}</div>}
      </div>
      <label
        className={
          'border border-dashed rounded-input p-3 text-center bg-surface transition-colors ' +
          borde +
          ' ' +
          interaccion
        }
      >
        <input
          id={inputId}
          type="file"
          // El .pdf ayuda donde el sistema no conoce el tipo MIME.
          accept="application/pdf,.pdf"
          className="sr-only"
          disabled={bloqueado}
          aria-label={label}
          aria-invalid={conError || undefined}
          aria-describedby={error ? errorId : undefined}
          onChange={elegir}
        />
        {contenido()}
      </label>
      {error && (
        <p id={errorId} role="alert" className="text-[12px] text-danger">
          {error}
        </p>
      )}
    </div>
  )
}
