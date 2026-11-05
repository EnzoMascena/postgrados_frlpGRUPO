/* ═══════════════════════════════════════════════════════════════
   Seguimiento.tsx — MI PREINSCRIPCIÓN (/seguimiento/:token)
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Es la segunda pantalla del aspirante. Llega acá de dos formas:
     · recién guardó el formulario (POST /legajos le dio el token)
     · abrió el link del email (link_seguimiento u observación)
   No tiene usuario ni contraseña: el token de la URL es la llave.
   Vence a los 60 días y cada email trae uno nuevo, así que si
   alguien lo encuentra viejo en un mail reenviado, ya no sirve.

   QUÉ HACE: lee el token con useParams y pide el legajo con
   useSeguimiento(token) (GET /seguimiento/{token}). Según la
   respuesta:
     · cargando     → <Cargando>
     · 404          → el link no vale: card con el mensaje del back
                      y un botón para pedir uno nuevo
     · otro error   → <Alerta> con el mensaje (sin conexión, 500)
     · el legajo    → código y estado arriba, el aviso de qué hacer
                      y el resumen de los datos

   Comparado con la entrega 2: antes no existía esta pantalla y el
   estado del legajo no se veía en ningún lado. Ahora todo sale del
   back y TanStack Query lo guarda en la caché ['seguimiento', token].
   ═══════════════════════════════════════════════════════════════ */

import { Link, useParams } from 'react-router'
import { IconLinkOff, IconListSearch, IconMailForward } from '@tabler/icons-react'
import Topbar from '../../shared/layout/Topbar'
import Alerta from '../../shared/components/Alerta'
import Card from '../../shared/components/Card'
import Cargando from '../../shared/components/Cargando'
import EstadoBadge from '../../shared/components/EstadoBadge'
import AvisoEstado from '../components/AvisoEstado'
import ResumenDatos from '../components/ResumenDatos'
import { esLinkInvalido } from '../api'
import { useSeguimiento } from '../hooks/useSeguimiento'

function CodigoSeguimiento({ codigo, className }: { codigo: string; className: string }) {
  return (
    <span className={'text-[12px] text-muted ' + className}>
      Código de seguimiento{' '}
      <span className="font-mono font-medium text-ink">{codigo}</span>
    </span>
  )
}

export default function Seguimiento() {
  // La ruta es /seguimiento/:token, así que siempre viene.
  const { token = '' } = useParams()
  const seguimiento = useSeguimiento(token)
  const legajo = seguimiento.data

  function contenido() {
    if (seguimiento.isPending) return <Cargando texto="Cargando tu preinscripción…" />

    if (esLinkInvalido(seguimiento.error)) {
      return (
        <Card title="Este link no es válido" icon={IconLinkOff} className="max-w-xl">
          <p className="text-[13px] text-ink">{seguimiento.error?.message}</p>
          <p className="text-[12px] text-muted mt-1.5">
            Los links vencen a los 60 días y cada email trae uno nuevo. Pedí otro con el email con
            el que te inscribiste.
          </p>
          {/* Es navegación, no una acción: va como link con el aspecto del Button primary. */}
          <Link
            to="/inscripcion?recuperar=1"
            className="mt-3.5 inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-input border border-primary bg-primary text-white text-[12px] font-medium hover:bg-primary-hover hover:border-primary-hover transition-colors"
          >
            <IconMailForward size={15} stroke={1.5} />
            Pedir un link nuevo
          </Link>
        </Card>
      )
    }

    if (seguimiento.isError) {
      return (
        <Alerta variant="danger">
          <p>{seguimiento.error.message}</p>
          <p className="mt-1">Recargá la página en unos minutos.</p>
        </Alerta>
      )
    }

    return (
      <>
        <AvisoEstado legajo={seguimiento.data} />
        <ResumenDatos legajo={seguimiento.data} />
      </>
    )
  }

  return (
    <>
      <Topbar title="Mi preinscripción" icon={IconListSearch}>
        {legajo && (
          <>
            {/* En 375 px no entra junto al título: ahí va abajo, en la página. */}
            <CodigoSeguimiento codigo={legajo.codigoSeguimiento} className="hidden sm:inline" />
            <EstadoBadge estado={legajo.estado} />
          </>
        )}
      </Topbar>

      <div className="p-5">
        {legajo && (
          <CodigoSeguimiento
            codigo={legajo.codigoSeguimiento}
            className="block sm:hidden -mt-1 mb-3"
          />
        )}
        {contenido()}
      </div>
    </>
  )
}
