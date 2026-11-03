/* ═══════════════════════════════════════════════════════════════
   Cargando.tsx — INDICADOR MIENTRAS LLEGAN LOS DATOS
   ───────────────────────────────────────────────────────────────
   Se muestra mientras un hook de TanStack Query está en
   `isPending`. role="status" hace que el lector de pantalla
   anuncie "Cargando…" sin interrumpir.
   ═══════════════════════════════════════════════════════════════ */

import { IconLoader2 } from '@tabler/icons-react'

export default function Cargando({ texto = 'Cargando…' }: { texto?: string }) {
  return (
    <div role="status" className="flex items-center justify-center gap-2 py-6 text-[12px] text-muted">
      <IconLoader2 size={16} stroke={1.5} className="animate-spin" />
      {texto}
    </div>
  )
}
