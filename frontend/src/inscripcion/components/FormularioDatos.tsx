/* ═══════════════════════════════════════════════════════════════
   FormularioDatos.tsx — LOS DATOS DEL ASPIRANTE (crear y editar)
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   En la entrega 2 los inputs eran HTML suelto: escribías y nada
   lo guardaba. Ahora es un FORMULARIO CONTROLADO: cada campo lee
   su valor del estado de React (`datos`) y cada tecla lo actualiza
   con setDatos. React es la única fuente de verdad: lo que está en
   `datos` es lo que se va a mandar a la API.

   Se usa en dos lugares (por eso es un componente aparte):
     /inscripcion          → crear el legajo   (POST /legajos)
     /seguimiento/:token   → editar los datos  (PUT /seguimiento/{token})
   La pantalla que lo usa decide qué hacer con onEnviar(datos).

   CUÁNDO SE MUESTRAN LOS ERRORES (US-CORE-001):
     1. Mientras escribís por primera vez, nada (no te reta antes
        de que termines).
     2. Al salir del campo (onBlur), se valida.
     3. De ahí en más, se revalida en cada tecla: el error se va
        apenas lo corregís.
     4. Al apretar el botón se valida todo y el foco va al primer
        campo con error.
   Los errores del back (erroresServidor) se muestran al lado de su
   campo hasta que el aspirante lo modifica.

   ACCESIBILIDAD: cada label apunta a su input (htmlFor/id), el
   input con error lleva aria-invalid y aria-describedby apuntando
   al mensaje, y los grupos de checkboxes y radios van en un
   <fieldset> con su <legend>.
   ═══════════════════════════════════════════════════════════════ */

import { useEffect, useId, useState } from 'react'
import {
  IconAward,
  IconCertificate,
  IconDeviceFloppy,
  IconMapPin,
  IconSchool,
  IconUser,
} from '@tabler/icons-react'
import Card from '../../shared/components/Card'
import Field from '../../shared/components/Field'
import Button from '../../shared/components/Button'
import Alerta from '../../shared/components/Alerta'
import Cargando from '../../shared/components/Cargando'
import { controlClass } from '../../shared/components/controls'
import { useCarreras } from '../../shared/hooks/useCatalogos'
import type { ComoConocio, TipoBeca } from '../../shared/api/tipos'
import {
  DATOS_VACIOS,
  OPCIONES_COMO_CONOCIO,
  type CampoInscripcion,
  type DatosInscripcion,
  type Errores,
} from '../types'
import { MAXIMO_CARRERAS, MOTIVACION_MINIMA, validarCampo, validarFormulario } from '../validaciones'

type Props = {
  valoresIniciales?: DatosInscripcion
  onEnviar: (datos: DatosInscripcion) => void
  enviando?: boolean
  /** Errores del back por campo. Pasá siempre el mismo objeto mientras no cambie. */
  erroresServidor?: Errores
  textoBoton: string
}

// El orden en que aparecen en pantalla: el foco va al primero con error.
const CAMPOS_EN_ORDEN: CampoInscripcion[] = [
  'carreraIds',
  'apellido',
  'nombre',
  'nacionalidad',
  'dni',
  'telefonoMovil',
  'telefonoFijo',
  'email',
  'emailAlternativo',
  'domicilio',
  'ciudad',
  'provincia',
  'pais',
  'tituloGrado',
  'tituloPosgrado',
  'comoConocio',
  'motivacion',
  'solicitaBeca',
  'tipoBeca',
]

// Los campos que son un input o textarea de texto libre.
type CampoTexto = Exclude<CampoInscripcion, 'carreraIds' | 'comoConocio' | 'solicitaBeca' | 'tipoBeca'>

const SIN_ERRORES: Errores = {}

// El mismo estilo de siempre, con el borde en rojo cuando hay error.
const controlConError = controlClass
  .replace('border-line-strong', 'border-danger')
  .replace('focus:border-primary', 'focus:border-danger')

const claseControl = (error: string | null) => (error ? controlConError : controlClass)

/**
 * Lleva el foco al primer campo con error que esté en pantalla. Si el
 * primero no existe (por ejemplo, las carreras no cargaron), sigue con
 * el próximo.
 */
function enfocarPrimerError(errores: Errores, base: string) {
  for (const campo of CAMPOS_EN_ORDEN) {
    const elemento = errores[campo] ? document.getElementById(`${base}-${campo}`) : null
    if (elemento) {
      elemento.focus()
      return
    }
  }
}

