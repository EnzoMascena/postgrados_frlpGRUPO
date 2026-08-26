/* ═══════════════════════════════════════════════════════════════
   ListaTutorias.tsx — HISTORIAL DE TUTORÍAS (usado en Legajo)
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Lista las reuniones del estudiante con su director/a de TFI:
   fecha, tema y un detalle. Hoy ese seguimiento se lleva por mail
   o en papel y se pierde; acá queda registrado en el legajo.

   Recibe las tutorías por props (no las busca ella misma) y las
   recorre con .map() para dibujar una tarjetita por cada una.
   Si no hay ninguna, muestra un mensaje en vez de un hueco vacío.
   ═══════════════════════════════════════════════════════════════ */

import { IconPlus } from '@tabler/icons-react'
import Button from '../../shared/components/Button'
import type { Tutoria } from '../types'

type Props = {
  tutorias: Tutoria[]
}

export default function ListaTutorias({ tutorias }: Props) {
  return (
    <>
      <div className="flex flex-col gap-2">
        {tutorias.map((t) => (
          <div key={t.id} className="bg-surface rounded-input p-2.5 text-[12px]">
            <div className="font-medium text-ink mb-0.5">
              {t.fecha} — {t.titulo}
            </div>
            <div className="text-muted">{t.detalle}</div>
          </div>
        ))}

        {tutorias.length === 0 && (
          <div className="text-[12px] text-muted text-center py-4">
            Todavía no hay tutorías registradas.
          </div>
        )}
      </div>

      <Button className="w-full mt-2.5 text-[11px]">
        <IconPlus size={13} stroke={1.5} /> Registrar tutoría
      </Button>
    </>
  )
}