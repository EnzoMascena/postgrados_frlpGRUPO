/* ═══════════════════════════════════════════════════════════════
   Dashboard.tsx — PANTALLA DE CONDUCCIÓN (Secretaría de Posgrado)
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Es el panel de control de quien gestiona la carrera. De un
   vistazo responde: ¿cuántos se inscribieron?, ¿cuántos hay para
   revisar?, ¿cuántos pidieron beca?

   QUÉ SE VE EN PANTALLA:
     · Arriba: selector de COHORTE (año de ingreso) y el
       interruptor para abrir/cerrar el período de inscripción.
     · 4 tarjetas de indicadores (total, para revisar, aprobados,
       con beca).
     · Una tabla con los inscriptos de la cohorte, de a 20, con
       buscador por DNI o apellido, filtros por estado, carrera y
       beca, y botón de exportar.

   LA IDEA TÉCNICA MÁS IMPORTANTE — EL ESTADO VIENE DEL SERVIDOR:
   Las cohortes y su período salen de GET /cohortes, los números
   de las tarjetas de GET /legajos/resumen y las filas de la tabla
   de GET /legajos: el back filtra, cuenta y pagina en la base. La
   pantalla solo guarda lo que eligió el usuario (qué cohorte
   mira, qué buscó, qué filtros puso, en qué página está). Cada
   cambio arma filtros nuevos y TanStack Query pide esa página.

   MÉTODOS DE JAVASCRIPT QUE USAMOS (por si preguntan):
     .find()   → el primer elemento que cumple algo (la cohorte)
     .reduce() → junta varios valores en uno (suma estados)
     .map()    → transforma cada elemento (acá: cada legajo en
                 una fila <tr> de la tabla)
   ═══════════════════════════════════════════════════════════════ */

import { useState } from 'react'
import { Link } from 'react-router'
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
import Alerta from '../../shared/components/Alerta'
import Cargando from '../../shared/components/Cargando'
import EstadoBadge from '../../shared/components/EstadoBadge'
import BarraProgreso from '../../shared/components/Barraprogreso'
import { useCarreras, useCohortes } from '../../shared/hooks/useCatalogos'
import {
  ETIQUETA_ESTADO,
  type Cohorte,
  type EstadoLegajo,
  type LegajoItem,
  type Variante,
} from '../../shared/api/tipos'
import PeriodoToggle from '../components/PeriodoToggle'
import CerrarInscripcion from '../components/CerrarInscripcion'
import { useCambiarPeriodo, useLegajos, useResumen } from '../hooks/useDashboard'
import { useDemorado } from '../hooks/useDemorado'
import { useExportar } from '../hooks/useExportar'
import type { FiltrosLegajos } from '../api'

const TAMANIO_PAGINA = 20
const MINIMO_LETRAS = 3 // con menos, el back responde 422 (plan §10)

/** La cohorte que se ve al entrar: la abierta más nueva, o la más
    nueva si no hay ninguna abierta. GET /cohortes ya viene de la
    más nueva a la más vieja. */
function cohortePorDefecto(cohortes: Cohorte[]): Cohorte | undefined {
  return cohortes.find((c) => c.inscripcionAbierta) ?? cohortes[0]
}

/** Qué manda el buscador al back. Un DNI se puede escribir con
    puntos o espacios ("28.456.789"): se mandan solo los números.
    Un apellido necesita 3 letras; con menos no se busca y se avisa. */
function interpretarBusqueda(texto: string): { q: string | null; aviso: string | null } {
  const limpio = texto.trim()
  const soloNumeros = limpio.replace(/[.\s]/g, '')
  if (limpio === '') return { q: null, aviso: null }
  if (/^\d+$/.test(soloNumeros)) return { q: soloNumeros, aviso: null }
  if (limpio.length < MINIMO_LETRAS) {
    return { q: null, aviso: `Escribí al menos ${MINIMO_LETRAS} letras del apellido.` }
  }
  return { q: limpio, aviso: null }
}

/** Qué porcentaje de los documentos obligatorios cargó.
    Ej: 4 documentos de 6 requeridos → 67%. */
function completitud(l: LegajoItem): number {
  if (l.documentosRequeridos === 0) return 100
  return Math.round((l.documentosCargados / l.documentosRequeridos) * 100)
}

/* Estos dos objetos traducen el dato interno a lo que se ve en
   pantalla: el texto de la etiqueta y su color. Se hace con un
   objeto en vez de una cadena de if/else porque queda más corto
   y es más fácil agregar un caso nuevo. */
