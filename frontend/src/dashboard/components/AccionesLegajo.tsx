/* ═══════════════════════════════════════════════════════════════
   AccionesLegajo.tsx — LOS BOTONES PARA CAMBIAR EL ESTADO
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   El front NO decide qué se puede hacer con un legajo: muestra un
   botón por cada acción de `accionesPermitidas`, que calcula el back
   con la máquina de estados según el estado y el rol. Si mañana
   cambia una regla, cambia en el back y los botones se acomodan
   solos. Y aunque alguien fuerce un pedido, el back lo vuelve a
   validar (409 si la transición no corresponde).

   Cuánto pide cada acción antes de mandarse:
     · Pasar a revisión → nada, un click.
     · Observar         → un comentario obligatorio (5 caracteres o
                          más): es lo que el aspirante tiene que corregir.
     · Aprobar, Matricular → confirmación.
     · Rechazar, Dar de baja → confirmación y comentario opcional.
   ═══════════════════════════════════════════════════════════════ */

import { useState, type FormEvent } from 'react'
import { IconClipboardCheck } from '@tabler/icons-react'
import Card from '../../shared/components/Card'
import Button from '../../shared/components/Button'
import Modal from '../../shared/components/Modal'
import Alerta from '../../shared/components/Alerta'
import { controlClass } from '../../shared/components/controls'
import {
  ETIQUETA_ACCION,
  type AccionLegajo,
  type EstadoLegajo,
  type LegajoDetalle,
} from '../../shared/api/tipos'
import { useCambiarEstado } from '../hooks/useDashboard'

const LARGO_MINIMO_OBSERVACION = 5 // igual que el back (validar_comentario)
const LARGO_MAXIMO_COMENTARIO = 2000

type Pide = 'nada' | 'confirmar' | 'comentario-opcional' | 'comentario-obligatorio'

type Config = {
  pide: Pide
  variante: 'default' | 'primary' | 'danger'
  pregunta?: string
  exito: (legajo: LegajoDetalle) => string
}

const ACCIONES: Partial<Record<AccionLegajo, Config>> = {
  REVISAR: { pide: 'nada', variante: 'primary', exito: () => 'El legajo pasó a revisión.' },
  OBSERVAR: {
    pide: 'comentario-obligatorio',
    variante: 'default',
    pregunta: 'Contale al aspirante qué tiene que corregir. Le llega por email con su link.',
    exito: () => 'Legajo observado: el aspirante recibió el comentario por email.',
  },
  APROBAR: {
    pide: 'confirmar',
    variante: 'primary',
    pregunta: 'Se asigna el número de legajo y el aspirante tiene 30 días para matricularse.',
    exito: (l) => `Legajo aprobado: ${l.numeroLegajo}`,
  },
  RECHAZAR: {
    pide: 'comentario-opcional',
    variante: 'danger',
    pregunta: 'El legajo se cierra y el aspirante recibe un email. No se puede deshacer.',
    exito: () => 'Legajo rechazado.',
  },
  MATRICULAR: {
    pide: 'confirmar',
    variante: 'primary',
    pregunta: 'El aspirante pasa a ser alumno activo de la cohorte.',
    exito: (l) => `Legajo matriculado: ${l.numeroLegajo}`,
  },
  DAR_DE_BAJA: {
    pide: 'comentario-opcional',
    variante: 'danger',
    pregunta: 'El alumno deja de estar activo. No se puede deshacer.',
    exito: () => 'Legajo dado de baja.',
  },
}

// Cuando el coordinador no puede hacer nada, le decimos a qué se espera.
const SIN_ACCIONES: Partial<Record<EstadoLegajo, string>> = {
  BORRADOR: 'El aspirante todavía no envió el legajo.',
  OBSERVADO: 'Esperando que el aspirante corrija lo observado y lo vuelva a enviar.',
}
const SIN_ACCIONES_GENERICO = 'No hay acciones para un legajo en este estado.'

