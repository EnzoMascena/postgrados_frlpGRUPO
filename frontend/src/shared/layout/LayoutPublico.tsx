/* ═══════════════════════════════════════════════════════════════
   LayoutPublico.tsx — MARCO DE LAS PANTALLAS DEL ASPIRANTE
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Las pantallas públicas (inscripción y seguimiento) no tienen
   menú lateral: el aspirante no tiene usuario y no tiene que ver
   las opciones del coordinador. Este layout solo pone el fondo
   y el <Outlet />, que es donde React Router dibuja la pantalla
   que corresponde a la URL.
   ═══════════════════════════════════════════════════════════════ */

import { Outlet } from 'react-router'

export default function LayoutPublico() {
  return (
    <main className="min-h-screen bg-page">
      <Outlet />
    </main>
  )
}
