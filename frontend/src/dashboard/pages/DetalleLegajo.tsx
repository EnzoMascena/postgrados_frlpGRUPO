/* ═══════════════════════════════════════════════════════════════
   DetalleLegajo.tsx — DETALLE DEL LEGAJO (coordinador)
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Se llega desde "Ver legajo" en el dashboard. El id sale de la URL
   (/coordinador/legajos/:id, con useParams) y todo lo demás de
   GET /legajos/{id}: datos, documentos, historial y qué acciones
   puede hacer el coordinador en el estado actual.

   QUÉ SE VE EN PANTALLA:
     · Arriba: apellido y nombre, el estado y el número de legajo
       (o el código de seguimiento si todavía no lo aprobaron).
     · A la izquierda: datos personales, carreras y documentación.
     · A la derecha: las acciones y el historial.

   Cuando una acción sale bien, el back devuelve el legajo ya
   cambiado: el estado, los botones y el historial se actualizan
   sin recargar la página.
   ═══════════════════════════════════════════════════════════════ */

import { Link, useParams } from 'react-router'
import { IconArrowLeft, IconId } from '@tabler/icons-react'
import Topbar from '../../shared/layout/Topbar'
import Alerta from '../../shared/components/Alerta'
import Cargando from '../../shared/components/Cargando'
import EstadoBadge from '../../shared/components/EstadoBadge'
import DatosLegajo from '../components/DatosLegajo'
import DocumentosLegajo from '../components/DocumentosLegajo'
import AccionesLegajo from '../components/AccionesLegajo'
import HistorialLegajo from '../components/HistorialLegajo'
import { useLegajo } from '../hooks/useDashboard'

function Volver() {
  return (
    <Link
      to="/coordinador"
      className="inline-flex items-center gap-1 text-[12px] text-muted hover:text-ink transition-colors"
    >
      <IconArrowLeft size={14} stroke={1.5} /> Volver al dashboard
    </Link>
  )
}

export default function DetalleLegajo() {
  const { id = '' } = useParams()
  const { data: legajo, error, isPending } = useLegajo(id)

  const titulo = legajo ? `Legajo · ${legajo.apellido}, ${legajo.nombre}` : 'Legajo'

  return (
    <>
      <Topbar title={titulo} icon={IconId}>
        {legajo && (
          <>
            <EstadoBadge estado={legajo.estado} />
            <span
              className={'text-[12px] ' + (legajo.numeroLegajo ? 'text-ink' : 'text-muted font-mono')}
              title={legajo.numeroLegajo ? 'Número de legajo' : 'Código de seguimiento'}
            >
              {legajo.numeroLegajo ?? legajo.codigoSeguimiento}
            </span>
          </>
        )}
      </Topbar>

      <div className="p-5">
        <div className="mb-4">
          <Volver />
        </div>

        {isPending && <Cargando texto="Cargando el legajo…" />}
        {error && <Alerta variant="danger">No se pudo cargar el legajo. {error.message}</Alerta>}

        {legajo && (
          <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] gap-x-4 items-start">
            <div>
              <DatosLegajo legajo={legajo} />
              <DocumentosLegajo documentos={legajo.documentos} />
            </div>
            <div>
              <AccionesLegajo legajo={legajo} />
              <HistorialLegajo historial={legajo.historial ?? []} />
            </div>
          </div>
        )}
      </div>
    </>
  )
}
