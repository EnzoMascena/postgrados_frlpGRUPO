/* ═══════════════════════════════════════════════════════════════
   Dashboard.tsx — PANTALLA DE CONDUCCIÓN (Secretaría de Posgrado)
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Es el panel de control de quien gestiona la carrera. De un
   vistazo responde: ¿cuántos se inscribieron?, ¿quiénes tienen
   el legajo completo?, ¿cuántos pidieron beca?

   QUÉ SE VE EN PANTALLA:
     · Arriba: selector de COHORTE (año de ingreso) y el
       interruptor para abrir/cerrar el período de inscripción.
     · 4 tarjetas de indicadores (total, completos, incompletos,
       con beca).
     · Una tabla con todos los inscriptos, con buscador por
       nombre o DNI y botón de exportar.

   LA IDEA TÉCNICA MÁS IMPORTANTE — DATOS DERIVADOS:
   Los números de las tarjetas NO están escritos a mano ni
   guardados en ningún lado: se CALCULAN a partir de la lista de
   inscriptos cada vez que se dibuja la pantalla. Por eso nunca
   pueden contradecirse entre sí. Si mañana esa lista viene del
   backend en vez del mock, las tarjetas siguen funcionando igual.

   MÉTODOS DE JAVASCRIPT QUE USAMOS (por si preguntan):
     .filter() → se queda solo con los elementos que cumplen algo
     .length   → cuántos quedaron
     .map()    → transforma cada elemento (acá: cada inscripto en
                 una fila <tr> de la tabla)

   DATOS: hoy salen de data/dashboardMock.ts (datos de prueba).
   Los tipos están en type.ts y ya describen cómo va a responder
   la API del backend.
   ═══════════════════════════════════════════════════════════════ */

import { useState } from 'react'
import {
  IconLayoutDashboard,
  IconUsers,
  IconDownload,
  IconSearch,
} from '@tabler/icons-react'
import Topbar from '../../shared/layout/Topbar'
import Card from '../../shared/components/Card'
import Badge from '../../shared/components/Badge'
import Button from '../../shared/components/Button'
import StatCard from '../../shared/components/StatCard'
import BarraProgreso from '../../shared/components/Barraprogreso'
import PeriodoToggle from '../components/PeriodoToggle'
import type { Beca, Inscripto } from '../type'
import { DOCUMENTOS_REQUERIDOS } from '../type'
import { cohortesDisponibles, inscriptosMock } from '../data/dashboardMock'

/* ── Cálculos derivados ───────────────────────────────────────
   Igual que en la planilla y en estadísticas: los totales y la
   completitud NO se guardan, se calculan desde la lista. Si cambia
   un dato del mock, las tarjetas y la tabla se actualizan solas.
   ─────────────────────────────────────────────────────────── */

/** Qué porcentaje del legajo tiene presentado un inscripto.
    Ej: 4 documentos de 6 requeridos → 67%. */
function completitud(i: Inscripto): number {
  return Math.round((i.documentosPresentados / DOCUMENTOS_REQUERIDOS) * 100)
}

function porcentaje(parte: number, total: number): number {
  if (total === 0) return 0
  return Math.round((parte / total) * 100)
}

/* Estos dos objetos traducen el dato interno a lo que se ve en
   pantalla: el texto de la etiqueta y su color. Se hace con un
   objeto en vez de una cadena de if/else porque queda más corto
   y es más fácil agregar un caso nuevo. */
const etiquetaBeca: Record<Beca, string> = {
  sin: 'Sin beca',
  '30': '30%',
  '100': '100%',
}

const variantBeca: Record<Beca, 'info' | 'success' | 'warn' | 'danger'> = {
  sin: 'warn',
  '30': 'info',
  '100': 'success',
}

