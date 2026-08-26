/* ═══════════════════════════════════════════════════════════════
   Button.tsx — BOTÓN ÚNICO DE TODA LA APLICACIÓN
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Un solo botón con tres VARIANTES visuales:
     · default → acciones secundarias (Exportar, Guardar borrador)
     · primary → la acción principal (Enviar inscripción, Ingresar)
     · danger  → acciones destructivas

   Al usarlo se escribe <Button variant="primary">Enviar</Button>.
   Los estilos de cada variante están en el objeto `styles`.

   DETALLE TÉCNICO: el `...rest` de la firma reenvía al <button>
   real cualquier atributo de HTML (onClick, disabled, type...).
   Así nuestro componente se comporta igual que un botón común
   pero con el estilo del sistema ya aplicado.
   ═══════════════════════════════════════════════════════════════ */

import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Variant = 'default' | 'primary' | 'danger'

const styles: Record<Variant, string> = {
  default: 'bg-card border-line-strong text-ink hover:bg-surface',
  primary: 'bg-primary border-primary text-white hover:bg-primary-hover hover:border-primary-hover',
  danger: 'bg-card border-danger-border text-danger hover:bg-danger-bg',
}

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant
  children: ReactNode
}

export default function Button({ variant = 'default', children, className = '', ...rest }: Props) {
  return (
    <button
      className={
        'inline-flex items-center justify-center gap-1.5 px-3.5 py-1.5 rounded-input border text-[12px] font-medium whitespace-nowrap transition-colors ' +
        styles[variant] +
        ' ' +
        className
      }
      {...rest}
    >
      {children}
    </button>
  )
}