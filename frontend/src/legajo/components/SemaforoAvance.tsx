/* ═══════════════════════════════════════════════════════════════
   SemaforoAvance.tsx — COMPONENTE DEL SEMÁFORO (usado en Legajo)
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Muestra de un vistazo cómo viene el estudiante: verde al día,
   amarillo en progreso, rojo en riesgo. Debajo aparece la
   referencia con los tres estados posibles.

   DETALLE TÉCNICO LINDO PARA CONTAR:
   Este componente NO decide nada: recibe el nivel ya calculado
   desde la pantalla Legajo y solo se ocupa de mostrarlo. Eso se
   llama "componente de presentación", y permite reutilizarlo en
   cualquier otra pantalla que necesite un semáforo.

   El color y el texto salen del objeto `estilos` de acá abajo: en
   vez de escribir if/else, buscamos el nivel como si fuera una
   tabla. Agregar un cuarto estado sería sumar una línea ahí.
   ═══════════════════════════════════════════════════════════════ */

// Los tres estados posibles del semáforo.
type Nivel = 'al-dia' | 'en-progreso' | 'en-riesgo'

const estilos: Record<Nivel, { fondo: string; punto: string; label: string }> = {
  'al-dia':      { fondo: 'bg-ok-bg',     punto: 'bg-ok',     label: 'Al día' },
  'en-progreso': { fondo: 'bg-warn-bg',   punto: 'bg-warn',   label: 'En progreso' },
  'en-riesgo':   { fondo: 'bg-danger-bg', punto: 'bg-danger', label: 'En riesgo' },
}

type Props = {
  nivel: Nivel
  detalle: string
}

// Semáforo de avance. El color y la etiqueta salen del nivel,
// que a su vez se calcula desde los seminarios.
export default function SemaforoAvance({ nivel, detalle }: Props) {
  const estilo = estilos[nivel]

  return (
    <>
      <div className="flex items-center gap-4 mb-3.5">
        <div
          className={
            'w-12 h-12 rounded-full flex-shrink-0 flex items-center justify-center ' +
            estilo.fondo
          }
        >
          <span className={'w-5 h-5 rounded-full ' + estilo.punto} />
        </div>
        <div>
          <div className="font-medium text-[13px] text-ink">{estilo.label}</div>
          <div className="text-[11px] text-muted mt-0.5">{detalle}</div>
        </div>
      </div>

      {/* Referencia de los tres estados posibles */}
      <div className="flex gap-3.5 flex-wrap">
        {(Object.keys(estilos) as Nivel[]).map((n) => (
          <div key={n} className="flex items-center gap-1.5 text-[11px] text-muted">
            <span className={'w-2 h-2 rounded-full ' + estilos[n].punto} />
            {estilos[n].label}
          </div>
        ))}
      </div>
    </>
  )
}