export default function Dashboard() {
  // Los 3 estados de la pantalla: qué cohorte se está mirando,
  // qué escribió el usuario en el buscador y si el período de
  // inscripción está abierto o cerrado.
  const [cohorte, setCohorte] = useState('2026')
  const [busqueda, setBusqueda] = useState('')
  const [periodoAbierto, setPeriodoAbierto] = useState(true)

  // 1) Recorte por cohorte: base de las tarjetas.
  const deLaCohorte = inscriptosMock.filter((i) => i.cohorte === cohorte)

  // 2) Recorte adicional por búsqueda: solo afecta a la tabla.
  const termino = busqueda.trim().toLowerCase()
  const visibles = termino
    ? deLaCohorte.filter(
        (i) =>
          i.apellidoNombre.toLowerCase().includes(termino) ||
          i.dni.replace(/\./g, '').includes(termino.replace(/\./g, '')),
      )
    : deLaCohorte

  // 3) Los indicadores: todos salen de contar sobre la misma lista.
  const total = deLaCohorte.length
  const completos = deLaCohorte.filter((i) => completitud(i) === 100).length
  const incompletos = total - completos
  const conBeca = deLaCohorte.filter((i) => i.beca !== 'sin').length
  const beca30 = deLaCohorte.filter((i) => i.beca === '30').length
  const beca100 = deLaCohorte.filter((i) => i.beca === '100').length

  // Guardamos en variables las clases de estilo de la tabla para no
  // repetir la misma lista de clases en cada celda.
  const th =
    'text-left font-medium text-muted py-2 px-2 border-b border-line whitespace-nowrap'
  const td = 'py-2 px-2 border-b border-line text-ink'

  return (
    <>
      <Topbar title="Dashboard · Conducción" icon={IconLayoutDashboard}>
        <select
          value={cohorte}
          onChange={(e) => setCohorte(e.target.value)}
          className="px-2 py-1 rounded-input border border-line-strong bg-surface text-ink text-[12px] focus:outline-none focus:border-primary transition-colors"
        >
          {/* Las opciones del desplegable se generan recorriendo la
              lista de cohortes disponibles, no se escriben a mano. */}
          {cohortesDisponibles.map((c) => (
            <option key={c} value={c}>
              Cohorte {c}
            </option>
          ))}
        </select>

        <PeriodoToggle
          abierto={periodoAbierto}
          onToggle={() => setPeriodoAbierto((v) => !v)}
        />
      </Topbar>

      <div className="p-5">
        {/* Indicadores: las 4 tarjetas de arriba. Reciben el número
            ya calculado; StatCard solo se ocupa de mostrarlo. */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <StatCard label="Total inscriptos" valor={total} sub={`Cohorte ${cohorte}`} />
          <StatCard
            label="Legajos completos"
            valor={completos}
            sub={`${porcentaje(completos, total)}% del total`}
          />
          <StatCard
            label="Legajos incompletos"
            valor={incompletos}
            sub="Pendientes de doc."
          />
          <StatCard
            label="Con beca"
            valor={conBeca}
            sub={`30% → ${beca30} · 100% → ${beca100}`}
          />
        </div>

        {/* Tabla de inscriptos */}
        <Card>
          <div className="flex items-center justify-between gap-3 flex-wrap mb-3.5">
            <div className="flex items-center gap-1.5 text-[13px] font-medium text-ink">
              <IconUsers size={15} stroke={1.5} />
              Inscriptos — Cohorte {cohorte}
            </div>

            <div className="flex items-center gap-2">
              <div className="relative">
                <IconSearch
                  size={14}
                  stroke={1.5}
                  className="absolute left-2.5 top-1/2 -translate-y-1/2 text-faint"
                />
                <input
                  value={busqueda}
                  onChange={(e) => setBusqueda(e.target.value)}
                  placeholder="Buscar por nombre o DNI..."
                  className="w-[220px] pl-8 pr-3 py-1.5 rounded-input border border-line-strong bg-surface text-ink text-[12px] placeholder:text-faint focus:outline-none focus:border-primary transition-colors"
                />
              </div>
              <Button>
                <IconDownload size={15} stroke={1.5} /> Exportar
              </Button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-[12px] border-collapse">
              <thead>
                <tr>
                  <th className={th}>Apellido y nombre</th>
                  <th className={th}>DNI</th>
                  <th className={th}>Carrera</th>
                  <th className={th}>Beca</th>
                  <th className={th}>Estado legajo</th>
                  <th className={th}>Completitud</th>
                  <th className={th}></th>
                </tr>
              </thead>

              <tbody>
                {/* Una fila por inscripto visible. `key` es un
                    identificador único que React necesita para saber
                    qué fila cambió y no redibujar la tabla entera. */}
                {visibles.map((i) => {
                  const pct = completitud(i)
                  const completo = pct === 100

                  return (
                    <tr key={i.id}>
                      <td className={td + ' font-medium'}>{i.apellidoNombre}</td>
                      <td className={td + ' text-muted'}>{i.dni}</td>
                      <td className={td}>{i.carrera}</td>
                      <td className={td}>
                        <Badge variant={variantBeca[i.beca]}>
                          {etiquetaBeca[i.beca]}
                        </Badge>
                      </td>
                      <td className={td}>
                        <Badge variant={completo ? 'success' : 'warn'}>
                          {completo ? 'Completo' : 'Incompleto'}
                        </Badge>
                      </td>
                      <td className={td}>
                        <BarraProgreso porcentaje={pct} />
                      </td>
                      <td className={td}>
                        <Button className="text-[11px] px-2.5 py-0.5">
                          Ver legajo
                        </Button>
                      </td>
                    </tr>
                  )
                })}

                {/* Mensaje para cuando la búsqueda no encuentra nada:
                    una tabla vacía sin explicación confunde al usuario. */}
                {visibles.length === 0 && (
                  <tr>
                    <td colSpan={7} className="py-6 text-center text-[12px] text-muted">
                      No se encontraron inscriptos con ese criterio.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between mt-2.5 pt-2.5 border-t border-line">
            <span className="text-[11px] text-muted">
              Mostrando {visibles.length} de {total} inscriptos
            </span>
            <div className="flex gap-1">
              <Button className="text-[11px] px-2.5 py-0.5">← Ant.</Button>
              <Button className="text-[11px] px-2.5 py-0.5">Sig. →</Button>
            </div>
          </div>
        </Card>
      </div>
    </>
  )
}