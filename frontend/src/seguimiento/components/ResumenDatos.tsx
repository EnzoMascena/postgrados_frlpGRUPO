/* ═══════════════════════════════════════════════════════════════
   ResumenDatos.tsx — LO QUE EL ASPIRANTE CARGÓ (solo lectura)
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Muestra los datos del legajo tal como los guardó el back, para
   que el aspirante los revise antes de enviar. No se edita acá:
   "Editar mis datos" (G4) abre el mismo FormularioDatos de la
   inscripción.

   Va con <dl> (lista de definiciones): cada <dt> es la etiqueta
   y su <dd> el valor. Así un lector de pantalla lee "DNI,
   28456789" y no dos textos sueltos. Las filas imitan las de
   "Datos del estudiante" del wireframe.

   Los opcionales vacíos (teléfono fijo, título de posgrado) se
   muestran como "—", para que se vea que no hay nada y no que
   falta cargar la pantalla.
   ═══════════════════════════════════════════════════════════════ */

import { IconAddressBook, IconSchool } from '@tabler/icons-react'
import Card from '../../shared/components/Card'
import type { LegajoDetalle } from '../../shared/api/tipos'
import { OPCIONES_COMO_CONOCIO } from '../../inscripcion/types'

const SIN_DATO = '—'

function Fila({ etiqueta, valor }: { etiqueta: string; valor: string | null }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-[2fr_3fr] gap-x-3 gap-y-0.5 py-1.5 border-b border-line last:border-b-0">
      <dt className="text-[11px] text-muted">{etiqueta}</dt>
      <dd className="text-[12px] text-ink break-words whitespace-pre-line">
        {valor?.trim() ? valor : SIN_DATO}
      </dd>
    </div>
  )
}

function textoBeca(legajo: LegajoDetalle): string {
  if (!legajo.solicitaBeca) return 'No'
  return legajo.tipoBeca ? `Sí, del ${legajo.tipoBeca}%` : 'Sí'
}

function textoComoConocio(legajo: LegajoDetalle): string {
  return (
    OPCIONES_COMO_CONOCIO.find((opcion) => opcion.valor === legajo.comoConocio)?.etiqueta ??
    legajo.comoConocio
  )
}

export default function ResumenDatos({ legajo }: { legajo: LegajoDetalle }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-4 items-start">
      <Card title="Carreras y cohorte" icon={IconSchool}>
        <dl>
          <Fila etiqueta="Cohorte" valor={legajo.cohorte.nombre} />
          {legajo.carreras.map((carrera, i) => (
            <Fila
              key={carrera.id}
              etiqueta={legajo.carreras.length > 1 ? `Carrera ${i + 1}` : 'Carrera'}
              valor={carrera.nombre}
            />
          ))}
          <Fila etiqueta="Solicita beca" valor={textoBeca(legajo)} />
          <Fila etiqueta="Título de grado" valor={legajo.tituloGrado} />
          <Fila etiqueta="Título de posgrado" valor={legajo.tituloPosgrado} />
          <Fila etiqueta="Cómo nos conociste" valor={textoComoConocio(legajo)} />
          <Fila etiqueta="Motivación" valor={legajo.motivacion} />
        </dl>
      </Card>

      <Card title="Datos personales" icon={IconAddressBook}>
        <dl>
          <Fila etiqueta="Apellido y nombre" valor={`${legajo.apellido}, ${legajo.nombre}`} />
          <Fila etiqueta="DNI" valor={legajo.dni} />
          <Fila etiqueta="Nacionalidad" valor={legajo.nacionalidad} />
          <Fila etiqueta="Email" valor={legajo.email} />
          {/* El tipo dice string, pero el back hoy lo acepta como null. */}
          <Fila etiqueta="Email alternativo" valor={legajo.emailAlternativo ?? null} />
          <Fila etiqueta="Teléfono móvil" valor={legajo.telefonoMovil} />
          <Fila etiqueta="Teléfono fijo" valor={legajo.telefonoFijo} />
          <Fila
            etiqueta="Domicilio"
            valor={`${legajo.domicilio}, ${legajo.ciudad}, ${legajo.provincia}, ${legajo.pais}`}
          />
        </dl>
      </Card>
    </div>
  )
}
