/* ═══════════════════════════════════════════════════════════════
   AvisoEstado.tsx — QUÉ LE TOCA HACER AL ASPIRANTE AHORA
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   El EstadoBadge del Topbar dice EN QUÉ estado está el legajo;
   este aviso dice QUÉ HACER con eso, en palabras del aspirante.
   Es una <Alerta> con el color del momento:
     info    → Borrador, Pendiente, En revisión (va bien, espera)
     warn    → Observado (tiene que corregir algo)
     success → Completado, Activo, Graduado
     danger  → Rechazado, Vencido, Baja

   El Record<EstadoLegajo, ...> de abajo obliga a cubrir los 10
   estados: si el back suma uno y no lo agregamos, no compila.

   El comentario del coordinador (ultimaObservacion) lo escribió
   una persona: React lo escapa solo, nunca se inserta como HTML.
   ═══════════════════════════════════════════════════════════════ */

import type { ReactNode } from 'react'
import Alerta from '../../shared/components/Alerta'
import type { EstadoLegajo, LegajoDetalle, Variante } from '../../shared/api/tipos'
import { fechaLimiteMatricula, plazoMatriculaVencido } from '../fechas'

type Aviso = { variante: Variante; titulo: string; texto: (legajo: LegajoDetalle) => ReactNode }

const EN_REVISION: Aviso = {
  variante: 'info',
  titulo: 'Recibimos tu preinscripción',
  texto: () => 'La Secretaría la está revisando. Te avisamos por email cuando haya novedades.',
}

const AVISOS: Record<EstadoLegajo, Aviso> = {
  BORRADOR: {
    variante: 'info',
    titulo: 'Tu preinscripción está guardada',
    texto: () => 'Subí tus documentos y enviá a revisión.',
  },
  PENDIENTE: EN_REVISION,
  EN_REVISION: EN_REVISION,
  OBSERVADO: {
    variante: 'warn',
    titulo: 'Tu legajo tiene observaciones',
    texto: (legajo) => (
      <>
        {legajo.ultimaObservacion && (
          <blockquote className="my-1.5 pl-2.5 border-l-2 border-warn-border whitespace-pre-line">
            {legajo.ultimaObservacion}
          </blockquote>
        )}
        Corregí lo que te pedimos y volvé a enviar.
      </>
    ),
  },
  COMPLETADO: {
    variante: 'success',
    titulo: '¡Aprobado!',
    texto: (legajo) => (
      <>
        Tu número de legajo es <strong>{legajo.numeroLegajo}</strong>.
        {legajo.fechaAprobacion &&
          (plazoMatriculaVencido(legajo.fechaAprobacion) ? (
            <>
              {' '}
              El plazo para matricularte venció el{' '}
              <strong>{fechaLimiteMatricula(legajo.fechaAprobacion)}</strong>. Escribile a la
              Secretaría de Posgrado para saber si todavía podés hacerlo.
            </>
          ) : (
            <>
              {' '}
              Tenés hasta el <strong>{fechaLimiteMatricula(legajo.fechaAprobacion)}</strong> para
              matricularte; después se libera la vacante.
            </>
          ))}
      </>
    ),
  },
  ACTIVO: {
    variante: 'success',
    titulo: 'Ya sos estudiante',
    texto: (legajo) => (
      <>
        Tu matrícula está confirmada. Tu número de legajo es{' '}
        <strong>{legajo.numeroLegajo}</strong>.
      </>
    ),
  },
  GRADUADO: {
    variante: 'success',
    titulo: 'Ya te graduaste',
    texto: () => '¡Felicitaciones! Completaste la carrera.',
  },
  RECHAZADO: {
    variante: 'danger',
    titulo: 'Tu preinscripción no fue aceptada',
    texto: () =>
      'Te mandamos un email con el resultado. Si tenés dudas, escribile a la Secretaría de Posgrado.',
  },
  VENCIDO: {
    variante: 'danger',
    titulo: 'Venció el plazo para matricularte',
    texto: () =>
      'Pasaron 30 días desde la aprobación y se liberó la vacante. Si querés seguir, escribile a la Secretaría de Posgrado.',
  },
  BAJA: {
    variante: 'danger',
    titulo: 'Tu legajo está dado de baja',
    texto: () => 'Si creés que es un error, escribile a la Secretaría de Posgrado.',
  },
}

export default function AvisoEstado({ legajo }: { legajo: LegajoDetalle }) {
  const { variante, titulo, texto } = AVISOS[legajo.estado]
  return (
    <Alerta variant={variante} className="mb-4">
      <p className="font-medium">{titulo}</p>
      <div className="mt-0.5">{texto(legajo)}</div>
    </Alerta>
  )
}
