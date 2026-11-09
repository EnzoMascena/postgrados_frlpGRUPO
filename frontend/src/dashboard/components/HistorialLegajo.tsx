/* ═══════════════════════════════════════════════════════════════
   HistorialLegajo.tsx — LÍNEA DE TIEMPO DEL LEGAJO
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Cada cambio de estado queda en la auditoría del back (quién,
   cuándo, de qué estado a cuál y con qué comentario) y nunca se
   borra. Acá se muestra de la más vieja a la más nueva, así se lee
   como la historia del legajo: lo envió, lo revisaron, lo
   observaron, lo corrigió...

   "Quién": el email del coordinador, o "Aspirante" / "Sistema"
   cuando no hay un usuario detrás (el aspirante entra con su link
   y el vencimiento lo hace la tarea diaria).
   ═══════════════════════════════════════════════════════════════ */

import { IconArrowRight, IconHistory } from '@tabler/icons-react'
import Card from '../../shared/components/Card'
import EstadoBadge from '../../shared/components/EstadoBadge'
import { ETIQUETA_ACCION, type ItemHistorial } from '../../shared/api/tipos'
import { fechaHora } from '../formato'

function quien(item: ItemHistorial): string {
  if (item.usuarioEmail) return item.usuarioEmail
  if (item.rol === 'ASPIRANTE') return 'Aspirante'
  if (item.rol === 'SISTEMA') return 'Sistema'
  return item.rol
}

export default function HistorialLegajo({ historial }: { historial: ItemHistorial[] }) {
  return (
    <Card title="Historial" icon={IconHistory}>
      {historial.length === 0 ? (
        <p className="text-[12px] text-muted">
          Todavía no hay cambios: el aspirante no envió el legajo.
        </p>
      ) : (
        <ol className="relative border-l border-line ml-1.5">
          {historial.map((item, i) => (
            <li key={`${item.fecha}-${i}`} className="pl-4 pb-4 last:pb-0 relative">
              <span
                aria-hidden="true"
                className="absolute -left-[5px] top-1 w-2.5 h-2.5 rounded-full bg-primary"
              />
              <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                <span className="text-[12.5px] font-medium text-ink">
                  {ETIQUETA_ACCION[item.accion]}
                </span>
                <EstadoBadge estado={item.estadoAnterior} />
                <IconArrowRight size={12} stroke={1.5} className="text-faint" aria-label="a" />
                <EstadoBadge estado={item.estadoNuevo} />
              </div>
              <div className="text-[11px] text-muted mt-0.5">
                <time dateTime={item.fecha}>{fechaHora(item.fecha)}</time> · {quien(item)}
              </div>
              {item.comentario && (
                <p className="text-[12px] text-ink mt-1 px-2.5 py-1.5 rounded-input bg-surface whitespace-pre-line">
                  {item.comentario}
                </p>
              )}
            </li>
          ))}
        </ol>
      )}
    </Card>
  )
}
