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

   Los campos viven en <FormularioDatos>, un componente aparte
   porque se reusa para editar los datos desde el seguimiento.

   PENDIENTE: el período (cohortes) se conecta en el checkpoint 2.3
   y el guardado en la API (POST /legajos) en el 2.4. Por ahora, al
   apretar el botón solo se valida y se avisa que está todo bien.
   ═══════════════════════════════════════════════════════════════ */

import { useState } from 'react'
import { IconClipboardList } from '@tabler/icons-react'
import Topbar from '../../shared/layout/Topbar'
import Badge from '../../shared/components/Badge'
import Alerta from '../../shared/components/Alerta'
import FormularioDatos from '../components/FormularioDatos'

export default function FormularioInscripcion() {
  // Temporal hasta el 2.4: avisa que los datos pasaron la validación.
  const [valido, setValido] = useState(false)

  return (
    <>
      <Topbar title="Formulario de preinscripción" icon={IconClipboardList}>
        <Badge variant="info">Período abierto</Badge>
      </Topbar>

      <div className="p-5">
        {valido && (
          <Alerta variant="success" className="mb-4">
            Los datos están completos. Todavía no se guardan: eso se conecta con la API en el
            próximo paso.
          </Alerta>
        )}
        <FormularioDatos
          textoBoton="Guardar y continuar con la documentación"
          onEnviar={() => {
            setValido(true)
            window.scrollTo({ top: 0, behavior: 'smooth' })
          }}
        />
      </div>
    </>
  )
}
