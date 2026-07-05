import { useState } from 'react'
import Sidebar from './shared/layout/Sidebar'
import FormularioInscripcion from './inscripcion/pages/FormularioInscripcion'

export type Screen =
  | 'inscripcion'
  | 'dashboard'
  | 'legajo'
  | 'estadisticas'
  | 'planilla'

export default function App() {
  const [screen, setScreen] = useState<Screen>('inscripcion')

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar active={screen} onNavigate={setScreen} />

      <main className="flex-1 overflow-auto min-w-0">
        {screen === 'inscripcion' && <FormularioInscripcion />}
        {screen === 'dashboard' && <Placeholder title="Dashboard · Conducción" />}
        {screen === 'legajo' && <Placeholder title="Legajo del estudiante" />}
        {screen === 'estadisticas' && <Placeholder title="Estadísticas" />}
        {screen === 'planilla' && <Placeholder title="Planilla docente" />}
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