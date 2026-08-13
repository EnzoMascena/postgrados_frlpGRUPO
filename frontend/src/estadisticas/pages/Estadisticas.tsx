import { useState } from 'react'
import {
  IconChartBar,
  IconDownload,
  IconUsers,
  IconCircleCheck,
  IconFileText,
  IconChartLine,
} from '@tabler/icons-react'
import Topbar from '../../shared/layout/Topbar'
import Card from '../../shared/components/Card'
import Button from '../../shared/components/Button'
import StatCard from '../../shared/components/StatCard'
import BarraChart from '../components/BaraChart'
import type { BarraDato, CohorteStats } from '../type'
import {
  cohortesDisponibles,
  cohortesMock,
  seminariosCohorteActual,
  trabajosFinales,
} from '../data/estadisticasMock'
 
/* ── Cálculos derivados ───────────────────────────────────────
   Igual que en la planilla: los totales NO se guardan, se calculan
   a partir de las cohortes. Si cambia un número del mock, las stat
   cards, el gráfico y la tabla se actualizan solos y nunca quedan
   contradiciéndose entre sí.
   ─────────────────────────────────────────────────────────── */
 
function sumar(cohortes: CohorteStats[], campo: keyof CohorteStats): number {
  return cohortes.reduce((acum, c) => acum + c[campo], 0)
}
 
function porcentaje(parte: number, total: number): number {
  if (total === 0) return 0
  return Math.round((parte / total) * 100)
}
 
export default function Estadisticas() {
  const [cohorteFiltro, setCohorteFiltro] = useState('Todas las cohortes')
 
  // El filtro del topbar recorta los datos; todo lo demás se recalcula.
  const cohortes =
    cohorteFiltro === 'Todas las cohortes'
      ? cohortesMock
      : cohortesMock.filter((c) => String(c.anio) === cohorteFiltro)
 
  const totalInscriptos = sumar(cohortes, 'inscriptos')
  const totalGraduados = sumar(cohortes, 'graduados')
  const totalActivos = sumar(cohortes, 'activos')
  const totalDesgranados = sumar(cohortes, 'desgranados')
 
  // Gráfico de inscriptos: se arma desde las mismas cohortes.
  const barrasInscriptos: BarraDato[] = cohortes.map((c) => ({
    label: String(c.anio),
    valor: c.inscriptos,
    color: 'primary',
  }))
 
  const th =
    'text-left font-medium text-muted py-2 px-2 border-b border-line whitespace-nowrap'
  const td = 'py-2 px-2 border-b border-line text-ink'
 
  return (
    <>
      <Topbar title="Estadísticas y reportes" icon={IconChartBar}>
        <select
          value={cohorteFiltro}
          onChange={(e) => setCohorteFiltro(e.target.value)}
          className="px-2 py-1 rounded-input border border-line-strong bg-surface text-ink text-[12px] focus:outline-none focus:border-primary transition-colors"
        >
          {cohortesDisponibles.map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
        <Button>
          <IconDownload size={15} stroke={1.5} /> Exportar
        </Button>
      </Topbar>
 
      <div className="p-5">
        {/* Indicadores */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <StatCard
            label="Total histórico"
            valor={totalInscriptos}
            sub="Inscriptos desde 2022"
          />
          <StatCard
            label="Graduados"
            valor={totalGraduados}
            sub={`${porcentaje(totalGraduados, totalInscriptos)}% del total`}
          />
          <StatCard
            label="En curso"
            valor={totalActivos}
            sub={`${porcentaje(totalActivos, totalInscriptos)}% activos`}
          />
          <StatCard
            label="Desgranamiento"
            valor={totalDesgranados}
            sub={`${porcentaje(totalDesgranados, totalInscriptos)}% abandonaron`}
          />
        </div>
 
        {/* Dos columnas de gráficos */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card title="Inscriptos por cohorte" icon={IconUsers}>
            <BarraChart datos={barrasInscriptos} />
          </Card>
 
          <Card title="Estado de seminarios — cohorte 2026" icon={IconCircleCheck}>
            <BarraChart datos={seminariosCohorteActual} maximo={100} sufijo="%" />
 
            <div className="h-px bg-line my-4" />
 
            <div className="flex items-center gap-1.5 text-[13px] font-medium text-ink mb-3">
              <IconFileText size={15} stroke={1.5} />
              Trabajos finales — global
            </div>
            <BarraChart datos={trabajosFinales} maximo={100} sufijo="%" />
          </Card>
        </div>
 
        {/* Tabla de desgranamiento */}
        <Card
          title="Desgranamiento y ralentización por cohorte"
          icon={IconChartLine}
        >
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-[12px] border-collapse">
              <thead>
                <tr>
                  <th className={th}>Cohorte</th>
                  <th className={th}>Inscriptos</th>
                  <th className={th}>Activos</th>
                  <th className={th}>Graduados</th>
                  <th className={th}>Desgranam.</th>
                  <th className={th}>En ralentiz.</th>
                  <th className={th}>Tasa graduación</th>
                </tr>
              </thead>
              <tbody>
                {cohortes.map((c) => {
                  // La tasa sale de los datos, no está escrita a mano.
                  const tasa = porcentaje(c.graduados, c.inscriptos)
                  const colorTasa =
                    tasa >= 50 ? 'bg-ok' : tasa > 0 ? 'bg-warn' : 'bg-faint'
 
                  return (
                    <tr key={c.anio}>
                      <td className={td + ' font-medium'}>{c.anio}</td>
                      <td className={td}>{c.inscriptos}</td>
                      <td className={td}>{c.activos}</td>
                      <td className={td}>{c.graduados}</td>
                      <td className={td}>{c.desgranados}</td>
                      <td className={td}>{c.ralentizados}</td>
                      <td className={td}>
                        <div className="flex items-center gap-1.5">
                          <div className="w-14 h-1.5 rounded-full bg-line overflow-hidden">
                            <div
                              className={'h-full rounded-full transition-all ' + colorTasa}
                              style={{ width: `${tasa}%` }}
                            />
                          </div>
                          <span className="text-[10px] text-muted">
                            {tasa === 0 ? '—' : `${tasa}%`}
                          </span>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </>
  )
}