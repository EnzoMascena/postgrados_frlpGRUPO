type Props = {
  porcentaje: number
}

// El color sale del propio porcentaje: no hace falta guardarlo aparte.
export default function BarraAsistencia({ porcentaje }: Props) {
  const colorBarra =
    porcentaje >= 75 ? 'bg-ok' : porcentaje >= 50 ? 'bg-warn' : 'bg-danger'
  const colorTexto = porcentaje < 50 ? 'text-danger' : 'text-ink'

  return (
    <div className="flex items-center gap-1.5 justify-center">
      <div className="w-10 h-1.5 rounded-full bg-line overflow-hidden">
        <div
          className={'h-full rounded-full transition-all ' + colorBarra}
          style={{ width: `${porcentaje}%` }}
        />
      </div>
      <span className={'text-[10px] ' + colorTexto}>{porcentaje}%</span>
    </div>
  )
}