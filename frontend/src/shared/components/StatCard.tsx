type Props = {
  label: string
  valor: number | string
  sub?: string
}
 
// Tarjeta de indicador. Vive en shared/ porque también la usa el Dashboard.
export default function StatCard({ label, valor, sub }: Props) {
  return (
    <div className="bg-card border border-line rounded-card shadow-card p-4">
      <div className="text-[11px] uppercase tracking-wide text-muted">{label}</div>
      <div className="text-[26px] font-medium text-ink leading-tight mt-1">{valor}</div>
      {sub && <div className="text-[11px] text-faint mt-0.5">{sub}</div>}
    </div>
  )
}
 