/* ═══════════════════════════════════════════════════════════════
   DetalleLegajo.tsx — DETALLE DEL LEGAJO (coordinador)
   ───────────────────────────────────────────────────────────────
   Stub: existe para que la ruta /coordinador/legajos/:id ya
   funcione. En D5 muestra los datos, los PDFs, el historial y
   los botones para cambiar el estado.
   ═══════════════════════════════════════════════════════════════ */

import { IconId } from '@tabler/icons-react'
import Topbar from '../../shared/layout/Topbar'
import Card from '../../shared/components/Card'

export default function DetalleLegajo() {
  return (
    <>
      <Topbar title="Legajo" icon={IconId} />
      <div className="p-5">
        <Card>
          <p className="text-[13px] text-muted">En construcción.</p>
        </Card>
      </div>
    </>
  )
}
