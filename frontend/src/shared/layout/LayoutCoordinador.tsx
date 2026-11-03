/* ═══════════════════════════════════════════════════════════════
   LayoutCoordinador.tsx — MARCO DE LAS PANTALLAS DEL COORDINADOR
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Es el "molde" que comparten todas las rutas /coordinador/...:
   el menú lateral fijo a la izquierda y, a la derecha, el área
   donde se dibuja la pantalla elegida.

   CONCEPTO CLAVE — <Outlet />:
   Es el hueco donde React Router pone la pantalla hija que
   coincide con la URL. Si estás en /coordinador/estadisticas,
   en el Outlet aparece Estadísticas; el Sidebar no se vuelve a
   dibujar. Antes esto lo hacía App con un useState y un `&&` por
   pantalla; ahora lo decide la URL.
   ═══════════════════════════════════════════════════════════════ */

import { Outlet } from 'react-router'
import Sidebar from './Sidebar'

export default function LayoutCoordinador() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-auto min-w-0">
        <Outlet />
      </main>
    </div>
  )
}
