/* ═══════════════════════════════════════════════════════════════
   DatosLegajo.tsx — LO QUE CARGÓ EL ASPIRANTE
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Dos tarjetas de solo lectura: datos personales y de contacto, y
   lo académico (carreras, cohorte, títulos y beca). El coordinador
   no edita nada acá: si falta o está mal algo, observa el legajo y
   lo corrige el aspirante desde su link.

   Cada dato es un par etiqueta/valor dentro de un <dl> (lista de
   definiciones): es el elemento de HTML pensado para eso, y un
   lector de pantalla lo lee como "Etiqueta: valor".
   ═══════════════════════════════════════════════════════════════ */

import type { ReactNode } from 'react'
import { IconSchool, IconUser } from '@tabler/icons-react'
import Card from '../../shared/components/Card'
import type { LegajoDetalle } from '../../shared/api/tipos'
import { OPCIONES_COMO_CONOCIO } from '../../inscripcion/types'
import { fecha } from '../formato'

function Dato({ etiqueta, children }: { etiqueta: string; children: ReactNode }) {
  return (
    <div className="min-w-0">
      <dt className="text-[11px] text-muted">{etiqueta}</dt>
      <dd className="text-[12.5px] text-ink break-words">{children || '—'}</dd>
    </div>
  )
}

const grilla = 'grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3'

export default function DatosLegajo({ legajo }: { legajo: LegajoDetalle }) {
  const comoConocio = OPCIONES_COMO_CONOCIO.find((o) => o.valor === legajo.comoConocio)
  const beca = legajo.solicitaBeca ? `Sí, ${legajo.tipoBeca}%` : 'No'

  return (
    <>
      <Card title="Datos personales y contacto" icon={IconUser}>
        <dl className={grilla}>
          <Dato etiqueta="Apellido y nombre">
            {legajo.apellido}, {legajo.nombre}
          </Dato>
          <Dato etiqueta="DNI">{legajo.dni}</Dato>
          <Dato etiqueta="Nacionalidad">{legajo.nacionalidad}</Dato>
          <Dato etiqueta="Email">{legajo.email}</Dato>
          <Dato etiqueta="Email alternativo">{legajo.emailAlternativo}</Dato>
          <Dato etiqueta="Teléfono móvil">{legajo.telefonoMovil}</Dato>
          <Dato etiqueta="Teléfono fijo">{legajo.telefonoFijo}</Dato>
          <Dato etiqueta="Domicilio">
            {legajo.domicilio}, {legajo.ciudad}, {legajo.provincia}, {legajo.pais}
          </Dato>
        </dl>
      </Card>

      <Card title="Carreras, cohorte y beca" icon={IconSchool}>
        <dl className={grilla}>
          <Dato etiqueta={legajo.carreras.length > 1 ? 'Carreras' : 'Carrera'}>
            {/* En el orden en que las eligió: la primera es la principal. */}
            {legajo.carreras.map((c) => c.nombre).join(' · ')}
          </Dato>
          <Dato etiqueta="Cohorte">{legajo.cohorte.nombre}</Dato>
          <Dato etiqueta="Título de grado">{legajo.tituloGrado}</Dato>
          <Dato etiqueta="Título de posgrado">{legajo.tituloPosgrado}</Dato>
          <Dato etiqueta="Solicita beca">{beca}</Dato>
          <Dato etiqueta="Cómo conoció el posgrado">{comoConocio?.etiqueta}</Dato>
          <Dato etiqueta="Inscripción">
            {legajo.fechaInscripcion ? fecha(legajo.fechaInscripcion) : 'Todavía no la envió'}
          </Dato>
          {legajo.fechaAprobacion && (
            <Dato etiqueta="Aprobación">{fecha(legajo.fechaAprobacion)}</Dato>
          )}
          {legajo.fechaActivacion && (
            <Dato etiqueta="Matrícula">{fecha(legajo.fechaActivacion)}</Dato>
          )}
        </dl>
        <div className="mt-3">
          <div className="text-[11px] text-muted">Motivación</div>
          <p className="text-[12.5px] text-ink whitespace-pre-line mt-0.5">{legajo.motivacion}</p>
        </div>
      </Card>
    </>
  )
}
