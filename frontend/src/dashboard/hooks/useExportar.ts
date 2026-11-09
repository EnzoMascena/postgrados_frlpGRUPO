/* ═══════════════════════════════════════════════════════════════
   useExportar.ts — EL BOTÓN "EXPORTAR" DEL DASHBOARD
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   El Excel lo arma el back (GET /legajos/exportar) con los mismos
   filtros que la tabla. Como el pedido lleva el token, no alcanza
   con un <a href>: el front lo pide con apiDescargar, recibe el
   archivo como Blob y lo guarda con un truco del navegador:
     1. URL.createObjectURL(blob) → una URL temporal, solo de esta pestaña.
     2. Un <a download="nombre"> invisible con esa URL, y un click.
     3. URL.revokeObjectURL → se libera la memoria.
   El nombre del archivo es el que manda el back en Content-Disposition.

   Es un useMutation (no un useQuery) porque es una acción que el
   usuario dispara, no un dato que se muestra: nos da isPending para
   deshabilitar el botón mientras baja y el error para la Alerta.
   ═══════════════════════════════════════════════════════════════ */

import { useMutation } from '@tanstack/react-query'
import { exportarLegajos } from '../api'

function guardarArchivo(blob: Blob, nombreArchivo: string) {
  const url = URL.createObjectURL(blob)
  const enlace = document.createElement('a')
  enlace.href = url
  enlace.download = nombreArchivo
  document.body.appendChild(enlace)
  enlace.click()
  enlace.remove()
  // Se libera después del click: algunos navegadores todavía la están leyendo.
  setTimeout(() => URL.revokeObjectURL(url), 0)
}

/** GET /legajos/exportar y guarda el archivo con el nombre del back. */
export function useExportar() {
  return useMutation({
    mutationFn: exportarLegajos,
    onSuccess: ({ blob, nombreArchivo }) => guardarArchivo(blob, nombreArchivo),
  })
}
