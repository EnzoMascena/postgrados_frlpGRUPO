import { useState } from 'react'
import Sidebar from './shared/layout/Sidebar'
import FormularioInscripcion from './inscripcion/pages/FormularioInscripcion'
import Login from './auth/pages/Login'
import PlanillaDocente from './planilla-docente/pages/PlanillaDocente'
import Estadisticas from './estadisticas/pages/Estadisticas'
import Dashboard from './dashboard/pages/Dashboard'
import Legajo from './legajo/pages/Legajo'


export type Screen =
  | 'inscripcion'
  | 'dashboard'
  | 'legajo'
  | 'estadisticas'
  | 'planilla'

export default function App() {
  // ¿Inició sesión? Arranca en false, así primero se ve el login.
  const [loggedIn, setLoggedIn] = useState(false)
  const [screen, setScreen] = useState<Screen>('inscripcion')

  // Si todavía no entró, mostramos SOLO el login (sin sidebar).
  if (!loggedIn) {
    return <Login onLogin={() => setLoggedIn(true)} />
  }

  // Ya adentro: el layout normal con el menú lateral.
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar active={screen} onNavigate={setScreen} onLogout={() => setLoggedIn(false)}/>

      <main className="flex-1 overflow-auto min-w-0">
        {screen === 'inscripcion' && <FormularioInscripcion />}
        {screen === 'dashboard' && <Dashboard/>}
        {screen === 'legajo' && <Legajo />}
        {screen === 'estadisticas' && <Estadisticas />}
        {screen === 'planilla' && <PlanillaDocente />}
      </main>
    </div>
  )
}