type Beca = 'sin' | '30' | '100'

const etiquetaBeca: Record<Beca, string> = {
  sin: 'Sin beca',
  '30': '30%',
  '100': '100%',
}

const variantBeca: Record<Beca, Variante> = {
  sin: 'warn',
  '30': 'info',
  '100': 'success',
}

const ESTADOS = Object.keys(ETIQUETA_ESTADO) as EstadoLegajo[]

export default function Dashboard() {
  // Lo único que guarda la pantalla: lo que eligió el usuario.
  // cohorteId null = todavía ninguna, se usa la de por defecto.
  const [cohorteId, setCohorteId] = useState<string | null>(null)
  const [busqueda, setBusqueda] = useState('')
  const [estado, setEstado] = useState<FiltrosLegajos['estado']>('')
  const [carrera, setCarrera] = useState('')
  const [beca, setBeca] = useState<FiltrosLegajos['beca']>('')
  const [pagina, setPagina] = useState(1)
  const [confirmandoCierre, setConfirmandoCierre] = useState(false)

  const cohortes = useCohortes()
  const carreras = useCarreras()
  const lista = cohortes.data ?? []
  const cohorte = lista.find((c) => c.id === cohorteId) ?? cohortePorDefecto(lista)

  const resumen = useResumen(cohorte?.id)
  const periodo = useCambiarPeriodo()

  // El buscador pide recién cuando el usuario deja de escribir
  // 300 ms. El aviso de "3 letras", en cambio, se ve al instante.
  const buscado = useDemorado(busqueda, 300)
  const { q } = interpretarBusqueda(buscado)
  const { aviso } = interpretarBusqueda(busqueda)

  // Los mismos filtros arman la página de la tabla y el Excel: lo que
  // se exporta es lo que se está viendo, pero sin cortar en 20.
  const filtros = cohorte && { cohorte: cohorte.id, q, estado, carrera, beca }
  const legajos = useLegajos(filtros && { ...filtros, page: pagina, size: TAMANIO_PAGINA })
  const exportar = useExportar()
  const filas = legajos.data?.items ?? []
  const total = legajos.data?.total ?? 0
  const hayAnterior = pagina > 1
  const haySiguiente = pagina * TAMANIO_PAGINA < total

  // Cambiar cualquier filtro vuelve a la página 1: la 3 de una
  // búsqueda vieja puede no existir en la nueva.
  function filtrar(cambio: () => void) {
    cambio()
    setPagina(1)
  }

  // Abrir es un click; cerrar pide confirmación (y la próxima apertura).
  function alternarPeriodo() {
    if (!cohorte) return
    periodo.reset()
    if (cohorte.inscripcionAbierta) {
      setConfirmandoCierre(true)
    } else {
      periodo.mutate({ cohorteId: cohorte.id, abierta: true, proximaApertura: null })
    }
  }

  function cerrarPeriodo(proximaApertura: string | null) {
    if (!cohorte) return
    periodo.mutate(
      { cohorteId: cohorte.id, abierta: false, proximaApertura },
      { onSuccess: () => setConfirmandoCierre(false) },
    )
  }

  // Las tarjetas suman estados del resumen: "Para revisar" son los
  // pendientes y los que están en revisión, por ejemplo.
  const r = resumen.data
  const cuantos = (...estados: EstadoLegajo[]) =>
    estados.reduce((suma, e) => suma + (r?.porEstado[e] ?? 0), 0)

  // Guardamos en variables las clases de estilo para no repetir la
  // misma lista de clases en cada celda y en cada filtro.
  const th =
    'text-left font-medium text-muted py-2 px-2 border-b border-line whitespace-nowrap'
  const td = 'py-2 px-2 border-b border-line text-ink'
  const control =
    'w-full sm:w-auto px-2 py-1.5 rounded-input border border-line-strong bg-surface text-ink text-[12px] focus:outline-none focus:border-primary transition-colors'

  return (
    <>
      <Topbar title="Dashboard · Conducción" icon={IconLayoutDashboard}>
        <select
          aria-label="Cohorte"
          value={cohorte?.id ?? ''}
          onChange={(e) => filtrar(() => setCohorteId(e.target.value))}
          disabled={!cohorte}
          className="px-2 py-1 rounded-input border border-line-strong bg-surface text-ink text-[12px] focus:outline-none focus:border-primary transition-colors"
        >
          {/* Las opciones del desplegable se generan recorriendo las
              cohortes que manda la API, no se escriben a mano. */}
          {cohortes.isPending && <option value="">Cargando…</option>}
          {lista.map((c) => (
            <option key={c.id} value={c.id}>
              {c.nombre}
            </option>
          ))}
        </select>

        {cohorte && (
          <PeriodoToggle
            abierto={cohorte.inscripcionAbierta}
            onToggle={alternarPeriodo}
            deshabilitado={periodo.isPending}
          />
        )}
      </Topbar>

      <CerrarInscripcion
        abierto={confirmandoCierre}
        cohorte={cohorte?.nombre ?? ''}
        enviando={periodo.isPending}
        error={periodo.error}
        onCerrar={() => setConfirmandoCierre(false)}
        onConfirmar={cerrarPeriodo}
      />

      <div className="p-5">
        {/* Si algo falla, el mensaje del back arriba de todo. El error
            al cerrar el período se ve adentro del modal. */}
        {cohortes.error && (
          <Alerta variant="danger" className="mb-4">
            No se pudieron cargar las cohortes. {cohortes.error.message}
          </Alerta>
        )}
        {periodo.error && !confirmandoCierre && (
          <Alerta variant="danger" className="mb-4">
            No se pudo abrir la inscripción. {periodo.error.message}
          </Alerta>
        )}
        {resumen.error && (
          <Alerta variant="danger" className="mb-4">
            No se pudo cargar el resumen. {resumen.error.message}
          </Alerta>
        )}

        {/* Indicadores: las 4 tarjetas de arriba. Reciben el número
            que contó el back; StatCard solo se ocupa de mostrarlo.
            Mientras no llega el resumen, muestran un guion. */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <StatCard label="Total inscriptos" valor={r ? r.total : '–'} sub={cohorte?.nombre} />
          <StatCard
            label="Para revisar"
            valor={r ? cuantos('PENDIENTE', 'EN_REVISION') : '–'}
            sub="Pendientes y en revisión"
          />
          <StatCard
            label="Aprobados"
            valor={r ? cuantos('COMPLETADO', 'ACTIVO') : '–'}
            sub="Completados y matriculados"
          />
          <StatCard
            label="Con beca"
            valor={r ? r.conBeca : '–'}
            sub={r ? `30% → ${r.beca30} · 100% → ${r.beca100}` : undefined}
          />
        </div>

        {/* Tabla de inscriptos */}
        <Card>
          <div className="flex items-center justify-between gap-3 flex-wrap mb-3.5">
            <div className="flex items-center gap-1.5 text-[13px] font-medium text-ink">
              <IconUsers size={15} stroke={1.5} />
              Inscriptos — {cohorte?.nombre}
            </div>
            <Button
              onClick={() => filtros && exportar.mutate(filtros)}
              disabled={!filtros || exportar.isPending}
              className="disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <IconDownload size={15} stroke={1.5} />
              {exportar.isPending ? 'Exportando…' : 'Exportar'}
            </Button>
          </div>

          {/* Búsqueda y filtros en la misma barra: se combinan entre sí
              y con la cohorte de arriba. En el celular, uno abajo del otro. */}
          <div className="flex flex-col sm:flex-row sm:flex-wrap sm:items-start gap-2 mb-3.5">
            <div className="w-full sm:w-[220px]">
              <div className="relative">
                <IconSearch
                  size={14}
                  stroke={1.5}
                  className="absolute left-2.5 top-1/2 -translate-y-1/2 text-faint"
                />
                <input
                  type="search"
                  aria-label="Buscar por DNI o apellido"
                  aria-describedby={aviso ? 'aviso-busqueda' : undefined}
                  value={busqueda}
                  onChange={(e) => filtrar(() => setBusqueda(e.target.value))}
                  placeholder="DNI o apellido"
                  className={control + ' sm:w-full pl-8 placeholder:text-faint'}
                />
              </div>
              {aviso && (
                <p id="aviso-busqueda" className="text-[11px] text-muted mt-1">
                  {aviso}
                </p>
              )}
            </div>

            <select
              aria-label="Estado"
              value={estado}
              onChange={(e) =>
                filtrar(() => setEstado(e.target.value as FiltrosLegajos['estado']))
              }
              className={control}
            >
              <option value="">Todos los estados</option>
              {ESTADOS.map((e) => (
                <option key={e} value={e}>
                  {ETIQUETA_ESTADO[e]}
                </option>
              ))}
            </select>

            <select
              aria-label="Carrera"
              value={carrera}
              onChange={(e) => filtrar(() => setCarrera(e.target.value))}
              className={control}
            >
              <option value="">Todas las carreras</option>
              {carreras.data?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nombre}
                </option>
              ))}
            </select>

            <select
              aria-label="Beca"
              value={beca}
              onChange={(e) => filtrar(() => setBeca(e.target.value as FiltrosLegajos['beca']))}
              className={control}
            >
              <option value="">Beca: todos</option>
              <option value="true">Con beca</option>
              <option value="false">Sin beca</option>
            </select>
          </div>

          {legajos.error && (
            <Alerta variant="danger" className="mb-3.5">
              No se pudieron cargar los inscriptos. {legajos.error.message}
            </Alerta>
          )}
          {exportar.error && (
            <Alerta variant="danger" className="mb-3.5">
              No se pudo exportar. {exportar.error.message}
            </Alerta>
          )}

          {/* La tabla es más ancha que un celular: se desplaza de costado
              adentro de la tarjeta, sin mover el resto de la pantalla. */}
          <div className="overflow-x-auto">
            <table className="w-full min-w-[860px] text-[12px] border-collapse">
              <thead>
                <tr>
                  <th className={th}>Nº de legajo</th>
                  <th className={th}>Apellido y nombre</th>
                  <th className={th}>DNI</th>
                  <th className={th}>Carrera</th>
                  <th className={th}>Beca</th>
                  <th className={th}>Estado</th>
                  <th className={th}>Documentación</th>
                  <th className={th}></th>
                </tr>
              </thead>

              <tbody>
                {legajos.isPending && !legajos.error && (
                  <tr>
                    <td colSpan={8}>
                      <Cargando texto="Cargando inscriptos…" />
                    </td>
                  </tr>
                )}

                {/* Una fila por legajo de la página. `key` es un
                    identificador único que React necesita para saber
                    qué fila cambió y no redibujar la tabla entera. */}
                {filas.map((l) => {
                  const tipo: Beca = l.solicitaBeca && l.tipoBeca ? l.tipoBeca : 'sin'
                  return (
                    <tr key={l.id}>
                      <td className={td + ' whitespace-nowrap'}>
                        {/* Sin número todavía (se asigna al aprobar): el
                            código de seguimiento, para poder ubicarlo. */}
                        {l.numeroLegajo ?? (
                          <span className="text-muted font-mono" title="Código de seguimiento">
                            {l.codigoSeguimiento}
                          </span>
                        )}
                      </td>
                      <td className={td + ' font-medium'}>
                        {l.apellido}, {l.nombre}
                      </td>
                      <td className={td + ' text-muted'}>{l.dni}</td>
                      <td className={td}>{l.carreras.join(' · ')}</td>
                      <td className={td}>
                        <Badge variant={variantBeca[tipo]}>{etiquetaBeca[tipo]}</Badge>
                      </td>
                      <td className={td}>
                        <EstadoBadge estado={l.estado} />
                      </td>
                      <td className={td}>
                        <div
                          className="flex items-center gap-2"
                          title={`${l.documentosCargados} de ${l.documentosRequeridos} documentos`}
                        >
                          <BarraProgreso porcentaje={completitud(l)} />
                          <span className="text-[10px] text-faint">
                            {l.documentosCargados}/{l.documentosRequeridos}
                          </span>
                        </div>
                      </td>
                      <td className={td}>
                        <Link
                          to={`/coordinador/legajos/${l.id}`}
                          className="inline-flex items-center px-2.5 py-0.5 rounded-input border border-line-strong bg-card text-ink text-[11px] font-medium whitespace-nowrap hover:bg-surface transition-colors"
                        >
                          Ver legajo
                        </Link>
                      </td>
                    </tr>
                  )
                })}

                {/* Mensaje para cuando la búsqueda no encuentra nada:
                    una tabla vacía sin explicación confunde al usuario. */}
                {legajos.isSuccess && filas.length === 0 && (
                  <tr>
                    <td colSpan={8} className="py-6 text-center text-[12px] text-muted">
                      No se encontraron inscriptos con ese criterio.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between mt-2.5 pt-2.5 border-t border-line">
            <span className="text-[11px] text-muted">
              Mostrando {filas.length} de {total} inscriptos
            </span>
            <div className="flex gap-1">
              <Button
                className="text-[11px] px-2.5 py-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={!hayAnterior}
                onClick={() => setPagina((p) => p - 1)}
              >
                ← Ant.
              </Button>
              <Button
                className="text-[11px] px-2.5 py-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={!haySiguiente}
                onClick={() => setPagina((p) => p + 1)}
              >
                Sig. →
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </>
  )
}
