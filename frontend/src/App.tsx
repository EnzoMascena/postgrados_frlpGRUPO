/* ═══════════════════════════════════════════════════════════════
   App.tsx — COMPONENTE RAÍZ / "CENTRO DE MANDO"
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   App decide DOS cosas y nada más:
     1) ¿El usuario inició sesión?  → si no, muestra el Login.
     2) ¿Qué pantalla está eligiendo? → renderiza esa pantalla.

   NAVEGACIÓN SIN LIBRERÍA DE RUTAS:
   No usamos React Router. Guardamos en una variable de estado
   cuál es la pantalla activa y mostramos el componente que
   corresponde. Es más simple y alcanza para el prototipo.

   CONCEPTO CLAVE — useState:
   Es un "hook" de React. Guarda un valor que puede cambiar
   (estado) y, cada vez que ese valor cambia, React vuelve a
   dibujar la pantalla automáticamente. Devuelve un par:
   [valorActual, funciónParaCambiarlo].

   ESTRUCTURA DEL PROYECTO (mencionar al pasar):
   src/ está dividido por MÓDULO, no por tipo de archivo:
     auth/ · inscripcion/ · dashboard/ · legajo/ ·
     estadisticas/ · planilla-docente/
   y cada módulo tiene sus pages/, components/, data/ y types.
   Aparte está shared/, con lo que se reutiliza en toda la app
   (Button, Card, Badge, Sidebar, Topbar...).

   FRASE PARA DECIR: "App es el esqueleto: muestra el login o, si
   ya entraste, el menú lateral más la pantalla seleccionada."
   ═══════════════════════════════════════════════════════════════ */

import { useState } from 'react'
import Sidebar from './shared/layout/Sidebar'
import FormularioInscripcion from './inscripcion/pages/FormularioInscripcion'
import Login from './auth/pages/Login'
import PlanillaDocente from './planilla-docente/pages/PlanillaDocente'
import Estadisticas from './estadisticas/pages/Estadisticas'
import Dashboard from './dashboard/pages/Dashboard'
import Legajo from './legajo/pages/Legajo'


// Las 5 pantallas posibles. Al ser un tipo de TypeScript, si
// escribimos mal un nombre el editor lo marca en rojo ANTES de
// ejecutar: ese es el beneficio de usar TS en vez de JS.
export type Screen =
  | 'inscripcion'
  | 'dashboard'
  | 'legajo'
  | 'estadisticas'
  | 'planilla'

export default function App() {
  // ¿Inició sesión? Arranca en false, así primero se ve el login.
  const [loggedIn, setLoggedIn] = useState(false)
  // Pantalla actualmente visible. Arranca en el formulario de
  // inscripción, que es el primer paso del circuito real.
  const [screen, setScreen] = useState<Screen>('inscripcion')

  // Si todavía no entró, mostramos SOLO el login (sin sidebar).
  if (!loggedIn) {
    return <Login onLogin={() => setLoggedIn(true)} />
  }

  // Ya adentro: el layout normal con el menú lateral.
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Menú lateral. Le pasamos:
          - active: para que resalte la opción actual
          - onNavigate: función que el Sidebar llama al hacer click.
            Así el hijo (Sidebar) le avisa al padre (App) que cambie
            de pantalla. Ese patrón se llama "levantar el estado". */}
      <Sidebar active={screen} onNavigate={setScreen} onLogout={() => setLoggedIn(false)}/>

      {/* Área de contenido. Se muestra UNA sola pantalla a la vez:
          `condición && <Componente />` significa "si la condición es
          verdadera, mostrá esto". Es el 'if' dentro del JSX. */}
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