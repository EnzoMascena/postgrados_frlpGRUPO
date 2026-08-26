/* ═══════════════════════════════════════════════════════════════
   Legajo.tsx — LEGAJO ACADÉMICO DEL ESTUDIANTE
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Es la ficha completa de UN estudiante: sus datos, cómo viene
   con los seminarios, en qué estado está su Trabajo Final
   Integrador (TFI) y las tutorías que tuvo. Es la pantalla que
   usa Conducción para el seguimiento individual.

   QUÉ SE VE, DE ARRIBA HACIA ABAJO:
     1. Aviso amarillo de VENCIMIENTO (solo aparece si hay un
        seminario por vencer). Este es el punto fuerte a mostrar:
        el sistema avisa solo, hoy eso se controla a mano.
     2. Datos del estudiante + SEMÁFORO de avance.
     3. Tabla de seminarios (asistencia, condición, nota, acta,
        vencimiento).
     4. Trabajo Final Integrador (editable) + tutorías.

   EL SEMÁFORO — LO MÁS DESTACABLE:
   Verde "Al día" / Amarillo "En progreso" / Rojo "En riesgo".
   El color NO se carga a mano: lo calcula la función
   nivelAvance() mirando cuántos seminarios aprobó y si tiene un
   vencimiento cerca. Es la regla del reglamento traducida a código.

   OTRA VEZ, DATOS DERIVADOS:
   Seminarios aprobados, asistencia promedio y el nivel del
   semáforo se calculan desde la lista de seminarios. No están
   guardados: si cambia un seminario, se reacomoda todo solo.

   DIVISIÓN EN COMPONENTES: el semáforo y la lista de tutorías
   están en archivos aparte (legajo/components/) para que esta
   pantalla no quede gigante y para poder reutilizarlos.
   ═══════════════════════════════════════════════════════════════ */

import { useState } from 'react'
import {
  IconUserCircle,
  IconUser,
  IconDownload,
  IconAlertTriangle,
  IconTrafficCone,
  IconBooks,
  IconFileText,
  IconMessages,
  IconDeviceFloppy,
} from '@tabler/icons-react'
import Topbar from '../../shared/layout/Topbar'
import Card from '../../shared/components/Card'
import Badge from '../../shared/components/Badge'
import Button from '../../shared/components/Button'
import Field from '../../shared/components/Field'
import StatCard from '../../shared/components/StatCard'
import BarraProgreso from '../../shared/components/Barraprogreso'
import { controlClass } from '../../shared/components/controls'
import SemaforoAvance from '../components/SemaforoAvance'
import ListaTutorias from '../components/ListaTutorias'
import type { CondicionSeminario, Seminario } from '../types'
import {
  estudianteMock,
  seminariosMock,
  trabajoFinalMock,
  tutoriasMock,
} from '../data/legajoMock'

/* ── Cálculos derivados ───────────────────────────────────────
   Igual que en las pantallas anteriores: el semáforo, los
   contadores y el promedio de asistencia se calculan desde la
   lista de seminarios. Si cambia un dato, todo se reacomoda.
   ─────────────────────────────────────────────────────────── */

/** Seminarios que cuentan para el plan (el TFI se sigue aparte). */
function seminariosDelPlan(lista: Seminario[]): Seminario[] {
  return lista.filter((s) => s.condicion !== 'en-elaboracion')
}

/** Promedio de asistencia, ignorando los seminarios que todavía no
    tienen asistencia cargada (los que valen null). */
function promedioAsistencia(lista: Seminario[]): number {
  const conAsistencia = lista.filter((s) => s.asistencia !== null)
  if (conAsistencia.length === 0) return 0
  const suma = conAsistencia.reduce((acum, s) => acum + (s.asistencia ?? 0), 0)
  return Math.round(suma / conAsistencia.length)
}

/** LA REGLA DEL SEMÁFORO:
    - Aprobó todo               → verde  (al día)
    - Le falta pero está a tiempo→ amarillo (en progreso)
    - Le falta y sin vencimiento próximo controlado → rojo (en riesgo) */
