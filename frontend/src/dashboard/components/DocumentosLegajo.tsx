/* ═══════════════════════════════════════════════════════════════
   DocumentosLegajo.tsx — CHECKLIST DE DOCUMENTOS Y VISOR DE PDF
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   La lista sale del back: qué documentos le corresponden a ESTE
   legajo (según beca y título de posgrado) y cuáles ya subió. Los
   obligatorios que faltan se ven en rojo.

   EL DETALLE DE SEGURIDAD — por qué el PDF no es un link:
   Los PDFs no tienen una URL pública. Para verlo, el front pide
   GET /documentos/{id}/download CON el token del coordinador, recibe
   el archivo como Blob y arma una URL temporal que existe solo en
   este navegador (URL.createObjectURL). El <iframe> del Modal
   muestra esa URL, y al cerrar se libera (URL.revokeObjectURL).
   Así nadie puede copiar un link y abrir el documento sin sesión.
   ═══════════════════════════════════════════════════════════════ */

import { useEffect, useRef, useState } from 'react'
import { IconCheck, IconFileText, IconX } from '@tabler/icons-react'
import Card from '../../shared/components/Card'
import Button from '../../shared/components/Button'
import Modal from '../../shared/components/Modal'
import Alerta from '../../shared/components/Alerta'
import Cargando from '../../shared/components/Cargando'
import type { ItemDocumento } from '../../shared/api/tipos'
import { descargarDocumento } from '../api'
import { fecha, tamanio } from '../formato'

type Visor =
  | { estado: 'cargando'; nombre: string }
  | { estado: 'listo'; nombre: string; url: string }
  | { estado: 'error'; nombre: string; mensaje: string }

export default function DocumentosLegajo({ documentos }: { documentos: ItemDocumento[] }) {
  const [visor, setVisor] = useState<Visor | null>(null)
  const url = visor?.estado === 'listo' ? visor.url : null

  // Cuando la URL temporal deja de usarse (se cierra el visor o se
  // abre otro documento), se libera la memoria del Blob.
  useEffect(() => {
    if (!url) return
    return () => URL.revokeObjectURL(url)
  }, [url])

  // Cada "Ver" tiene su número. Si mientras baja el PDF se cerró el
  // visor o se abrió otro, la respuesta vieja se descarta.
  const ultimoPedido = useRef(0)

  async function ver(doc: ItemDocumento) {
    if (!doc.documentoId) return
    const pedido = ++ultimoPedido.current
    setVisor({ estado: 'cargando', nombre: doc.nombre })
    try {
      const { blob } = await descargarDocumento(doc.documentoId)
      if (pedido !== ultimoPedido.current) return
      setVisor({ estado: 'listo', nombre: doc.nombre, url: URL.createObjectURL(blob) })
    } catch (error) {
      if (pedido !== ultimoPedido.current) return
      setVisor({ estado: 'error', nombre: doc.nombre, mensaje: (error as Error).message })
    }
  }

  function cerrar() {
    ultimoPedido.current++
    setVisor(null)
  }

  const faltan = documentos.filter((d) => d.obligatorio && !d.cargado).length

  return (
    <Card title="Documentación" icon={IconFileText}>
      <p className="text-[12px] text-muted mb-3">
        {faltan === 0
          ? 'Están todos los documentos obligatorios.'
          : faltan === 1
            ? 'Falta 1 documento obligatorio.'
            : `Faltan ${faltan} documentos obligatorios.`}
      </p>

      <ul className="divide-y divide-line">
        {documentos.map((doc) => {
          const falta = doc.obligatorio && !doc.cargado
          return (
            <li key={doc.tipo} className="py-2.5 flex flex-wrap items-center gap-x-3 gap-y-1.5">
              <div className="flex-1 min-w-[200px]">
                <div className="text-[12.5px] text-ink">
                  {doc.nombre}
                  {!doc.obligatorio && <span className="text-muted"> (opcional)</span>}
                </div>
                {doc.cargado && doc.nombreOriginal && (
                  <div className="text-[11px] text-muted break-all">
                    {doc.nombreOriginal}
                    {doc.tamanioBytes !== null && ` · ${tamanio(doc.tamanioBytes)}`}
                    {doc.fechaSubida && ` · ${fecha(doc.fechaSubida)}`}
                  </div>
                )}
              </div>

              {doc.cargado ? (
                <span className="inline-flex items-center gap-1 text-[11.5px] text-ok">
                  <IconCheck size={14} stroke={2} aria-hidden="true" /> Cargado
                </span>
              ) : (
                <span
                  className={
                    'inline-flex items-center gap-1 text-[11.5px] ' + (falta ? 'text-danger' : 'text-muted')
                  }
                >
                  <IconX size={14} stroke={2} aria-hidden="true" /> Pendiente
                </span>
              )}

              <Button
                className="text-[11px] px-2.5 py-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={!doc.documentoId}
                onClick={() => ver(doc)}
                aria-label={`Ver ${doc.nombre}`}
              >
                Ver
              </Button>
            </li>
          )
        })}
      </ul>

      <Modal abierto={visor !== null} titulo={visor?.nombre ?? ''} onCerrar={cerrar} grande>
        {visor?.estado === 'cargando' && <Cargando texto="Abriendo el documento…" />}
        {visor?.estado === 'error' && (
          <Alerta variant="danger">No se pudo abrir el documento. {visor.mensaje}</Alerta>
        )}
        {visor?.estado === 'listo' && (
          <iframe
            src={visor.url}
            title={visor.nombre}
            className="w-full h-[70vh] rounded-input border border-line bg-surface"
          />
        )}
      </Modal>
    </Card>
  )
}