export default function AccionesLegajo({ legajo }: { legajo: LegajoDetalle }) {
  const cambio = useCambiarEstado(legajo.id)
  const [abierta, setAbierta] = useState<AccionLegajo | null>(null)
  const [exito, setExito] = useState<string | null>(null)

  const acciones = (legajo.accionesPermitidas ?? []).filter((a) => ACCIONES[a])

  function mandar(accion: AccionLegajo, comentario: string | null) {
    setExito(null)
    cambio.mutate(
      { accion, comentario },
      {
        onSuccess: (actualizado) => {
          setAbierta(null)
          setExito(ACCIONES[accion]!.exito(actualizado))
        },
      },
    )
  }

  function elegir(accion: AccionLegajo) {
    cambio.reset()
    setExito(null)
    if (ACCIONES[accion]!.pide === 'nada') mandar(accion, null)
    else setAbierta(accion)
  }

  return (
    <Card title="Acciones" icon={IconClipboardCheck}>
      {exito && (
        <Alerta variant="success" className="mb-3">
          {exito}
        </Alerta>
      )}
      {/* El error de una acción sin modal se ve acá; el de las otras, en su modal. */}
      {cambio.error && abierta === null && (
        <Alerta variant="danger" className="mb-3">
          {cambio.error.message}
        </Alerta>
      )}

      {acciones.length === 0 ? (
        <p className="text-[12px] text-muted">{SIN_ACCIONES[legajo.estado] ?? SIN_ACCIONES_GENERICO}</p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {acciones.map((accion) => (
            <Button
              key={accion}
              variant={ACCIONES[accion]!.variante}
              disabled={cambio.isPending}
              onClick={() => elegir(accion)}
              className="disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {cambio.isPending && cambio.variables?.accion === accion
                ? 'Guardando…'
                : ETIQUETA_ACCION[accion]}
            </Button>
          ))}
        </div>
      )}

      <Modal
        abierto={abierta !== null}
        titulo={abierta ? `${ETIQUETA_ACCION[abierta]} el legajo` : ''}
        onCerrar={() => setAbierta(null)}
      >
        {abierta && (
          <ConfirmarAccion
            accion={abierta}
            config={ACCIONES[abierta]!}
            enviando={cambio.isPending}
            error={cambio.error}
            onCancelar={() => setAbierta(null)}
            onConfirmar={(comentario) => mandar(abierta, comentario)}
          />
        )}
      </Modal>
    </Card>
  )
}

function ConfirmarAccion({
  accion,
  config,
  enviando,
  error,
  onCancelar,
  onConfirmar,
}: {
  accion: AccionLegajo
  config: Config
  enviando: boolean
  error: Error | null
  onCancelar: () => void
  onConfirmar: (comentario: string | null) => void
}) {
  const [comentario, setComentario] = useState('')
  const pideComentario = config.pide === 'comentario-obligatorio' || config.pide === 'comentario-opcional'
  const obligatorio = config.pide === 'comentario-obligatorio'
  const corto = obligatorio && comentario.trim().length < LARGO_MINIMO_OBSERVACION

  function confirmar(e: FormEvent) {
    e.preventDefault()
    if (corto) return
    onConfirmar(comentario.trim() || null)
  }

  return (
    <form onSubmit={confirmar} className="flex flex-col gap-3.5">
      {config.pregunta && <p className="text-[12.5px] text-muted">{config.pregunta}</p>}

      {pideComentario && (
        <div>
          <label htmlFor="comentario-accion" className="block text-[12px] text-muted mb-1">
            Comentario{obligatorio ? '' : ' (opcional)'}
          </label>
          <textarea
            id="comentario-accion"
            value={comentario}
            onChange={(e) => setComentario(e.target.value)}
            maxLength={LARGO_MAXIMO_COMENTARIO}
            rows={4}
            required={obligatorio}
            aria-describedby={obligatorio ? 'ayuda-comentario' : undefined}
            className={controlClass + ' resize-y'}
          />
          {obligatorio && (
            <p id="ayuda-comentario" className="text-[11px] text-muted mt-1">
              Al menos {LARGO_MINIMO_OBSERVACION} caracteres.
            </p>
          )}
        </div>
      )}

      {error && <Alerta variant="danger">{error.message}</Alerta>}

      <div className="flex justify-end gap-2">
        <Button type="button" onClick={onCancelar}>
          Cancelar
        </Button>
        <Button
          type="submit"
          variant={config.variante === 'danger' ? 'danger' : 'primary'}
          disabled={enviando || corto}
          className="disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {enviando ? 'Guardando…' : ETIQUETA_ACCION[accion]}
        </Button>
      </div>
    </form>
  )
}
