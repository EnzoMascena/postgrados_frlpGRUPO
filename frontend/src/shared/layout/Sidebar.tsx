/* ═══════════════════════════════════════════════════════════════
   Sidebar.tsx — MENÚ LATERAL (navegación de toda la app)
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Es el menú fijo de la izquierda. Lo importante NO es que sea un
   menú, sino cómo está organizado: las opciones están agrupadas
   POR PERFIL DE USUARIO, que son los tres actores del sistema:

     · ASPIRANTE  → Inscripción
     · CONDUCCIÓN → Dashboard, Legajo académico, Estadísticas
     · DOCENTES   → Planilla

   Esa agrupación es la que definimos en el análisis de requisitos:
   cada perfil ve las funciones que le corresponden. Las pantallas
   que todavía usan datos de prueba (módulos B, C y D) dicen
   "(demo)" para que nadie las confunda con datos reales.

   TÉCNICAMENTE: el menú no está escrito a mano en el HTML. Está
   definido como una lista de datos (la constante `groups` de acá
   abajo) y se dibuja recorriéndola con .map(). Agregar una
   pantalla nueva = agregar un renglón a esa lista.

   CONCEPTO CLAVE — <NavLink>:
   Es un link de React Router que sabe si su dirección es la URL
   actual (`isActive`) y con eso se pinta resaltado. Antes App le
   pasaba al Sidebar la pantalla activa por props; ahora la URL es
   la única fuente de verdad y el Sidebar no recibe nada.
   ═══════════════════════════════════════════════════════════════ */

import { NavLink, useNavigate } from 'react-router'
import {
  IconClipboardList,
  IconLayoutDashboard,
  IconUserCircle,
  IconChartBar,
  IconTable,
  IconLogout,
} from '@tabler/icons-react'
import type { ElementType } from 'react'

type NavItem = { to: string; label: string; icon: ElementType; demo?: boolean }
type NavGroup = { label: string; items: NavItem[] }

// El menú COMO DATO: los tres perfiles y sus pantallas.
// Cambiar el menú es cambiar esta lista, no tocar el diseño.
const groups: NavGroup[] = [
  {
    label: 'Aspirante',
    items: [{ to: '/inscripcion', label: 'Inscripción', icon: IconClipboardList }],
  },
  {
    label: 'Conducción',
    items: [
      { to: '/coordinador', label: 'Dashboard', icon: IconLayoutDashboard },
      { to: '/coordinador/legajo-academico', label: 'Legajo académico', icon: IconUserCircle, demo: true },
      { to: '/coordinador/estadisticas', label: 'Estadísticas', icon: IconChartBar, demo: true },
    ],
  },
  {
    label: 'Docentes',
    items: [{ to: '/coordinador/planilla', label: 'Planilla', icon: IconTable, demo: true }],
  },
]

export default function Sidebar() {
  const navigate = useNavigate()

  return (
    <aside className="w-60 flex-shrink-0 bg-sidebar flex flex-col py-3 overflow-y-auto">
      {/* Logo */}
      <div className="px-4 pb-4 mb-2 border-b border-white/10">
        <div className="text-[11px] uppercase tracking-wide text-faint">UTN · FRLP</div>
        <div className="text-[13px] font-medium text-on-dark">Sistema Posgrado</div>
      </div>

      {/* Grupos de navegación */}
      {groups.map((group) => (
        <div key={group.label} className="px-2 mb-0.5">
          <div className="text-[11px] uppercase tracking-wide text-faint px-2 py-1">
            {group.label}
          </div>

          {group.items.map((item) => {
            const Icon = item.icon
            return (
              // `end`: solo está activo si la URL es exactamente esa.
              // Sin él, "Dashboard" (/coordinador) quedaría resaltado
              // también en /coordinador/estadisticas.
              <NavLink
                key={item.to}
                to={item.to}
                end
                className={({ isActive }) =>
                  'w-full flex items-center gap-2 px-2 py-[7px] rounded-input text-[12.5px] transition-colors ' +
                  (isActive
                    ? 'bg-sidebar-active text-on-dark font-medium'
                    : 'text-faint hover:bg-sidebar-active hover:text-on-dark')
                }
              >
                <Icon size={15} stroke={1.5} className="flex-shrink-0" />
                {item.label}
                {item.demo && ' (demo)'}
              </NavLink>
            )
          })}
        </div>
      ))}

      {/* Pie del menú: cerrar sesión. Por ahora solo vuelve al
          login; en D3 también borra la sesión guardada. */}
      <div className="mt-auto px-2 pt-2 border-t border-white/10">
        <button
          onClick={() => navigate('/login')}
          className="w-full flex items-center gap-2 px-2 py-[7px] rounded-input text-[12.5px] text-faint hover:bg-sidebar-active hover:text-on-dark transition-colors"
        >
          <IconLogout size={15} stroke={1.5} className="flex-shrink-0" />
          Cerrar sesión
        </button>
      </div>
    </aside>
  )
}
