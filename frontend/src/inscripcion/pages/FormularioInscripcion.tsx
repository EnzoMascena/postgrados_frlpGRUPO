/* ═══════════════════════════════════════════════════════════════
   FormularioInscripcion.tsx — PANTALLA DEL ASPIRANTE (/inscripcion)
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Es la preinscripción a una carrera de posgrado. Reemplaza al
   formulario en papel/PDF que hoy se completa a mano.

   EL RECORRIDO TIENE DOS PANTALLAS:
     1. Acá (/inscripcion): datos personales, carreras y beca. Al
        guardar se crea el legajo en Borrador.
     2. /seguimiento/:token: estado, documentación (PDF) y enviar a
        revisión. La documentación se pasó para allá porque para
        subir un PDF el legajo tiene que existir.

   EL PERÍODO (US-CORE-009): la pantalla pide las cohortes a la API
   con useCohortes() (TanStack Query) y decide qué mostrar:
     · cargando              → <Cargando>
     · falló el pedido       → <Alerta> con el error
     · ninguna abierta       → "La inscripción está cerrada…"
     · una abierta           → el formulario, para esa cohorte
     · varias abiertas       → un select para elegir la cohorte
   El Badge del Topbar ya no es fijo: sale de los mismos datos.

   Los campos viven en <FormularioDatos>, un componente aparte
   porque se reusa para editar los datos desde el seguimiento.

   PENDIENTE: el guardado en la API (POST /legajos) se conecta en el
   checkpoint 2.4. Por ahora, al apretar el botón solo se valida y se
   avisa que está todo bien.
   ═══════════════════════════════════════════════════════════════ */

import { useState } from 'react'
import { IconCalendarEvent, IconCalendarOff, IconClipboardList } from '@tabler/icons-react'
import Topbar from '../../shared/layout/Topbar'
import Badge from '../../shared/components/Badge'
import Alerta from '../../shared/components/Alerta'
import Card from '../../shared/components/Card'
import Cargando from '../../shared/components/Cargando'
import Field from '../../shared/components/Field'
import { controlClass } from '../../shared/components/controls'
import { useCarreras, useCohortes } from '../../shared/hooks/useCatalogos'
import FormularioDatos from '../components/FormularioDatos'
import { cohortesAbiertas, mensajeCerrada, proximaApertura } from '../periodo'

export default function FormularioInscripcion() {
  const cohortes = useCohortes()
  // También se piden acá para no mostrar el formulario a medias.
  // TanStack Query las comparte con FormularioDatos: se piden una vez.
  const carreras = useCarreras()

  // La cohorte elegida en el select ('' = todavía no tocó el select).
  const [cohorteElegida, setCohorteElegida] = useState('')
  // Temporal hasta el 2.4: avisa que los datos pasaron la validación.
  const [valido, setValido] = useState(false)

  const abiertas = cohortes.data ? cohortesAbiertas(cohortes.data) : []
  // Si no eligió nada (o la que eligió se cerró), va la más nueva abierta.
  const cohorte = abiertas.find((c) => c.id === cohorteElegida) ?? abiertas[0]

  function contenido() {
    if (cohortes.isPending || carreras.isPending) return <Cargando />

    if (cohortes.isError || carreras.isError) {
      return (
        <Alerta variant="danger">
          No pudimos cargar el formulario de inscripción. Revisá tu conexión y recargá la página.
        </Alerta>
      )
    }

    if (!cohorte) {
      return (
        <Card title="Inscripción cerrada" icon={IconCalendarOff}>
          <p className="text-[13px] text-ink">
            {mensajeCerrada(proximaApertura(cohortes.data))}
          </p>
        </Card>
      )
    }

    return (
      <>
        {valido && (
          <Alerta variant="success" className="mb-4">
            Los datos para la {cohorte.nombre} están completos. Todavía no se guardan: eso se
            conecta con la API en el próximo paso.
          </Alerta>
        )}

        {/* Con más de una cohorte abierta, el aspirante elige. */}
        {abiertas.length > 1 && (
          <Card title="Cohorte" icon={IconCalendarEvent}>
            <Field label="Cohorte a la que te inscribís" required htmlFor="cohorte" className="max-w-md">
              <select
                id="cohorte"
                className={controlClass}
                value={cohorte.id}
                onChange={(e) => setCohorteElegida(e.target.value)}
              >
                {abiertas.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nombre}
                  </option>
                ))}
              </select>
            </Field>
          </Card>
        )}

        <FormularioDatos
          textoBoton="Guardar y continuar con la documentación"
          onEnviar={() => {
            setValido(true)
            window.scrollTo({ top: 0, behavior: 'smooth' })
          }}
        />
      </>
    )
  }

  return (
    <>
      <Topbar title="Formulario de preinscripción" icon={IconClipboardList}>
        {cohortes.data &&
          (cohorte ? (
            <Badge variant="info">Período abierto</Badge>
          ) : (
            <Badge variant="warn">Período cerrado</Badge>
          ))}
      </Topbar>

      <div className="p-5">{contenido()}</div>
    </>
  )
}
