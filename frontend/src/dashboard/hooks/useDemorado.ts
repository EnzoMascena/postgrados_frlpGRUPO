/* useDemorado.ts — Un valor que se actualiza recién cuando deja de cambiar.
   El buscador lo usa con 300 ms: mientras el coordinador escribe
   "Rodríguez" no se pide una página por cada letra, sino una sola
   cuando hace una pausa. */

import { useEffect, useState } from 'react'

export function useDemorado<T>(valor: T, ms: number): T {
  const [demorado, setDemorado] = useState(valor)

  useEffect(() => {
    // Cada cambio reinicia la cuenta; si llega otro antes de `ms`,
    // el anterior se cancela y no se usa nunca.
    const espera = setTimeout(() => setDemorado(valor), ms)
    return () => clearTimeout(espera)
  }, [valor, ms])

  return demorado
}
