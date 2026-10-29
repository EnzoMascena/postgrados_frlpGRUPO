/* ═══════════════════════════════════════════════════════════════
   NoEncontrado.tsx — PÁGINA 404
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Es lo que se ve cuando la URL no coincide con ninguna ruta
   (la ruta "*" de App). Más adelante también la usa RutaProtegida
   cuando alguien entra con un rol que no corresponde: así no le
   contamos que la pantalla existe.
   ═══════════════════════════════════════════════════════════════ */

import { Link } from 'react-router'
import { IconError404 } from '@tabler/icons-react'
import Card from '../components/Card'

export default function NoEncontrado() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-page p-6">
      <div className="w-full max-w-[420px]">
        <Card className="text-center">
          <IconError404 size={32} stroke={1.5} className="mx-auto text-faint" />
          <h1 className="text-[18px] font-medium text-ink mt-2">Página no encontrada</h1>
          <p className="text-[12.5px] text-muted mt-1">
            La dirección que buscás no existe o no tenés acceso.
          </p>
          <Link to="/" className="inline-block mt-4 text-[12.5px] text-primary hover:underline">
            Volver al inicio
          </Link>
        </Card>
      </div>
    </main>
  )
}