function nivelAvance(
  aprobados: number,
  total: number,
  hayVencimientoProximo: boolean,
): 'al-dia' | 'en-progreso' | 'en-riesgo' {
  if (aprobados === total) return 'al-dia'
  if (hayVencimientoProximo) return 'en-progreso'
  return 'en-riesgo'
}

const etiquetaCondicion: Record<CondicionSeminario, string> = {
  aprobado: 'Aprobado',
  cursando: 'Cursando',
  pendiente: 'Pendiente',
  'en-elaboracion': 'En elaboración',
}

const variantCondicion: Record<
  CondicionSeminario,
  'info' | 'success' | 'warn' | 'danger'
> = {
  aprobado: 'success',
  cursando: 'info',
  pendiente: 'warn',
  'en-elaboracion': 'info',
}

export default function Legajo() {
  // El formulario del TFI sí es editable, así que va en el estado.
  // El único bloque editable de la pantalla es el TFI, así que es
  // lo único que guardamos en estado. Lo demás solo se muestra.
  const [tfi, setTfi] = useState(trabajoFinalMock)

  const delPlan = seminariosDelPlan(seminariosMock)
  const aprobados = delPlan.filter((s) => s.condicion === 'aprobado').length
  const totalPlan = delPlan.length
  const asistencia = promedioAsistencia(seminariosMock)

  // .find() devuelve el primer seminario por vencer, o undefined si
  // no hay ninguno. De eso depende que aparezca el aviso amarillo.
  const proximoAVencer = seminariosMock.find((s) => s.vencimientoProximo)
  const nivel = nivelAvance(aprobados, totalPlan, Boolean(proximoAVencer))

  const hayTFI = seminariosMock.some((s) => s.condicion === 'en-elaboracion')
  const detalleAvance =
    `${aprobados} de ${totalPlan} seminarios aprobados` +
    (hayTFI ? ' · TFI en elaboración' : '')

  const th =
    'text-left font-medium text-muted py-2 px-2 border-b border-line whitespace-nowrap'
  const td = 'py-2 px-2 border-b border-line text-ink'

  return (
    <>
      <Topbar
        title={`Legajo académico · ${estudianteMock.apellidoNombre}`}
        icon={IconUserCircle}
      >
        <Button>
          <IconDownload size={15} stroke={1.5} /> Descargar legajo
        </Button>
      </Topbar>

      <div className="p-5">
        {/* AVISO AUTOMÁTICO: solo se dibuja si proximoAVencer existe.
            Mostrar esto en la exposición: es el alerta temprana que
            hoy el sistema en papel no da. */}
        {proximoAVencer && (
          <div className="flex items-start gap-2 p-3 mb-4 rounded-card border border-warn-border bg-warn-bg text-[12.5px] text-warn">
            <IconAlertTriangle
              size={15}
              stroke={1.5}
              className="flex-shrink-0 mt-0.5"
            />
            <span>
              Seminario <strong>{proximoAVencer.nombre}</strong> vence el{' '}
              <strong>{proximoAVencer.vencimiento}</strong>. Se recomienda
              revisar el estado del acta de examen.
            </span>
          </div>
        )}

        {/* Datos del estudiante + estado de avance */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card title="Datos del estudiante" icon={IconUser}>
            <table className="w-full text-[12px]">
              <tbody>
                <FilaDato label="Carrera" valor={estudianteMock.carrera} />
                <FilaDato label="Cohorte" valor={estudianteMock.cohorte} />
                <FilaDato label="DNI" valor={estudianteMock.dni} />
                <FilaDato label="Correo" valor={estudianteMock.correo} />
                <FilaDato label="Título grado" valor={estudianteMock.tituloGrado} />
                <tr>
                  <td className="text-muted text-[11px] py-1 w-2/5">
                    Estado legajo
                  </td>
                  <td className="py-1">
                    <Badge variant={estudianteMock.legajoCompleto ? 'success' : 'warn'}>
                      {estudianteMock.legajoCompleto ? 'Completo' : 'Incompleto'}
                    </Badge>
                  </td>
                </tr>
              </tbody>
            </table>
          </Card>

          <Card title="Estado de avance" icon={IconTrafficCone}>
            {/* Al componente del semáforo solo le pasamos el nivel ya
                calculado y el texto de detalle. Él se ocupa del color. */}
            <SemaforoAvance nivel={nivel} detalle={detalleAvance} />

            <div className="h-px bg-line my-4" />

            <div className="grid grid-cols-2 gap-2">
              <StatCard
                label="Seminarios aprobados"
                valor={`${aprobados} / ${totalPlan}`}
              />
              <StatCard label="Asistencia promedio" valor={`${asistencia}%`} />
            </div>
          </Card>
        </div>

        {/* Tabla de seminarios */}
        <Card title="Seminarios" icon={IconBooks}>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[700px] text-[12px] border-collapse">
              <thead>
                <tr>
                  <th className={th}>Seminario</th>
                  <th className={th}>Asistencia</th>
                  <th className={th}>Condición</th>
                  <th className={th}>Calificación final</th>
                  <th className={th}>Fecha acta</th>
                  <th className={th}>Vencimiento</th>
                </tr>
              </thead>
              <tbody>
                {/* Una fila por seminario del plan de estudios. */}
                {seminariosMock.map((s) => (
                  <tr key={s.id}>
                    <td className={td}>{s.nombre}</td>

                    <td className={td}>
                      {/* Si todavía no hay asistencia cargada mostramos
                          un guion en vez de una barra en 0%, que daría a
                          entender que el alumno no fue nunca. */}
                      {s.asistencia !== null ? (
                        <BarraProgreso porcentaje={s.asistencia} ancho={60} />
                      ) : (
                        <span className="text-faint">—</span>
                      )}
                    </td>

                    <td className={td}>
                      <Badge variant={variantCondicion[s.condicion]}>
                        {etiquetaCondicion[s.condicion]}
                      </Badge>
                    </td>

                    <td className={td + ' font-medium'}>
                      {s.calificacion ?? <span className="text-faint font-normal">—</span>}
                    </td>

                    <td className={td + ' text-muted'}>{s.fechaActa ?? '—'}</td>

                    <td
                      className={
                        td +
                        ' ' +
                        (s.vencimientoProximo
                          ? 'text-warn font-medium'
                          : 'text-muted')
                      }
                    >
                      {s.vencimiento ?? '—'}
                      {s.vencimientoProximo && ' ⚠'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* TFI + tutorías */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card title="Trabajo Final Integrador" icon={IconFileText}>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Campos controlados: el valor sale del estado (`value`)
                  y cada tecla lo actualiza (`onChange`). Así React es
                  siempre la única fuente de verdad del formulario. */}
              <Field label="Título del TFI" className="sm:col-span-2">
                <input
                  className={controlClass}
                  value={tfi.titulo}
                  onChange={(e) => setTfi({ ...tfi, titulo: e.target.value })}
                />
              </Field>
              <Field label="Director/a">
                <input
                  className={controlClass}
                  value={tfi.director}
                  onChange={(e) => setTfi({ ...tfi, director: e.target.value })}
                />
              </Field>
              <Field label="Aprobación CPR">
                <input
                  className={controlClass}
                  placeholder="Fecha pendiente"
                  value={tfi.aprobacionCPR}
                  onChange={(e) =>
                    setTfi({ ...tfi, aprobacionCPR: e.target.value })
                  }
                />
              </Field>
              <Field label="N° de resolución">
                <input
                  className={controlClass}
                  placeholder="—"
                  value={tfi.numeroResolucion}
                  onChange={(e) =>
                    setTfi({ ...tfi, numeroResolucion: e.target.value })
                  }
                />
              </Field>
            </div>

            <div className="flex justify-end mt-2.5">
              <Button variant="primary" className="text-[11px]">
                <IconDeviceFloppy size={13} stroke={1.5} /> Guardar
              </Button>
            </div>
          </Card>

          <Card title="Seguimiento de tutorías" icon={IconMessages}>
            {/* Historial de reuniones con el director/a del TFI. */}
            <ListaTutorias tutorias={tutoriasMock} />
          </Card>
        </div>
      </div>
    </>
  )
}

// Fila de la tabla de datos del estudiante (etiqueta + valor).
function FilaDato({ label, valor }: { label: string; valor: string }) {
  return (
    <tr>
      <td className="text-muted text-[11px] py-1 w-2/5">{label}</td>
      <td className="py-1 text-ink">{valor}</td>
    </tr>
  )
}