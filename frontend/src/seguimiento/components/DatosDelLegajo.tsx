/* ═══════════════════════════════════════════════════════════════
   DatosDelLegajo.tsx — VER O EDITAR MIS DATOS (US-CORE-004)
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Muestra el resumen de los datos (ResumenDatos) y, si el legajo
   se puede editar (`puedeEditar`: Borrador u Observado), un botón
   "Editar mis datos". Al tocarlo, en el mismo lugar aparece el
   MISMO formulario de la inscripción (FormularioDatos), cargado
   con los datos actuales: no hay un segundo formulario que
   mantener, y las validaciones en tiempo real son las mismas.

   La cohorte no aparece: no se cambia al editar (el PUT no la
   recibe). Guardar (PUT /seguimiento/{token}) lo hace el padre
   con `onGuardar`; acá solo se muestra y se avisa.

   Los errores del back se reparten igual que en la inscripción
   (separarError): con `field`, al lado de ese campo; sin `field`
   (por ejemplo, 409 LEGAJO_NO_EDITABLE), en una Alerta arriba.
   ═══════════════════════════════════════════════════════════════ */

import { useEffect, useMemo, useRef } from 'react'
import { IconPencil } from '@tabler/icons-react'
import Alerta from '../../shared/components/Alerta'
import Button from '../../shared/components/Button'
import type { LegajoDetalle } from '../../shared/api/tipos'
import FormularioDatos from '../../inscripcion/components/FormularioDatos'
import type { DatosInscripcion } from '../../inscripcion/types'
import { separarError } from '../../inscripcion/api'
import { datosDesdeLegajo } from '../edicion'
import ResumenDatos from './ResumenDatos'

type Props = {
  legajo: LegajoDetalle
  editando: boolean
  onEditar: () => void
  onCancelar: () => void
  /** Hace el PUT /seguimiento/{token}. */
  onGuardar: (datos: DatosInscripcion) => void
  guardando: boolean
  /** El error del PUT, si falló. */
  error: Error | null
}

export default function DatosDelLegajo({
  legajo,
  editando,
  onEditar,
  onCancelar,
  onGuardar,
  guardando,
  error,
}: Props) {
  // Mismo objeto mientras el error no cambie: FormularioDatos lo compara para
  // saber si llegaron errores nuevos y llevar el foco al primero.
  const errorSeparado = useMemo(() => separarError(error), [error])

  // El botón "Guardar cambios" está abajo y la Alerta de un error sin campo,
  // arriba del formulario: si aparece, la llevamos a la vista (como en la
  // inscripción). Los errores con campo ya los enfoca FormularioDatos.
  const alertaArriba = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (errorSeparado.general) {
      alertaArriba.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [errorSeparado.general])

  if (!editando) {
    return (
      <section aria-label="Mis datos">
        {legajo.puedeEditar && (
          <div className="flex justify-end mb-2">
            <Button type="button" onClick={onEditar}>
              <IconPencil size={15} stroke={1.5} aria-hidden />
              Editar mis datos
            </Button>
          </div>
        )}
        <ResumenDatos legajo={legajo} />
      </section>
    )
  }

  return (
    <section aria-label="Editar mis datos">
      <h2 className="text-[14px] font-medium text-ink mb-1">Editar mis datos</h2>
      <p className="text-[12px] text-muted mb-3.5">
        Corregí lo que haga falta y guardá. La cohorte no se puede cambiar.
      </p>
      <div ref={alertaArriba}>
        {errorSeparado.general && (
          <Alerta variant="danger" className="mb-4">
            {errorSeparado.general}
          </Alerta>
        )}
      </div>
      {/* FormularioDatos copia los valores iniciales en su estado al abrirse:
          si mientras tanto se refresca el legajo, no pisa lo que se está escribiendo. */}
      <FormularioDatos
        valoresIniciales={datosDesdeLegajo(legajo)}
        onEnviar={onGuardar}
        enviando={guardando}
        erroresServidor={errorSeparado.porCampo}
        textoBoton="Guardar cambios"
        onCancelar={onCancelar}
      />
    </section>
  )
}
