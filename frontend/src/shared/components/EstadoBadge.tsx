/* ═══════════════════════════════════════════════════════════════
   EstadoBadge.tsx — EL ESTADO DEL LEGAJO COMO ETIQUETA DE COLOR
   ───────────────────────────────────────────────────────────────
   Recibe el estado tal como lo manda el back ("EN_REVISION") y
   muestra el Badge con su texto y su color, que salen de las
   tablas de tipos.ts. Así el dashboard, el detalle y la página
   del aspirante muestran cada estado siempre igual.
   ═══════════════════════════════════════════════════════════════ */

import Badge from './Badge'
import { ETIQUETA_ESTADO, VARIANTE_ESTADO, type EstadoLegajo } from '../api/tipos'

export default function EstadoBadge({ estado }: { estado: EstadoLegajo }) {
  return <Badge variant={VARIANTE_ESTADO[estado]}>{ETIQUETA_ESTADO[estado]}</Badge>
}
