type Props = {
  porcentaje: number
  /** Ancho de la barra en píxeles. */
  ancho?: number
}

// Barra de progreso con color derivado del propio valor.
// Vive en shared/ porque la usan el Dashboard y el Legajo.
export default function BarraProgreso({ porcentaje, ancho = 80 }: Props) {
  const color =
    porcentaje >= 100 ? 'bg-ok' : porcentaje >= 50 ? 'bg-warn' : 'bg-danger'

  return (
    <div className="flex items-center gap-1.5">
      <div
        className="h-1.5 rounded-full bg-line overflow-hidden flex-shrink-0"
        style={{ width: `${ancho}px` }}
      >
        <div
          className={'h-full rounded-full transition-all ' + color}
          style={{ width: `${porcentaje}%` }}
        />
      </div>
      <span className="text-[10px] text-muted">{porcentaje}%</span>
    </div>
  )
}