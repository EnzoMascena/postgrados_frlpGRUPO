import type { ReactNode } from 'react'

type Props = {
  label: string
  required?: boolean
  children: ReactNode
  className?: string
}

export default function Field({ label, required, children, className = '' }: Props) {
  return (
    <div className={'flex flex-col gap-1.5 ' + className}>
      <label className="text-[13px] text-muted">
        {label} {required && <span className="text-danger">*</span>}
      </label>
      {children}
    </div>
  )
}