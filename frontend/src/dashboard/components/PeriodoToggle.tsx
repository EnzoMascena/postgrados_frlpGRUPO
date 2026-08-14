type Props = {
  abierto: boolean
  onToggle: () => void
}

// Interruptor del período de inscripción.
// El color y el texto salen del estado: no se tocan clases a mano.
export default function PeriodoToggle({ abierto, onToggle }: Props) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-[11px] text-muted whitespace-nowrap">
        Período de inscripción
      </span>

      <button
        onClick={onToggle}
        role="switch"
        aria-checked={abierto}
        aria-label="Alternar período de inscripción"
        className={
          'relative w-8 h-[18px] rounded-full transition-colors flex-shrink-0 ' +
          (abierto ? 'bg-ok' : 'bg-line-strong')
        }
      >
        <span
          className={
            'absolute top-[2px] w-[14px] h-[14px] rounded-full bg-white transition-all ' +
            (abierto ? 'left-[16px]' : 'left-[2px]')
          }
        />
      </button>

      <span
        className={
          'text-[11px] font-medium whitespace-nowrap ' +
          (abierto ? 'text-ok' : 'text-muted')
        }
      >
        {abierto ? 'Abierto' : 'Cerrado'}
      </span>
    </div>
  )
}