/* ═══════════════════════════════════════════════════════════════
   Seguimiento.tsx — SEGUIMIENTO DE LA PREINSCRIPCIÓN (aspirante)
   ───────────────────────────────────────────────────────────────
   Stub: existe para que la ruta /seguimiento/:token ya funcione.
   La pantalla real (estado, PDFs y enviar) la arma Gero.
   ═══════════════════════════════════════════════════════════════ */

import { IconListSearch } from '@tabler/icons-react'
import Topbar from '../../shared/layout/Topbar'
import Card from '../../shared/components/Card'

export default function Seguimiento() {
  return (
    <>
      <Topbar title="Seguimiento de la preinscripción" icon={IconListSearch} />
      <div className="p-5">
        <Card>
          <p className="text-[13px] text-muted">En construcción.</p>
        </Card>
      </div>
    </>
  )
}
