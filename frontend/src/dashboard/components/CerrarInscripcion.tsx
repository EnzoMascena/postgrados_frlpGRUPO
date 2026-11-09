/* ═══════════════════════════════════════════════════════════════
   CerrarInscripcion.tsx — CONFIRMAR EL CIERRE DEL PERÍODO
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Abrir la inscripción es un click; cerrarla pide confirmación,
   porque desde ese momento ningún aspirante nuevo puede empezar
   su preinscripción en esa cohorte.

   La próxima apertura es opcional: si se carga, el formulario de
   inscripción la muestra en el aviso de "Inscripción cerrada". El
   input de fecha no deja elegir días pasados (`min`), y si igual
   llega una, el back responde 422 y el mensaje se ve acá.
   ═══════════════════════════════════════════════════════════════ */

import { useState, type FormEvent } from 'react'
import Modal from '../../shared/components/Modal'
import Alerta from '../../shared/components/Alerta'
import Button from '../../shared/components/Button'
import { controlClass } from '../../shared/components/controls'
import { hoyEnArgentina } from '../../inscripcion/periodo'

type Props = {
  abierto: boolean
  cohorte: string
  enviando: boolean
  error: Error | null
  onCerrar: () => void
  onConfirmar: (proximaApertura: string | null) => void
}

export default function CerrarInscripcion({ abierto, onCerrar, ...resto }: Props) {
  return (
    <Modal abierto={abierto} titulo="Cerrar la inscripción" onCerrar={onCerrar}>
      {/* El formulario vive adentro del Modal: como el Modal solo
          dibuja su contenido mientras está abierto, la fecha vuelve
          a arrancar vacía cada vez. */}
      <FormularioCierre onCerrar={onCerrar} {...resto} />
    </Modal>
  )
}

function FormularioCierre({
  cohorte,
  enviando,
  error,
  onCerrar,
  onConfirmar,
}: Omit<Props, 'abierto'>) {
  const [fecha, setFecha] = useState('')

  function confirmar(e: FormEvent) {
    e.preventDefault()
    onConfirmar(fecha || null)
  }

  return (
    <form onSubmit={confirmar} className="flex flex-col gap-3.5">
      <p className="text-[12.5px] text-muted">
        Desde ahora nadie va a poder empezar una preinscripción en la {cohorte}. Los que ya
        la empezaron pueden seguir con su link.
      </p>

      <div>
        <label htmlFor="proxima-apertura" className="block text-[12px] text-muted mb-1">
          Próxima apertura (opcional)
        </label>
        <input
          id="proxima-apertura"
          type="date"
          value={fecha}
          min={hoyEnArgentina()}
          onChange={(e) => setFecha(e.target.value)}
          className={controlClass}
        />
      </div>

      {error && <Alerta variant="danger">{error.message}</Alerta>}

      <div className="flex justify-end gap-2">
        <Button type="button" onClick={onCerrar}>
          Cancelar
        </Button>
        <Button type="submit" variant="danger" disabled={enviando}>
          {enviando ? 'Cerrando…' : 'Cerrar inscripción'}
        </Button>
      </div>
    </form>
  )
}
