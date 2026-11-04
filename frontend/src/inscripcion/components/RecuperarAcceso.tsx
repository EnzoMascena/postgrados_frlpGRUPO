/* ═══════════════════════════════════════════════════════════════
   RecuperarAcceso.tsx — "¿YA EMPEZASTE TU PREINSCRIPCIÓN?"
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   El aspirante no tiene usuario ni contraseña: entra con el link
   que le llega por email. Si lo perdió (o le venció a los 60
   días), escribe su email acá y el back le manda un link nuevo
   (POST /legajos/recuperar-acceso).

   El back responde SIEMPRE lo mismo, exista o no el email: si
   dijera "ese email no está inscripto", cualquiera podría averiguar
   quién se anotó. Por eso mostramos su mensaje tal cual.

   Se muestra aunque el período esté cerrado: el que recibió una
   observación tiene que poder volver a entrar para corregir.

   Con ?recuperar=1 en la URL (el botón del email de observación),
   la página baja hasta esta card y le pone el foco al email.
   ═══════════════════════════════════════════════════════════════ */

import { useEffect, useId, useRef, useState } from 'react'
import { IconMailForward } from '@tabler/icons-react'
import Card from '../../shared/components/Card'
import Field from '../../shared/components/Field'
import Button from '../../shared/components/Button'
import Alerta from '../../shared/components/Alerta'
import { controlClass } from '../../shared/components/controls'
import { ApiError } from '../../shared/api/client'
import { useRecuperarAcceso } from '../hooks/useInscripcion'
import { validarEmail } from '../validaciones'

type Props = {
  /** Si viene de ?recuperar=1: baja hasta la card y enfoca el email. */
  enfocar?: boolean
}

// El mismo estilo de siempre, con el borde en rojo cuando hay error.
const controlConError = controlClass
  .replace('border-line-strong', 'border-danger')
  .replace('focus:border-primary', 'focus:border-danger')

export default function RecuperarAcceso({ enfocar = false }: Props) {
  const id = useId()
  const idEmail = `${id}-email`
  const input = useRef<HTMLInputElement>(null)

  const recuperar = useRecuperarAcceso()
  const [email, setEmail] = useState('')
  const [errorLocal, setErrorLocal] = useState<string | null>(null)

  useEffect(() => {
    if (!enfocar || !input.current) return
    input.current.scrollIntoView({ behavior: 'smooth', block: 'center' })
    input.current.focus({ preventScroll: true })
  }, [enfocar])

  // Un 422 del back con field "email" va al lado del input; lo demás
  // (429 por pedir muchas veces, sin conexión) en una Alerta.
  const errorApi = recuperar.error
  const errorDelCampo =
    errorLocal ?? (errorApi instanceof ApiError && errorApi.campo === 'email' ? errorApi.mensaje : null)
  const errorGeneral = errorApi && !errorDelCampo ? errorApi.message : null

  function enviar() {
    const error = validarEmail(email)
    setErrorLocal(error)
    if (error) {
      input.current?.focus()
      return
    }
    recuperar.mutate(email)
  }

  return (
    <Card title="¿Ya empezaste tu preinscripción?" icon={IconMailForward}>
      <p className="text-[13px] text-muted mb-3">
        Escribí el email con el que te inscribiste y te mandamos un link nuevo para continuar.
      </p>

      <form
        noValidate
        onSubmit={(e) => {
          e.preventDefault()
          enviar()
        }}
        className="flex flex-col sm:flex-row sm:items-start gap-3"
      >
        <Field
          label="Correo electrónico"
          required
          htmlFor={idEmail}
          error={errorDelCampo}
          className="flex-1 min-w-0"
        >
          <input
            ref={input}
            id={idEmail}
            name="email"
            type="email"
            autoComplete="email"
            placeholder="nombre@email.com"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value)
              // Si ya le marcamos un error, se revalida mientras escribe.
              if (errorLocal) setErrorLocal(validarEmail(e.target.value))
              if (recuperar.isError || recuperar.isSuccess) recuperar.reset()
            }}
            aria-invalid={errorDelCampo ? true : undefined}
            aria-describedby={errorDelCampo ? `${idEmail}-error` : undefined}
            className={errorDelCampo ? controlConError : controlClass}
          />
        </Field>
        {/* El margen alinea el botón con el input, debajo del label. */}
        <Button
          type="submit"
          disabled={recuperar.isPending}
          aria-busy={recuperar.isPending}
          className="sm:mt-[26px] disabled:opacity-60 disabled:cursor-not-allowed"
        >
          <IconMailForward size={15} stroke={1.5} />
          {recuperar.isPending ? 'Enviando…' : 'Enviarme el link'}
        </Button>
      </form>

      {recuperar.isSuccess && (
        <Alerta variant="success" className="mt-3">
          {recuperar.data.mensaje}
        </Alerta>
      )}
      {errorGeneral && (
        <Alerta variant="danger" className="mt-3">
          {errorGeneral}
        </Alerta>
      )}
    </Card>
  )
}
