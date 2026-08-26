/* ═══════════════════════════════════════════════════════════════
   CeldaAsistencia.tsx — LA CELDA CLICKEABLE DE LA PLANILLA
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Cada cuadradito de la grilla del docente. Un click cicla entre
   los tres valores: vacío → P (presente) → A (ausente) → vacío.
   El color acompaña: gris, verde, rojo.

   PUNTO INTERESANTE PARA MOSTRARLE AL PROFESOR:
   El ciclo está definido como un DATO (el objeto `siguiente`), no
   como una cadena de if. Se lee casi como una tabla: "si estoy en
   vacío, el próximo es P". Agregar un estado nuevo (por ejemplo
   "J" de justificado) sería agregar una línea, sin tocar lógica.

   La celda tampoco guarda nada: le avisa al padre con onChange y
   la planilla decide. Todo el estado vive en un solo lugar.
   ═══════════════════════════════════════════════════════════════ */

import type { Asistencia } from '../types'

// El ciclo del wireframe: vacío → P → A → vacío.
// En vez de buscar clases en el DOM, lo definimos como un dato.
const siguiente: Record<Asistencia, Asistencia> = {
  '': 'P',
  P: 'A',
  A: '',
}

const estilos: Record<Asistencia, string> = {
  '': 'bg-surface border-line-strong text-faint',
  P: 'bg-ok-bg border-ok-border text-ok',
  A: 'bg-danger-bg border-danger-border text-danger',
}

type Props = {
  valor: Asistencia
  onChange: (nuevo: Asistencia) => void
}

export default function CeldaAsistencia({ valor, onChange }: Props) {
  return (
    <button
      onClick={() => onChange(siguiente[valor])}
      title="Click para cambiar: vacío → P → A"
      className={
        'w-6 h-6 mx-auto flex items-center justify-center rounded border ' +
        'text-[11px] font-medium transition-colors hover:opacity-80 ' +
        estilos[valor]
      }
    >
      {valor}
    </button>
  )
}