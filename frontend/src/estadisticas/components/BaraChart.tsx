import type { BarraDato } from '../type'
 
const colores: Record<BarraDato['color'], string> = {
  primary: 'bg-primary',
  ok: 'bg-ok',
  warn: 'bg-warn',
  neutral: 'bg-faint',
}
 
type Props = {
  datos: BarraDato[]
  /** Valor que representa el 100% del ancho. Si no se pasa, se usa el mayor. */
  maximo?: number
  /** Cómo se muestra el número al final de cada fila. */
  sufijo?: string
}
 
// Gráfico de barras horizontales, hecho con divs (mismo patrón que
// BarraAsistencia). El ancho sale del dato: no se guarda aparte.
export default function BarraChart({ datos, maximo, sufijo = '' }: Props) {
  const tope = maximo ?? Math.max(...datos.map((d) => d.valor), 1)
 
  return (
    <div className="flex flex-col gap-2">
      {datos.map((d) => {
        const ancho = Math.round((d.valor / tope) * 100)
        return (
          <div key={d.label} className="flex items-center gap-2.5">
            <div className="w-24 flex-shrink-0 text-[11.5px] text-muted truncate">
              {d.label}
            </div>
            <div className="flex-1 h-4 rounded bg-surface border border-line overflow-hidden">
              <div
                className={'h-full rounded transition-all ' + colores[d.color]}
                style={{ width: `${ancho}%` }}
              />
            </div>
            <div className="w-10 flex-shrink-0 text-right text-[11.5px] font-medium text-ink">
              {d.valor}
              {sufijo}
            </div>
          </div>
        )
      })}
    </div>
  )
}
 