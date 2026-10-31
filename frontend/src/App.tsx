/* ═══════════════════════════════════════════════════════════════
   App.tsx — COMPONENTE RAÍZ / MAPA DE RUTAS
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   App ya no guarda en un useState qué pantalla se ve: ahora lo
   decide la URL. Cada <Route> dice "si la dirección es esta,
   mostrá este componente". Ventajas frente a la entrega 2:
     · Se puede recargar la página o compartir un link
       (/coordinador/estadisticas) y abre en la misma pantalla.
     · El botón "atrás" del navegador funciona.
     · El detalle de un legajo tiene su propia dirección
       (/coordinador/legajos/:id), con el id adentro de la URL.

   RUTAS ANIDADAS Y LAYOUTS:
   Las rutas que van dentro de otra comparten su "marco":
     · LayoutPublico → inscripción y seguimiento (sin menú).
     · LayoutCoordinador → todo lo de /coordinador (con Sidebar).
   El layout dibuja lo común y, en su <Outlet />, la pantalla hija.

   ESTRUCTURA DEL PROYECTO (mencionar al pasar):
   src/ está dividido por MÓDULO, no por tipo de archivo:
     auth/ · inscripcion/ · seguimiento/ · dashboard/ · legajo/ ·
     estadisticas/ · planilla-docente/
   y cada módulo tiene sus pages/, components/, data/ y types.
   Aparte está shared/, con lo que se reutiliza en toda la app.

   FRASE PARA DECIR: "App es el mapa del sitio: cada dirección
   tiene su pantalla, y los layouts ponen lo que se repite."
   ═══════════════════════════════════════════════════════════════ */

import { Navigate, Route, Routes } from 'react-router'
import LayoutPublico from './shared/layout/LayoutPublico'
import LayoutCoordinador from './shared/layout/LayoutCoordinador'
import NoEncontrado from './shared/pages/NoEncontrado'
import Login from './auth/pages/Login'
import FormularioInscripcion from './inscripcion/pages/FormularioInscripcion'
import Seguimiento from './seguimiento/pages/Seguimiento'
import Dashboard from './dashboard/pages/Dashboard'
import DetalleLegajo from './dashboard/pages/DetalleLegajo'
import Legajo from './legajo/pages/Legajo'
import Estadisticas from './estadisticas/pages/Estadisticas'
import PlanillaDocente from './planilla-docente/pages/PlanillaDocente'

export default function App() {
  return (
    <Routes>
      {/* `replace` reemplaza "/" en el historial en vez de sumar
          una entrada: así "atrás" desde el login no vuelve a "/"
          para que lo redirija otra vez. */}
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Login />} />

      {/* Públicas: las usa el aspirante, sin usuario. */}
      <Route element={<LayoutPublico />}>
        <Route path="/inscripcion" element={<FormularioInscripcion />} />
        <Route path="/seguimiento/:token" element={<Seguimiento />} />
      </Route>

      {/* Coordinador. `index` es la ruta "/coordinador" a secas.
          En D3 este bloque queda adentro de RutaProtegida. */}
      <Route path="/coordinador" element={<LayoutCoordinador />}>
        <Route index element={<Dashboard />} />
        <Route path="legajos/:id" element={<DetalleLegajo />} />
        <Route path="legajo-academico" element={<Legajo />} />
        <Route path="estadisticas" element={<Estadisticas />} />
        <Route path="planilla" element={<PlanillaDocente />} />
      </Route>

      {/* Cualquier otra dirección. */}
      <Route path="*" element={<NoEncontrado />} />
    </Routes>
  )
}
