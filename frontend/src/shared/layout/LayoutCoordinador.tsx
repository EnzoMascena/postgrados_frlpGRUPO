import { useState } from 'react'
import { Outlet } from 'react-router'
import { IconMenu2 } from '@tabler/icons-react'
import Sidebar from './Sidebar'

export default function LayoutCoordinador() {
  // En pantallas chicas el menú no entra al lado del contenido: se
  // esconde y se abre con el botón "Menú", por encima de la pantalla.
  const [menuAbierto, setMenuAbierto] = useState(false)

  return (
    <div className="flex h-screen overflow-hidden">
      <div
        className={
          'fixed inset-y-0 left-0 z-40 md:static md:z-auto md:flex ' +
          (menuAbierto ? 'flex' : 'hidden')
        }
      >
        <Sidebar onNavegar={() => setMenuAbierto(false)} />
      </div>
      {menuAbierto && (
        <div
          aria-hidden="true"
          onClick={() => setMenuAbierto(false)}
          className="fixed inset-0 z-30 bg-sidebar/60 md:hidden"
        />
      )}

      <main className="flex-1 overflow-auto min-w-0">
        <div className="md:hidden flex items-center gap-2 h-11 px-4 bg-sidebar text-on-dark">
          <button
            type="button"
            onClick={() => setMenuAbierto(true)}
            aria-label="Abrir el menú"
            aria-expanded={menuAbierto}
            className="p-1 -ml-1 rounded-input hover:bg-sidebar-active transition-colors"
          >
            <IconMenu2 size={18} stroke={1.5} />
          </button>
          <span className="text-[13px] font-medium">Sistema Posgrado</span>
        </div>
        <Outlet />
      </main>
    </div>
  )
}
