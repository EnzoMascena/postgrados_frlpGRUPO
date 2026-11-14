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
     · el legajo    → código y estado arriba, el aviso de qué hacer,
                      la documentación (PDFs) y el resumen de los datos

   Comparado con la entrega 2: antes no existía esta pantalla y el
   estado del legajo no se veía en ningún lado. Ahora todo sale del
   back y TanStack Query lo guarda en la caché ['seguimiento', token].
   ═══════════════════════════════════════════════════════════════ */

import { useState } from 'react'
import { Link, useParams } from 'react-router'
import { IconLinkOff, IconListSearch, IconMailForward } from '@tabler/icons-react'
import Topbar from '../../shared/layout/Topbar'
import Alerta from '../../shared/components/Alerta'
import Card from '../../shared/components/Card'
import Cargando from '../../shared/components/Cargando'
import EstadoBadge from '../../shared/components/EstadoBadge'
import AvisoEstado from '../components/AvisoEstado'
import Documentacion from '../components/Documentacion'
import EnviarRevision from '../components/EnviarRevision'
import DatosDelLegajo from '../components/DatosDelLegajo'
import { esDocumentosFaltantes, esLinkInvalido } from '../api'
import { sePuedeEnviar } from '../envio'
import { aCuerpo } from '../../inscripcion/api'
import type { DatosInscripcion } from '../../inscripcion/types'
import { useActualizarDatos, useEnviar, useSeguimiento } from '../hooks/useSeguimiento'

// Los textos de la Alerta de éxito. La corrección se reconoce aparte, como en el
// email confirmacion_envio (es_correccion).
const EXITO = {
  envio: 'Recibimos tu preinscripción. Te mandamos un email con tu código de seguimiento.',
  correccion: 'Recibimos tu corrección. Te mandamos un email con tu código de seguimiento.',
  datos: 'Guardamos tus cambios.',
} as const

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
  const envio = useEnviar(token)
  const edicion = useActualizarDatos(token)
  const [editando, setEditando] = useState(false)
  // Se guarda aparte del legajo: después de enviar, el estado ya es PENDIENTE
  // y no se sabe si lo que se mandó era un envío o una corrección.
  const [exito, setExito] = useState<keyof typeof EXITO | null>(null)

  // Los botones estaban abajo y la Alerta de éxito queda arriba: la llevamos a la vista.
  function mostrarExito(cual: keyof typeof EXITO) {
    setExito(cual)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function enviar(esCorreccion: boolean) {
    setExito(null)
    envio.mutate(undefined, {
      onSuccess: () => mostrarExito(esCorreccion ? 'correccion' : 'envio'),
    })
  }

  function editar() {
    setExito(null)
    edicion.reset()
    setEditando(true)
  }

  function cancelarEdicion() {
    edicion.reset()
    setEditando(false)
  }

  function guardar(datos: DatosInscripcion) {
    setExito(null)
    edicion.mutate(aCuerpo(datos), {
      onSuccess: () => {
        setEditando(false)
        mostrarExito('datos')
      },
    })
  }

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

    const datos = seguimiento.data
    return (
      <>
        {exito && (
          <Alerta variant="success" className="mb-3.5">
            {EXITO[exito]}
          </Alerta>
        )}
        <AvisoEstado legajo={datos} />
        <Documentacion
          token={token}
          legajo={datos}
          // Solo después de que el back frenó el envío: antes, los pendientes no van en rojo.
          faltantes={esDocumentosFaltantes(envio.error) ? datos.documentosFaltantes : []}
        />
        {/* Mientras edita no se envía: primero guarda o cancela. */}
        {sePuedeEnviar(datos) && !editando && (
          <EnviarRevision
            legajo={datos}
            onConfirmar={() => enviar(datos.estado === 'OBSERVADO')}
            enviando={envio.isPending}
            error={envio.error?.message ?? null}
          />
        )}
        <DatosDelLegajo
          legajo={datos}
          // Si el legajo dejó de ser editable (lo envió desde otra pestaña), se cierra solo.
          editando={editando && datos.puedeEditar === true}
          onEditar={editar}
          onCancelar={cancelarEdicion}
          onGuardar={guardar}
          guardando={edicion.isPending}
          error={edicion.error}
        />
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
