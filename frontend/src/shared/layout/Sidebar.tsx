/* ═══════════════════════════════════════════════════════════════
   Sidebar.tsx — MENÚ LATERAL (navegación de toda la app)
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Es el menú fijo de la izquierda. Lo importante NO es que sea un
   menú, sino cómo está organizado: las opciones están agrupadas
   POR PERFIL DE USUARIO, que son los tres actores del sistema:

     · ASPIRANTE  → Inscripción
     · CONDUCCIÓN → Dashboard, Legajo, Estadísticas
     · DOCENTES   → Planilla

   Esa agrupación es la que definimos en el análisis de requisitos:
   cada perfil ve las funciones que le corresponden. En la versión
   final, según con qué usuario inicie sesión, se le van a mostrar
   solo sus grupos.

   TÉCNICAMENTE: el menú no está escrito a mano en el HTML. Está
   definido como una lista de datos (la constante `groups` de acá
   abajo) y se dibuja recorriéndola con .map(). Agregar una
   pantalla nueva = agregar un renglón a esa lista.

   Marca en negrita la opción activa comparando `active` con el id
   de cada ítem, y al hacer click avisa a App con onNavigate.
   ═══════════════════════════════════════════════════════════════ */

import type { Screen } from '../../App'
import {
  IconClipboardList,
  IconLayoutDashboard,
  IconUserCircle,
  IconChartBar,
  IconTable,
  IconLogout,
} from '@tabler/icons-react'
import type { ElementType } from 'react'

type NavItem = { id: Screen; label: string; icon: ElementType }
type NavGroup = { label: string; items: NavItem[] }

// El menú COMO DATO: los tres perfiles y sus pantallas.
// Cambiar el menú es cambiar esta lista, no tocar el diseño.
const groups: NavGroup[] = [
  {
    label: 'Aspirante',
    items: [{ id: 'inscripcion', label: 'Inscripción', icon: IconClipboardList }],
  },
  {
    label: 'Conducción',
    items: [
      { id: 'dashboard', label: 'Dashboard', icon: IconLayoutDashboard },
      { id: 'legajo', label: 'Legajo', icon: IconUserCircle },
      { id: 'estadisticas', label: 'Estadísticas', icon: IconChartBar },
    ],
  },
  {
    label: 'Docentes',
    items: [{ id: 'planilla', label: 'Planilla', icon: IconTable }],
  },
]

type Props = {
  active: Screen
  onNavigate: (screen: Screen) => void
  onLogout: () => void
}

export default function Sidebar({ active, onNavigate, onLogout }: Props) {
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
            const isActive = active === item.id
            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={
                  'w-full flex items-center gap-2 px-2 py-[7px] rounded-input text-[12.5px] transition-colors ' +
                  (isActive
                    ? 'bg-sidebar-active text-on-dark font-medium'
                    : 'text-faint hover:bg-sidebar-active hover:text-on-dark')
                }
              >
                <Icon size={15} stroke={1.5} className="flex-shrink-0" />
                {item.label}
              </button>
            )
          })}
        </div>
      ))}

      {/* Pie del menú: cerrar sesión y el indicador con el punto
          verde que avisa si la inscripción está abierta. */}
      <div className="mt-auto px-2 pt-2 border-t border-white/10">
        <button
          onClick={onLogout}
          className="w-full flex items-center gap-2 px-2 py-[7px] rounded-input text-[12.5px] text-faint hover:bg-sidebar-active hover:text-on-dark transition-colors"
        >
          <IconLogout size={15} stroke={1.5} className="flex-shrink-0" />
          Cerrar sesión
        </button>
        <div className="flex items-center gap-1.5 text-[11px] text-faint px-2 pt-2 mt-1 border-t border-white/10">
          <span className="w-2 h-2 rounded-full bg-[#22c55e] flex-shrink-0" />
          Período abierto
        </div>
      </div>
    </aside>
  )
}