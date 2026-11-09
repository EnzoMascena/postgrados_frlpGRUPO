/* ═══════════════════════════════════════════════════════════════
   Documentacion.tsx — LOS PDFs DEL ASPIRANTE (US-CORE-003)
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   En la entrega 2 esta card estaba en el formulario y no subía
   nada. Se pasó acá porque para guardar un PDF el legajo tiene
   que existir. La lista no está fija en el front: sale de
   `documentos` del back, que ya trae solo los que le tocan a este
   aspirante (los 5 obligatorios, más el título de posgrado si lo
   declaró y el formulario de beca si pidió beca).

   EL RECORRIDO DE UN PDF:
     1. Elige el archivo en un UploadBox.
     2. validarPdf() en el navegador: si no es PDF o pesa más de
        5 MB, el error sale al toque y NO se manda nada.
     3. Si pasa, useSubirDocumento → POST con FormData.
     4. El back vuelve a validar (los bytes reales). Si lo frena,
        su mensaje sale en ese mismo documento.
     5. Si sale bien, se invalida ['seguimiento', token] y la
        caja pasa a Cargado ✓ con el nombre del archivo.

   Cada documento es su propio <ItemDocumento> con su propia
   mutación: así se pueden subir dos a la vez y cada uno muestra
   su "Subiendo…" y su error sin pisarse.

   Solo se sube si `puedeEditar` (Borrador u Observado). Si no,
   la lista queda de solo lectura, pero se puede seguir viendo.
   ═══════════════════════════════════════════════════════════════ */

import { useState } from 'react'
import { IconCheck, IconExternalLink, IconFileText, IconX } from '@tabler/icons-react'
import Badge from '../../shared/components/Badge'
import Card from '../../shared/components/Card'
import UploadBox, { type EstadoUpload } from '../../shared/components/UploadBox'
import type { ItemDocumento as Item, LegajoDetalle, TipoDocumento } from '../../shared/api/tipos'
import { urlDescarga } from '../api'
import { useSubirDocumento } from '../hooks/useSeguimiento'
import { validarPdf } from '../validaciones'

// Los que hay que imprimir, firmar a mano y escanear (como en el wireframe).
const HINT: Partial<Record<TipoDocumento, string>> = {
  FORM_INSCRIPCION: 'Con firma analógica · máx 5 MB',
  FORM_BECA: 'Con firma analógica · máx 5 MB',
}

type PropsItem = {
  token: string
  item: Item
  editable: boolean
  faltante: boolean
}

function ItemDocumento({ token, item, editable, faltante }: PropsItem) {
  const subida = useSubirDocumento(token)
  // El error del navegador (paso 2); el del back viene en subida.error.
  const [errorLocal, setErrorLocal] = useState<string | null>(null)

  function elegir(archivo: File) {
    subida.reset()
    const error = validarPdf(archivo)
    setErrorLocal(error)
    if (!error) subida.mutate({ tipo: item.tipo, archivo })
  }

  const error = errorLocal ?? subida.error?.message ?? null
  let estado: EstadoUpload = item.cargado ? 'cargado' : 'pendiente'
  if (subida.isPending) estado = 'subiendo'
  else if (error) estado = 'error'

  return (
    <UploadBox
      id={`documento-${item.tipo}`}
      label={item.nombre}
      optional={!item.obligatorio}
      hint={HINT[item.tipo]}
      estado={estado}
      // Con error se sigue mostrando el que ya estaba subido, si había.
      nombreArchivo={item.cargado ? item.nombreOriginal : null}
      error={error}
      deshabilitado={!editable}
      faltante={faltante}
      onArchivo={elegir}
      acciones={
        <>
          {item.cargado ? (
            <Badge variant="success">
              <IconCheck size={12} stroke={2} className="mr-0.5" aria-hidden />
              Cargado
            </Badge>
          ) : (
            <Badge variant={item.obligatorio ? 'danger' : 'info'}>
              <IconX size={12} stroke={2} className="mr-0.5" aria-hidden />
              Pendiente
            </Badge>
          )}
          {item.cargado && item.documentoId && (
            <a
              href={urlDescarga(token, item.documentoId)}
              target="_blank"
              rel="noopener"
              className="inline-flex items-center gap-0.5 text-[12px] text-primary hover:underline"
              aria-label={`Ver ${item.nombre} (se abre en otra pestaña)`}
            >
              Ver
              <IconExternalLink size={12} stroke={1.5} aria-hidden />
            </a>
          )}
        </>
      }
    />
  )
}

type Props = {
  token: string
  legajo: LegajoDetalle
  /** Los que hay que marcar en rojo (los usa "Enviar a revisión" en G4). */
  faltantes?: readonly TipoDocumento[]
}

export default function Documentacion({ token, legajo, faltantes = [] }: Props) {
  const editable = legajo.puedeEditar === true
  const cargados = legajo.documentos.filter((d) => d.cargado).length

  return (
    <Card title="Documentación requerida (PDF)" icon={IconFileText}>
      <p className="text-[12px] text-muted -mt-1.5 mb-3.5">
        {cargados} de {legajo.documentos.length} cargados.{' '}
        {editable
          ? 'Solo PDF de hasta 5 MB. Si subís otro del mismo tipo, reemplaza al anterior.'
          : 'Tu legajo ya no está en Borrador ni Observado: la documentación no se puede cambiar.'}
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-3 gap-y-4">
        {legajo.documentos.map((item) => (
          <ItemDocumento
            key={item.tipo}
            token={token}
            item={item}
            editable={editable}
            faltante={faltantes.includes(item.tipo)}
          />
        ))}
      </div>
    </Card>
  )
}
