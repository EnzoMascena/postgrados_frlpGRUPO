/* ═══════════════════════════════════════════════════════════════
   main.tsx — PUNTO DE ENTRADA DE LA APLICACIÓN
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Este es el primer archivo que ejecuta el navegador. Su única
   tarea es "montar" React dentro del <div id="root"> que está en
   el index.html, y envolver toda la app con los proveedores
   globales de configuración.

   Las 3 piezas que lo componen:
   1) createRoot(...).render(<App />) → React toma ese div del HTML
      y a partir de ahí dibuja TODA la interfaz.
   2) <StrictMode> → modo estricto de React. Solo en desarrollo:
      avisa en consola si usamos algo mal o desactualizado.
   3) <QueryClientProvider> → React Query. Es la librería que en la
      Entrega 3 va a manejar los pedidos HTTP al backend (traer
      datos, cachearlos, reintentar si falla). Ya lo dejamos
      configurado aunque hoy los datos salgan de archivos mock.

   FRASE PARA DECIR: "main.tsx es el arranque: engancha React al
   HTML y deja lista la configuración global de la app."
   ═══════════════════════════════════════════════════════════════ */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import './index.css'

// Cliente de React Query: el "administrador" central de los datos
// que en la próxima entrega se van a pedir a la API del backend.
const queryClient = new QueryClient()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
)