const claseLeyenda = 'text-[13px] text-muted mb-1.5'
const claseError = 'text-[12px] text-danger mt-1.5'

export default function FormularioDatos({
  valoresIniciales = DATOS_VACIOS,
  onEnviar,
  enviando = false,
  erroresServidor = SIN_ERRORES,
  textoBoton,
}: Props) {
  // useId da un prefijo único, así los id no chocan si hay dos formularios.
  const base = useId()
  const idDe = (campo: CampoInscripcion) => `${base}-${campo}`
  const idError = (campo: CampoInscripcion) => `${idDe(campo)}-error`

  const carreras = useCarreras()

  const [datos, setDatos] = useState(valoresIniciales)
  // Los campos por los que el aspirante ya pasó: solo esos muestran error.
  const [tocados, setTocados] = useState<ReadonlySet<CampoInscripcion>>(() => new Set())

  // Los errores del back, que se van borrando a medida que se corrigen.
  // Cuando llegan errores nuevos, se reemplazan (patrón de React para
  // "ajustar el estado cuando cambia una prop", sin useEffect).
  const [servidor, setServidor] = useState(erroresServidor)
  const [servidorPrevio, setServidorPrevio] = useState(erroresServidor)
  if (erroresServidor !== servidorPrevio) {
    setServidorPrevio(erroresServidor)
    setServidor(erroresServidor)
  }

  // Si el back devolvió errores, el foco va al primer campo marcado.
  useEffect(() => {
    enfocarPrimerError(erroresServidor, base)
  }, [erroresServidor, base])

  /** El error que se ve: primero el del front (si ya lo tocó), si no el del back. */
  function errorDe(campo: CampoInscripcion): string | null {
    if (tocados.has(campo)) {
      const local = validarCampo(campo, datos)
      if (local) return local
    }
    return servidor[campo] ?? null
  }

  function marcarTocado(campo: CampoInscripcion) {
    setTocados((previos) => (previos.has(campo) ? previos : new Set(previos).add(campo)))
  }

  /** Cambia uno o más campos y borra el error del back de esos campos. */
  function actualizar(cambios: Partial<DatosInscripcion>) {
    setDatos((previos) => ({ ...previos, ...cambios }))
    setServidor((previos) => {
      const quedan = { ...previos }
      for (const campo of Object.keys(cambios) as CampoInscripcion[]) delete quedan[campo]
      return quedan
    })
  }

  function alternarCarrera(id: string) {
    const ids = datos.carreraIds.includes(id)
      ? datos.carreraIds.filter((otra) => otra !== id)
      : [...datos.carreraIds, id]
    actualizar({ carreraIds: ids })
    marcarTocado('carreraIds')
  }

  function enviar() {
    const errores = validarFormulario(datos)
    setTocados(new Set(CAMPOS_EN_ORDEN))
    if (Object.keys(errores).length > 0) {
      enfocarPrimerError(errores, base)
      return
    }
    onEnviar(datos)
  }

  /** Las props comunes de un input o textarea de texto. */
  function propsTexto(campo: CampoTexto) {
    const error = errorDe(campo)
    return {
      id: idDe(campo),
      name: campo,
      value: datos[campo],
      onChange: (e: { target: { value: string } }) => actualizar({ [campo]: e.target.value }),
      onBlur: () => marcarTocado(campo),
      'aria-invalid': error ? true : undefined,
      'aria-describedby': error ? idError(campo) : undefined,
      className: claseControl(error),
    }
  }

  /** Un Field con su input de texto. */
  function campoTexto(
    campo: CampoTexto,
    label: string,
    opciones: {
      requerido?: boolean
      className?: string
      type?: string
      placeholder?: string
      autoComplete?: string
      inputMode?: 'numeric' | 'tel' | 'email'
    } = {},
  ) {
    const { requerido = true, className, ...input } = opciones
    return (
      <Field
        label={label}
        required={requerido}
        htmlFor={idDe(campo)}
        error={errorDe(campo)}
        className={className}
      >
        <input {...propsTexto(campo)} {...input} />
      </Field>
    )
  }

  const errorCarreras = errorDe('carreraIds')
  const errorBeca = errorDe('tipoBeca')
  const errorComoConocio = errorDe('comoConocio')
  const errorMotivacion = errorDe('motivacion')
  const largoMotivacion = datos.motivacion.trim().length
  const idContador = `${idDe('motivacion')}-contador`

  return (
    <form
      noValidate // los mensajes son los nuestros, no los globitos del navegador
      onSubmit={(e) => {
        e.preventDefault()
        enviar()
      }}
    >
      {/* Mientras se guarda, todos los campos quedan deshabilitados. */}
      <fieldset disabled={enviando} className="min-w-0">
        {/* Carrera: checkboxes, máximo 2 (BR-001). */}
        <Card title="Carrera" icon={IconSchool}>
          <fieldset aria-describedby={errorCarreras ? idError('carreraIds') : undefined}>
            <legend className={claseLeyenda}>
              Carrera/s a inscribirse (máximo {MAXIMO_CARRERAS}) <span className="text-danger">*</span>
            </legend>
            {carreras.isPending ? (
              <Cargando texto="Cargando carreras…" />
            ) : carreras.isError ? (
              <Alerta variant="danger">
                No pudimos cargar las carreras. Recargá la página para intentar de nuevo.
              </Alerta>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {carreras.data.map((carrera, i) => {
                  const elegida = datos.carreraIds.includes(carrera.id)
                  // Con 2 elegidas, las demás se deshabilitan.
                  const bloqueada = !elegida && datos.carreraIds.length >= MAXIMO_CARRERAS
                  return (
                    <label
                      key={carrera.id}
                      className={
                        'flex items-start gap-2 text-[13px] ' +
                        (bloqueada ? 'text-faint cursor-not-allowed' : 'text-ink cursor-pointer')
                      }
                    >
                      <input
                        type="checkbox"
                        // El primero lleva el id del campo: ahí va el foco si hay error.
                        id={i === 0 ? idDe('carreraIds') : undefined}
                        className="mt-0.5"
                        checked={elegida}
                        disabled={bloqueada}
                        aria-invalid={errorCarreras ? true : undefined}
                        onChange={() => alternarCarrera(carrera.id)}
                      />
                      {carrera.nombre}
                    </label>
                  )
                })}
              </div>
            )}
            {errorCarreras && (
              <p id={idError('carreraIds')} role="alert" className={claseError}>
                {errorCarreras}
              </p>
            )}
          </fieldset>
        </Card>

        {/* Datos personales: en celular una columna, en pantalla grande dos. */}
        <Card title="Datos personales" icon={IconUser}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {campoTexto('apellido', 'Apellido', { autoComplete: 'family-name' })}
            {campoTexto('nombre', 'Nombre', { autoComplete: 'given-name' })}
            {campoTexto('nacionalidad', 'Nacionalidad', { placeholder: 'Argentina' })}
            {campoTexto('dni', 'DNI', { placeholder: '38.500.000', inputMode: 'numeric' })}
            {campoTexto('telefonoMovil', 'Teléfono móvil', {
              type: 'tel',
              placeholder: '+54 221 …',
              autoComplete: 'tel',
            })}
            {campoTexto('telefonoFijo', 'Teléfono fijo', {
              requerido: false,
              type: 'tel',
              placeholder: '0221 …',
            })}
            {campoTexto('email', 'Correo electrónico', {
              type: 'email',
              placeholder: 'nombre@email.com',
              autoComplete: 'email',
            })}
            {campoTexto('emailAlternativo', 'Correo alternativo', {
              type: 'email',
              placeholder: 'otro@email.com',
            })}
          </div>
        </Card>

        {/* Domicilio */}
        <Card title="Domicilio" icon={IconMapPin}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {campoTexto('domicilio', 'Domicilio', {
              className: 'sm:col-span-2',
              placeholder: 'Calle 123',
              autoComplete: 'street-address',
            })}
            {campoTexto('ciudad', 'Ciudad', { placeholder: 'La Plata', autoComplete: 'address-level2' })}
            {campoTexto('provincia', 'Provincia', {
              placeholder: 'Buenos Aires',
              autoComplete: 'address-level1',
            })}
            {campoTexto('pais', 'País', { placeholder: 'Argentina', autoComplete: 'country-name' })}
          </div>
        </Card>

        {/* Formación y motivación */}
        <Card title="Formación y motivación" icon={IconCertificate}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {campoTexto('tituloGrado', 'Título de grado', { placeholder: 'Ing. en Sistemas' })}
            {campoTexto('tituloPosgrado', 'Título de posgrado', { requerido: false })}

            <Field
              label="¿Cómo conoció la oferta?"
              required
              htmlFor={idDe('comoConocio')}
              error={errorComoConocio}
              className="sm:col-span-2"
            >
              <select
                id={idDe('comoConocio')}
                name="comoConocio"
                className={claseControl(errorComoConocio)}
                value={datos.comoConocio}
                aria-invalid={errorComoConocio ? true : undefined}
                aria-describedby={errorComoConocio ? idError('comoConocio') : undefined}
                onChange={(e) => {
                  actualizar({ comoConocio: e.target.value as ComoConocio })
                  marcarTocado('comoConocio')
                }}
                onBlur={() => marcarTocado('comoConocio')}
              >
                <option value="" disabled>
                  — Seleccionar —
                </option>
                {OPCIONES_COMO_CONOCIO.map(({ valor, etiqueta }) => (
                  <option key={valor} value={valor}>
                    {etiqueta}
                  </option>
                ))}
              </select>
            </Field>

            <Field
              label="Motivaciones para realizar la/s carrera/s"
              required
              htmlFor={idDe('motivacion')}
              error={errorMotivacion}
              className="sm:col-span-2"
            >
              <textarea
                {...propsTexto('motivacion')}
                // Apunta al error (si hay) y al contador.
                aria-describedby={[errorMotivacion && idError('motivacion'), idContador]
                  .filter(Boolean)
                  .join(' ')}
                rows={4}
                placeholder="Describí brevemente tus motivaciones…"
              />
              <p id={idContador} className="text-[12px] text-muted">
                {largoMotivacion >= MOTIVACION_MINIMA
                  ? `${largoMotivacion} caracteres ✓`
                  : `${largoMotivacion} de ${MOTIVACION_MINIMA} caracteres mínimos`}
              </p>
            </Field>
          </div>
        </Card>

        {/* Beca: opcional. Si la pide, elige 30% o 100%. */}
        <Card title="Beca" icon={IconAward}>
          <label className="flex items-center gap-2 text-[13px] text-ink cursor-pointer">
            <input
              type="checkbox"
              id={idDe('solicitaBeca')}
              checked={datos.solicitaBeca}
              onChange={(e) => {
                const pide = e.target.checked
                // Si deja de pedirla, el tipo vuelve a null (lo pide el contrato).
                actualizar({ solicitaBeca: pide, tipoBeca: pide ? datos.tipoBeca : null })
              }}
            />
            Solicito beca
          </label>

          {datos.solicitaBeca && (
            <div className="mt-4 flex flex-col gap-3">
              <fieldset aria-describedby={errorBeca ? idError('tipoBeca') : undefined}>
                <legend className={claseLeyenda}>
                  Porcentaje de beca <span className="text-danger">*</span>
                </legend>
                <div className="flex gap-4 text-[13px] text-ink">
                  {(['30', '100'] as TipoBeca[]).map((tipo, i) => (
                    <label key={tipo} className="flex items-center gap-1.5 cursor-pointer">
                      <input
                        type="radio"
                        name={`${base}-tipoBeca`}
                        id={i === 0 ? idDe('tipoBeca') : undefined}
                        value={tipo}
                        checked={datos.tipoBeca === tipo}
                        aria-invalid={errorBeca ? true : undefined}
                        onChange={() => {
                          actualizar({ tipoBeca: tipo })
                          marcarTocado('tipoBeca')
                        }}
                      />
                      {tipo}%
                    </label>
                  ))}
                </div>
                {errorBeca && (
                  <p id={idError('tipoBeca')} role="alert" className={claseError}>
                    {errorBeca}
                  </p>
                )}
              </fieldset>
              <p className="text-[12px] text-muted">
                El formulario de beca firmado lo subís en el paso siguiente, junto con el resto de
                la documentación.
              </p>
            </div>
          )}
        </Card>

        <div className="flex justify-end pb-2">
          <Button
            type="submit"
            variant="primary"
            aria-busy={enviando}
            className="disabled:opacity-60 disabled:cursor-not-allowed"
          >
            <IconDeviceFloppy size={15} stroke={1.5} /> {enviando ? 'Guardando…' : textoBoton}
          </Button>
        </div>
      </fieldset>
    </form>
  )
}
