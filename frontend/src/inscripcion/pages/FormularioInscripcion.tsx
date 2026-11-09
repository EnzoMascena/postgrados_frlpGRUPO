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

   GUARDAR (US-CORE-001): "Guardar y continuar…" → POST /legajos con
   useInscribir() → si sale bien, el back devuelve el token y vamos a
   /seguimiento/{token}. Si falla, el error del back se muestra:
     · con `field` → al lado de ese campo (erroresServidor)
     · sin `field` → en una Alerta arriba (también el 429 y "sin
       conexión")
     · 409 de email repetido → además, "Mandarme el link"
     · 409 PERIODO_CERRADO → se vuelven a pedir las cohortes, y la
       pantalla pasa sola a "Inscripción cerrada"

   RECUPERAR: la card "¿Ya empezaste tu preinscripción?" está siempre,
   aunque el período esté cerrado. Con ?recuperar=1 (viene del email
   de observación) la página baja hasta ella y enfoca el email.
   ═══════════════════════════════════════════════════════════════ */

import { useMemo, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router'
import { useQueryClient } from '@tanstack/react-query'
import { IconCalendarEvent, IconCalendarOff, IconClipboardList, IconMailForward } from '@tabler/icons-react'
import Topbar from '../../shared/layout/Topbar'
import Badge from '../../shared/components/Badge'
import Alerta from '../../shared/components/Alerta'
import Button from '../../shared/components/Button'
import Card from '../../shared/components/Card'
import Cargando from '../../shared/components/Cargando'
import Field from '../../shared/components/Field'
import { controlClass } from '../../shared/components/controls'
import { useCarreras, useCohortes } from '../../shared/hooks/useCatalogos'
import FormularioDatos from '../components/FormularioDatos'
import RecuperarAcceso from '../components/RecuperarAcceso'
import { aPayload, esEmailRepetido, esPeriodoCerrado, separarError } from '../api'
import { useInscribir, useRecuperarAcceso } from '../hooks/useInscripcion'
import { cohortesAbiertas, mensajeCerrada, proximaApertura } from '../periodo'
import type { DatosInscripcion } from '../types'

export default function FormularioInscripcion() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [parametros] = useSearchParams()

  const cohortes = useCohortes()
  // También se piden acá para no mostrar el formulario a medias.
  // TanStack Query las comparte con FormularioDatos: se piden una vez.
  const carreras = useCarreras()

  const inscripcion = useInscribir()
  // El "Mandarme el link" del 409 de email repetido.
  const linkPorEmailRepetido = useRecuperarAcceso()

  // La cohorte elegida en el select ('' = todavía no tocó el select).
  const [cohorteElegida, setCohorteElegida] = useState('')
  const alertaArriba = useRef<HTMLDivElement>(null)

  const abiertas = cohortes.data ? cohortesAbiertas(cohortes.data) : []
  // Si no eligió nada (o la que eligió se cerró), va la más nueva abierta.
  const cohorte = abiertas.find((c) => c.id === cohorteElegida) ?? abiertas[0]

  // useMemo: FormularioDatos necesita el mismo objeto mientras el error
  // no cambie (si no, volvería a poner el foco en cada render).
  const error = useMemo(() => separarError(inscripcion.error), [inscripcion.error])
  const emailRepetido = esEmailRepetido(inscripcion.error)

  function guardar(datos: DatosInscripcion) {
    if (!cohorte) return
    linkPorEmailRepetido.reset()
    inscripcion.mutate(aPayload(datos, cohorte.id), {
      onSuccess: ({ token }) => navigate(`/seguimiento/${encodeURIComponent(token)}`),
      onError: (e) => {
        // Se cerró mientras completaba: con las cohortes nuevas la
        // pantalla muestra "Inscripción cerrada" con la próxima fecha.
        if (esPeriodoCerrado(e)) void queryClient.invalidateQueries({ queryKey: ['cohortes'] })
        // Un error sin campo (o el de email repetido) se lee arriba.
        if (!separarError(e).general && !esEmailRepetido(e)) return
        // Espera al render que muestra la Alerta.
        requestAnimationFrame(() =>
          alertaArriba.current?.scrollIntoView({ behavior: 'smooth', block: 'center' }),
        )
      },
    })
  }

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
        <div ref={alertaArriba}>
          {error.general && (
            <Alerta variant="danger" className="mb-4">
              {error.general}
            </Alerta>
          )}

          {/* El mensaje del 409 ya está al lado del email: acá va la salida. */}
          {emailRepetido && inscripcion.variables && (
            <Alerta variant="warn" className="mb-4">
              <p>
                Ya hay una preinscripción con <strong>{inscripcion.variables.email}</strong>. Si
                la empezaste vos, pedí el link para continuar donde la dejaste.
              </p>
              {linkPorEmailRepetido.isSuccess ? (
                <p className="mt-2">{linkPorEmailRepetido.data.mensaje}</p>
              ) : (
                <Button
                  className="mt-2 disabled:opacity-60 disabled:cursor-not-allowed"
                  disabled={linkPorEmailRepetido.isPending}
                  aria-busy={linkPorEmailRepetido.isPending}
                  onClick={() => linkPorEmailRepetido.mutate(inscripcion.variables!.email)}
                >
                  <IconMailForward size={15} stroke={1.5} />
                  {linkPorEmailRepetido.isPending ? 'Enviando…' : 'Mandarme el link'}
                </Button>
              )}
              {linkPorEmailRepetido.isError && (
                <p className="mt-2 text-danger">{linkPorEmailRepetido.error.message}</p>
              )}
            </Alerta>
          )}
        </div>

        {/* Con más de una cohorte abierta, el aspirante elige. */}
        {abiertas.length > 1 && (
          <Card title="Cohorte" icon={IconCalendarEvent}>
            <Field label="Cohorte a la que te inscribís" required htmlFor="cohorte" className="max-w-md">
              <select
                id="cohorte"
                className={controlClass}
                value={cohorte.id}
                disabled={inscripcion.isPending}
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
          onEnviar={guardar}
          // Después de un 201 se sigue en "Guardando…" hasta que cambia la página.
          enviando={inscripcion.isPending || inscripcion.isSuccess}
          erroresServidor={error.porCampo}
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

      <div className="p-5">
        {/* Arriba de todo y fuera de contenido(): anda aunque el período esté cerrado. */}
        <RecuperarAcceso enfocar={parametros.get('recuperar') === '1'} />
        {contenido()}
      </div>
    </>
  )
}
