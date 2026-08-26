/* ═══════════════════════════════════════════════════════════════
   PlanillaDocente.tsx — PANTALLA DEL DOCENTE
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Reemplaza la planilla de Excel/papel donde el docente toma
   asistencia y carga las notas de un seminario. Es la pantalla
   MÁS INTERACTIVA del prototipo: conviene demostrarla en vivo.

   DEMO SUGERIDA (hacerlo mientras se explica):
     Hacer click en una celda de asistencia → cambia de vacío a
     "P" (presente), otro click a "A" (ausente), otro vuelve a
     vacío. En el mismo momento se actualizan solos el porcentaje
     de asistencia y el estado del alumno (Libre / Regular /
     Aprobado). Nadie lo recalcula a mano: lo hace el sistema.

   LAS REGLAS DE NEGOCIO QUE PROGRAMAMOS:
     · Si no llega a la asistencia mínima (75%) → LIBRE, sin
       importar la nota que tenga.
     · Si llega a la asistencia y tiene 6 o más → APROBADO.
     · Si llega a la asistencia pero no tiene nota → REGULAR.
   Están en la función calcularEstado(), un solo lugar. Si el
   reglamento cambia, se toca ahí y listo.

   CÓMO FUNCIONA POR DENTRO:
   Toda la grilla vive en UN estado (`estudiantes`). Cuando se
   toca una celda no modificamos el dato original: creamos una
   copia con el cambio (INMUTABILIDAD). React compara y vuelve a
   dibujar solo lo que cambió. Es la forma correcta de trabajar
   en React y evita errores muy difíciles de encontrar.

   Arriba también hay un aviso de que el sistema manda recordatorio
   automático por mail si el docente no carga a tiempo.
   ═══════════════════════════════════════════════════════════════ */

import { useState } from 'react'
import {
  IconTable,
  IconDownload,
  IconMail,
  IconInfoCircle,
  IconCalendar,
  IconUsers,
  IconPlus,
  IconDeviceFloppy,
} from '@tabler/icons-react'
import Topbar from '../../shared/layout/Topbar'
import Card from '../../shared/components/Card'
import Badge from '../../shared/components/Badge'
import Button from '../../shared/components/Button'
import CeldaAsistencia from '../components/CeldaAsistencia'
import BarraAsistencia from '../components/BarraAsistencia'
import type { Asistencia, EstudiantePlanilla } from '../types'
import {
  estudiantesMock,
  fechasGrilla,
  fechasRegistradas,
  seminarioMock,
} from '../data/planillaMock'

/* ── Cálculos derivados ───────────────────────────────────────
   Estas funciones NO guardan nada: reciben datos y devuelven el
   resultado. Por eso el porcentaje y el estado se actualizan solos
   cada vez que cambia una celda.
   ─────────────────────────────────────────────────────────── */

/** Cuenta cuántas "P" hay sobre el total de clases y lo pasa a %. */
function calcularPorcentaje(asistencias: Asistencia[]): number {
  const total = asistencias.length
  if (total === 0) return 0
  const presentes = asistencias.filter((a) => a === 'P').length
  return Math.round((presentes / total) * 100)
}

type EstadoInfo = {
  label: string
  variant: 'info' | 'success' | 'warn' | 'danger'
}

/** LAS REGLAS DEL REGLAMENTO, en un solo lugar.
    Se lee de arriba hacia abajo: la primera condición que se cumple
    define el estado del estudiante. */
function calcularEstado(porcentaje: number, nota: string): EstadoInfo {
  // Sin la asistencia mínima, queda libre sin importar la nota.
  if (porcentaje < seminarioMock.asistenciaMinima) {
    return { label: 'Libre', variant: 'danger' }
  }
  const valor = Number(nota)
  if (nota.trim() !== '' && !Number.isNaN(valor) && valor >= 6) {
    return { label: 'Aprobado', variant: 'success' }
  }
  return { label: 'Regular', variant: 'info' }
}

/* ── Pantalla ─────────────────────────────────────────────── */

