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