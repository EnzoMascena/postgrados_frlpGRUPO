import type { ElementType, ReactNode } from 'react'
import ThemeToggle from '../components/ThemeToggle'

type Props = {
  title: string
  icon?: ElementType
  children?: ReactNode
}

export default function Topbar({ title, icon: Icon, children }: Props) {
  return (
    <div className="h-14 flex items-center justify-between gap-3 px-5 bg-card border-b border-line flex-shrink-0">
      <div className="flex items-center gap-1.5 font-medium text-[15px] text-ink truncate">
        {Icon && <Icon size={15} stroke={1.5} />}
        {title}
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        {children}
        <ThemeToggle />
      </div>
    </div>
  )
}