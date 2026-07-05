import { useState } from 'react'
import {
  IconClipboardList,
  IconSchool,
  IconUser,
  IconMapPin,
  IconCertificate,
  IconFileText,
  IconAward,
  IconSend,
  IconDeviceFloppy,
} from '@tabler/icons-react'
import Topbar from '../../shared/layout/Topbar'
import Card from '../../shared/components/Card'
import Badge from '../../shared/components/Badge'
import Button from '../../shared/components/Button'
import Field from '../../shared/components/Field'
import UploadBox from '../../shared/components/UploadBox'
import { controlClass } from '../../shared/components/controls'

export default function FormularioInscripcion() {
  const [solicitaBeca, setSolicitaBeca] = useState(false)

  return (
    <>
      <Topbar title="Formulario de preinscripción" icon={IconClipboardList}>
        <Badge variant="info">Período abierto</Badge>
      </Topbar>

      <div className="p-5">
        {/* Carrera */}
        <Card title="Carrera" icon={IconSchool}>
          <Field label="Carrera/s a inscribirse" required className="max-w-md">
            <select className={controlClass} defaultValue="">
              <option value="" disabled>
                — Seleccionar carrera —
              </option>
              <option>Especialización en Ingeniería en Sistemas</option>
              <option>Maestría en Ingeniería en Sistemas</option>
              <option>Doctorado en Ingeniería</option>
            </select>
          </Field>
        </Card>

        {/* Datos personales */}
        <Card title="Datos personales" icon={IconUser}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Field label="Apellido" required>
              <input className={controlClass} />
            </Field>
            <Field label="Nombre" required>
              <input className={controlClass} />
            </Field>
            <Field label="Nacionalidad" required>
              <input className={controlClass} />
            </Field>
            <Field label="DNI o Pasaporte" required>
              <input className={controlClass} placeholder="Ej: 30456789" />
            </Field>
            <Field label="Teléfono móvil" required>
              <input className={controlClass} />
            </Field>
            <Field label="Teléfono fijo">
              <input className={controlClass} />
            </Field>
            <Field label="Correo electrónico" required>
              <input type="email" className={controlClass} />
            </Field>
            <Field label="Correo alternativo">
              <input type="email" className={controlClass} />
            </Field>
          </div>
        </Card>

        {/* Domicilio */}
        <Card title="Domicilio" icon={IconMapPin}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Field label="Domicilio" required className="sm:col-span-2">
              <input className={controlClass} />
            </Field>
            <Field label="Ciudad" required>
              <input className={controlClass} />
            </Field>
            <Field label="Provincia" required>
              <input className={controlClass} />
            </Field>
            <Field label="País" required>
              <input className={controlClass} />
            </Field>
          </div>
        </Card>

        {/* Formación y motivación */}
        <Card title="Formación y motivación" icon={IconCertificate}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Field label="Título de grado" required>
              <input className={controlClass} />
            </Field>
            <Field label="Título de posgrado">
              <input className={controlClass} />
            </Field>
            <Field label="¿Cómo conoció la oferta?" required className="sm:col-span-2">
              <select className={controlClass} defaultValue="">
                <option value="" disabled>
                  — Seleccionar —
                </option>
                <option>Sitio web UTN FRLP</option>
                <option>Otros sitios web</option>
                <option>Egresados de la UTN FRLP</option>
                <option>Comentarios de colegas</option>
                <option>Otros</option>
              </select>
            </Field>
            <Field
              label="Motivaciones para realizar la/s carrera/s"
              required
              className="sm:col-span-2"
            >
              <textarea className={controlClass} rows={4} placeholder="Mínimo 50 caracteres" />
            </Field>
          </div>
        </Card>

        {/* Documentación */}
        <Card title="Documentación (PDF)" icon={IconFileText}>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <UploadBox label="Formulario de preinscripción firmado" />
            <UploadBox label="Copia del DNI" />
            <UploadBox label="Partida de nacimiento" />
            <UploadBox label="Constancia de CUIT / CUIL" />
            <UploadBox label="Copia del título de grado" />
            <UploadBox label="Copia del título de posgrado" optional />
          </div>
        </Card>

        {/* Beca */}
        <Card title="Beca" icon={IconAward}>
          <label className="flex items-center gap-2 text-[13px] text-ink cursor-pointer">
            <input
              type="checkbox"
              checked={solicitaBeca}
              onChange={(e) => setSolicitaBeca(e.target.checked)}
            />
            Solicito beca
          </label>

          {solicitaBeca && (
            <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field label="Porcentaje de beca" required>
                <div className="flex gap-4 text-[13px] text-ink pt-1">
                  <label className="flex items-center gap-1.5">
                    <input type="radio" name="beca" /> 30%
                  </label>
                  <label className="flex items-center gap-1.5">
                    <input type="radio" name="beca" /> 100%
                  </label>
                </div>
              </Field>
              <UploadBox label="Formulario de beca firmado" />
            </div>
          )}
        </Card>

        {/* Acciones */}
        <div className="flex justify-end gap-2 pb-2">
          <Button>
            <IconDeviceFloppy size={15} stroke={1.5} /> Guardar borrador
          </Button>
          <Button variant="primary">
            <IconSend size={15} stroke={1.5} /> Enviar inscripción
          </Button>
        </div>
      </div>
    </>
  )
}