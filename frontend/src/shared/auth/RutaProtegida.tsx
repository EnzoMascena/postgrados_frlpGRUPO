/* ═══════════════════════════════════════════════════════════════
   RutaProtegida.tsx — EL "PATOVICA" DE LAS RUTAS DEL COORDINADOR
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Se pone en App alrededor de las rutas que piden login:
     <Route element={<RutaProtegida rol="COORDINADOR" />}> … </Route>
   y decide antes de dibujar la pantalla:
     · Sin sesión → al login, recordando a dónde quería ir, así
       después de entrar lo llevamos ahí.
     · Con otro rol → NoEncontrado (no le contamos que existe).
     · Con el rol correcto → <Outlet />, o sea, la pantalla hija.

   OJO: esto es comodidad para el usuario, no seguridad. La
   seguridad real está en el back, que valida el token y el rol
   en cada pedido (401 / 403).
   ═══════════════════════════════════════════════════════════════ */

import { Navigate, Outlet, useLocation } from 'react-router'
import type { Rol } from '../api/tipos'
import NoEncontrado from '../pages/NoEncontrado'
import { useAuth } from './useAuth'

export default function RutaProtegida({ rol }: { rol: Rol }) {
  const { usuario } = useAuth()
  const location = useLocation()

  if (!usuario) {
    return <Navigate to="/login" replace state={{ desde: location.pathname + location.search }} />
  }
  if (usuario.rol !== rol) return <NoEncontrado />
  return <Outlet />
}
