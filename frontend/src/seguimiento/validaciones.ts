/* ═══════════════════════════════════════════════════════════════
   validaciones.ts — ¿ESTE ARCHIVO SE PUEDE SUBIR?
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Antes de mandar un PDF, el navegador mira dos cosas que ya
   sabe sin subir nada: el nombre/tipo y el tamaño. Si no cumple,
   no se manda ni un byte y el aspirante ve el error al instante
   (un PDF de 20 MB en un celular tardaría minutos en rebotar).

   PERO el front solo ve la etiqueta del archivo, no lo que tiene
   adentro: un JPG renombrado a "dni.pdf" pasa este control. Por
   eso el back vuelve a validar mirando los primeros bytes
   (%PDF-), que es lo único que no se puede falsear con un nombre.

   OJO: file.type puede venir vacío (algunos sistemas no conocen
   el tipo). Si viene vacío, alcanza con que el nombre termine en
   .pdf; si viene otro tipo, no es PDF.
   ═══════════════════════════════════════════════════════════════ */

export const TAMANIO_MAXIMO_BYTES = 5 * 1024 * 1024 // 5 MB, igual que el back

// Los mensajes del SRS (RF-CORE-002), iguales a los del back.
export const MENSAJE_NO_ES_PDF = 'Solo se aceptan archivos en formato PDF'
export const MENSAJE_DEMASIADO_GRANDE = 'El archivo es demasiado grande. Máximo permitido: 5MB'

/** Un mensaje si el archivo no se puede subir; null si está bien. */
export function validarPdf(archivo: Pick<File, 'name' | 'type' | 'size'>): string | null {
  const nombrePdf = archivo.name.toLowerCase().endsWith('.pdf')
  const tipoPdf = archivo.type === '' || archivo.type === 'application/pdf'
  if (!nombrePdf || !tipoPdf) return MENSAJE_NO_ES_PDF
  if (archivo.size > TAMANIO_MAXIMO_BYTES) return MENSAJE_DEMASIADO_GRANDE
  return null
}
