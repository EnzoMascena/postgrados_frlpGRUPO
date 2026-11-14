/* ═══════════════════════════════════════════════════════════════
   EnviarRevision.tsx — ENVIAR A REVISIÓN O REENVIAR LA CORRECCIÓN
   (US-CORE-004)
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Es el último paso del aspirante. Solo aparece cuando el legajo
   se puede enviar: en Borrador ("Enviar a revisión") o en
   Observado ("Reenviar corrección"). En los demás estados ya lo
   está mirando la Secretaría y no hay nada que mandar.

   EL BOTÓN SE DESHABILITA SOLO: la lista de lo que falta no la
   calculamos en el front, la manda el back en
   `documentosFaltantes` (GET /seguimiento/{token}). Cuando el
   aspirante sube un PDF, TanStack Query vuelve a pedir el legajo,
   la lista se achica y, con la lista vacía, el botón se habilita.
   Así la regla de "qué es obligatorio" vive en un solo lugar.

   Al hacer clic no se manda nada todavía: se abre un Modal para
   confirmar, porque después de enviar ya no puede cambiar sus
   datos ni sus PDFs. El envío en sí (POST) lo hace el padre con
   `onConfirmar`: este componente solo muestra y pregunta.

   El back igual vuelve a controlar los documentos: si entre medio
   faltara uno, responde 422 DOCUMENTOS_FALTANTES y el padre nos
   pasa ese mensaje en `error`.
   ═══════════════════════════════════════════════════════════════ */

import { useId, useState } from 'react'
import { IconAlertCircle, IconSend } from '@tabler/icons-react'
import Alerta from '../../shared/components/Alerta'
import Button from '../../shared/components/Button'
import Card from '../../shared/components/Card'
import Modal from '../../shared/components/Modal'
import type { LegajoDetalle } from '../../shared/api/tipos'

type Props = {
  legajo: LegajoDetalle
  /** Hace el POST /seguimiento/{token}/enviar. */
  onConfirmar: () => void
  enviando: boolean
  /** El mensaje del back si el envío falló (por ejemplo, 422 DOCUMENTOS_FALTANTES). */
  error: string | null
}

export default function EnviarRevision({ legajo, onConfirmar, enviando, error }: Props) {
  const [confirmando, setConfirmando] = useState(false)
  const idFaltantes = useId()

  const esCorreccion = legajo.estado === 'OBSERVADO'
  // Los nombres salen de `documentos`, que trae "Copia del título de grado" para TITULO_GRADO.
  const faltantes = legajo.documentosFaltantes.map(
    (tipo) => legajo.documentos.find((d) => d.tipo === tipo)?.nombre ?? tipo,
  )
  const hayFaltantes = faltantes.length > 0

  const texto = esCorreccion ? 'Reenviar corrección' : 'Enviar a revisión'

  function confirmar() {
    setConfirmando(false)
    onConfirmar()
  }

  return (
    <Card title={texto} icon={IconSend}>
      <p className="text-[12px] text-muted -mt-1.5 mb-3.5">
        {esCorreccion
          ? 'Cuando hayas corregido lo que te pedimos, reenviá tu legajo para que la Secretaría lo vuelva a revisar.'
          : 'Cuando tengas todos los documentos obligatorios, enviá tu preinscripción para que la Secretaría la revise.'}
      </p>

      <div className="flex flex-col sm:flex-row sm:items-start gap-3">
        <Button
          variant="primary"
          // Deshabilitado también mientras se envía: un doble clic no manda dos veces.
          disabled={hayFaltantes || enviando}
          aria-describedby={hayFaltantes ? idFaltantes : undefined}
          onClick={() => setConfirmando(true)}
          className="self-start disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-primary disabled:hover:border-primary"
        >
          <IconSend size={15} stroke={1.5} aria-hidden />
          {enviando ? 'Enviando…' : texto}
        </Button>

        {hayFaltantes && (
          <div id={idFaltantes} className="text-[12px] text-danger">
            <p className="flex items-center gap-1 font-medium">
              <IconAlertCircle size={14} stroke={1.5} aria-hidden />
              {faltantes.length === 1
                ? 'Para enviar falta este documento:'
                : `Para enviar faltan estos ${faltantes.length} documentos:`}
            </p>
            <ul className="mt-1 ml-[18px] list-disc">
              {faltantes.map((nombre) => (
                <li key={nombre}>{nombre}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {error && (
        <Alerta variant="danger" className="mt-3.5">
          {error}
        </Alerta>
      )}

      <Modal
        abierto={confirmando}
        titulo={esCorreccion ? '¿Reenviar tu corrección?' : '¿Enviar tu preinscripción a revisión?'}
        onCerrar={() => setConfirmando(false)}
      >
        <p className="text-[13px] text-ink">
          Después de enviarla no vas a poder cambiar tus datos ni tus documentos, salvo que la
          Secretaría te pida una corrección.
        </p>
        <p className="text-[12px] text-muted mt-1.5">
          Te vamos a mandar un email con tu código de seguimiento{' '}
          <span className="font-mono font-medium text-ink">{legajo.codigoSeguimiento}</span>.
        </p>
        <div className="flex justify-end gap-2 mt-5">
          <Button type="button" onClick={() => setConfirmando(false)}>
            Cancelar
          </Button>
          <Button type="button" variant="primary" onClick={confirmar}>
            {esCorreccion ? 'Sí, reenviar' : 'Sí, enviar'}
          </Button>
        </div>
      </Modal>
    </Card>
  )
}
