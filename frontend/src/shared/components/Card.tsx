import type { ElementType, ReactNode } from 'react'

type Props = {
  title?: string
  icon?: ElementType
  children: ReactNode
  className?: string
}

export default function Card({ title, icon: Icon, children, className = '' }: Props) {
  return (
    <div className={'bg-card border border-line rounded-card shadow-card p-5 mb-4 ' + className}>
      {title && (
        <div className="flex items-center gap-1.5 text-[13px] font-medium text-ink mb-3.5">
          {Icon && <Icon size={15} stroke={1.5} />}
          {title}
        </div>
      )}
      {children}
    </div>
  )
}