export default function PlanillaDocente() {
  // TODA la grilla vive en este único estado.
  const [estudiantes, setEstudiantes] =
    useState<EstudiantePlanilla[]>(estudiantesMock)

  // Cambia una celda: reemplaza al estudiante por una copia con la
  // asistencia nueva. Nunca modificamos el original directamente.
  function cambiarAsistencia(
    id: string,
    indiceFecha: number,
    nuevo: Asistencia,
  ) {
    setEstudiantes((previos) =>
      previos.map((e) => {
        if (e.id !== id) return e
        const asistencias = [...e.asistencias]
        asistencias[indiceFecha] = nuevo
        return { ...e, asistencias }
      }),
    )
  }

  function cambiarNota(id: string, nota: string) {
    setEstudiantes((previos) =>
      previos.map((e) => (e.id === id ? { ...e, nota } : e)),
    )
  }

  const th =
    'text-left font-medium text-muted py-2 px-2 border-b border-line whitespace-nowrap'
  const thCenter = th + ' text-center'
  const td = 'py-2 px-2 border-b border-line'

  return (
    <>
      <Topbar
        title={`Planilla docente · ${seminarioMock.nombre}`}
        icon={IconTable}
      >
        <Button>
          <IconDownload size={15} stroke={1.5} /> Descargar planilla
        </Button>
      </Topbar>

      <div className="p-5">
        {/* Recordatorio de la fecha límite de carga. En el sistema
            final esto además dispara un mail automático al docente. */}
        <div className="flex items-start gap-2 p-3 mb-4 rounded-card border border-warn-border bg-warn-bg text-[12.5px] text-warn">
          <IconMail size={15} stroke={1.5} className="flex-shrink-0 mt-0.5" />
          <span>
            Si no completa la carga antes del <strong>30/06/2026</strong>{' '}
            recibirá un recordatorio automático por correo electrónico.
          </span>
        </div>

        {/* Dos columnas: datos del seminario + fechas */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card title="Datos del seminario" icon={IconInfoCircle}>
            <table className="w-full text-[12px]">
              <tbody>
                <FilaDato label="Seminario" valor={seminarioMock.nombre} />
                <FilaDato label="Docente" valor={seminarioMock.docente} />
                <FilaDato label="Carrera" valor={seminarioMock.carrera} />
                <FilaDato label="Cohorte" valor={seminarioMock.cohorte} />
                <FilaDato
                  label="Asistencia mínima"
                  valor={`${seminarioMock.asistenciaMinima}%`}
                  destacado
                />
              </tbody>
            </table>
          </Card>

          <Card title="Fechas de cursada registradas" icon={IconCalendar}>
            <div className="flex gap-1.5 flex-wrap items-center">
              {fechasRegistradas.map((f) => (
                <Badge key={f.fecha} variant={f.dictada ? 'success' : 'warn'}>
                  {f.fecha}
                </Badge>
              ))}
              <Button className="text-[11px] px-2 py-0.5">
                <IconPlus size={13} stroke={1.5} /> Nueva fecha
              </Button>
            </div>
          </Card>
        </div>

        {/* LA GRILLA: filas = estudiantes, columnas = fechas de
            cursada. Es el corazón de esta pantalla. */}
        <Card title="Registro de asistencia y calificaciones" icon={IconUsers}>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[680px] text-[12px] border-collapse">
              <thead>
                <tr>
                  <th className={th + ' min-w-[140px]'}>Estudiante</th>
                  <th className={th}>Email</th>
                  <th className={th}>Carrera grado</th>
                  {/* Las columnas de fechas se generan desde los datos:
                      si el docente agrega una fecha nueva, aparece una
                      columna nueva sin tocar el código. */}
                  {fechasGrilla.map((f) => (
                    <th key={f} className={thCenter}>
                      {f}
                    </th>
                  ))}
                  <th className={thCenter}>Asistencia</th>
                  <th className={thCenter}>Nota final</th>
                  <th className={thCenter}>Estado</th>
                </tr>
              </thead>

              <tbody>
                {estudiantes.map((e) => {
                  // Se recalculan en cada render, a partir del estado.
                  const porcentaje = calcularPorcentaje(e.asistencias)
                  const estado = calcularEstado(porcentaje, e.nota)

                  return (
                    <tr key={e.id}>
                      <td className={td + ' font-medium text-ink'}>
                        {e.nombre}
                      </td>
                      <td className={td + ' text-[11px] text-muted'}>
                        {e.email}
                      </td>
                      <td className={td + ' text-[11px] text-muted'}>
                        {e.carreraGrado}
                      </td>

                      {/* Una celda clickeable por fecha. Le pasamos el
                          valor actual y qué hacer cuando cambie. */}
                      {e.asistencias.map((valor, indice) => (
                        <td key={indice} className={td + ' text-center'}>
                          <CeldaAsistencia
                            valor={valor}
                            onChange={(nuevo) =>
                              cambiarAsistencia(e.id, indice, nuevo)
                            }
                          />
                        </td>
                      ))}

                      <td className={td}>
                        <BarraAsistencia porcentaje={porcentaje} />
                      </td>

                      <td className={td + ' text-center'}>
                        <input
                          value={e.nota}
                          onChange={(ev) => cambiarNota(e.id, ev.target.value)}
                          placeholder="—"
                          className="w-10 text-center py-1 rounded border border-line-strong bg-surface text-ink text-[12px] placeholder:text-faint focus:outline-none focus:border-primary transition-colors"
                        />
                      </td>

                      <td className={td + ' text-center'}>
                        <Badge variant={estado.variant}>{estado.label}</Badge>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          <div className="flex justify-end mt-3">
            <Button variant="primary">
              <IconDeviceFloppy size={15} stroke={1.5} /> Guardar cambios
            </Button>
          </div>
        </Card>
      </div>
    </>
  )
}

// Fila de la tabla de datos del seminario (etiqueta + valor).
function FilaDato({
  label,
  valor,
  destacado,
}: {
  label: string
  valor: string
  destacado?: boolean
}) {
  return (
    <tr>
      <td className="text-muted text-[11px] py-1 w-2/5">{label}</td>
      <td className={'py-1 ' + (destacado ? 'font-medium text-ink' : 'text-ink')}>
        {valor}
      </td>
    </tr>
  )
}