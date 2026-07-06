import { useState } from 'react'
import { IconMoon, IconSun } from '@tabler/icons-react'

export default function ThemeToggle() {
  const [dark, setDark] = useState(() =>
    document.documentElement.classList.contains('dark'),
  )

  function toggle() {
    const next = !dark
    setDark(next)
    document.documentElement.classList.toggle('dark', next)
  }

  return (
    <button
      onClick={toggle}
      className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-input border border-line-strong bg-card text-[12px] text-ink hover:bg-surface transition-colors"
    >
      {dark ? <IconSun size={15} stroke={1.5} /> : <IconMoon size={15} stroke={1.5} />}
      Tema
    </button>
  )
}