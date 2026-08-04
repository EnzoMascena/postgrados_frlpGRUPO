import { useState } from 'react'
import Sidebar from './shared/layout/Sidebar'
import FormularioInscripcion from './inscripcion/pages/FormularioInscripcion'
import Login from './auth/pages/Login'
import PlanillaDocente from './planilla-docente/pages/PlanillaDocente'

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
        {screen === 'dashboard' && <Placeholder title="Dashboard · Conducción" />}
        {screen === 'legajo' && <Placeholder title="Legajo del estudiante" />}
        {screen === 'estadisticas' && <Placeholder title="Estadísticas" />}
        {screen === 'planilla' && <PlanillaDocente />}
      </main>
    </div>
  )
}

function Placeholder({ title }: { title: string }) {
  return (
    <div className="p-8">
      <h1 className="text-xl font-semibold text-ink">{title}</h1>
      <p className="mt-2 text-sm text-muted">
        Pantalla en construcción — la portamos en el próximo paso.
      </p>
    </div>
  )
}