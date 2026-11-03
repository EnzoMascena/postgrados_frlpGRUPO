/* ═══════════════════════════════════════════════════════════════
   main.tsx — PUNTO DE ENTRADA DE LA APLICACIÓN
   ───────────────────────────────────────────────────────────────
   PARA EXPONER:
   Este es el primer archivo que ejecuta el navegador. Su única
   tarea es "montar" React dentro del <div id="root"> que está en
   el index.html, y envolver toda la app con los proveedores
   globales de configuración.

   Las 5 piezas que lo componen:
   1) createRoot(...).render(<App />) → React toma ese div del HTML
      y a partir de ahí dibuja TODA la interfaz.
   2) <StrictMode> → modo estricto de React. Solo en desarrollo:
      avisa en consola si usamos algo mal o desactualizado.
   3) <QueryClientProvider> → TanStack Query. Maneja los pedidos a
      la API: trae los datos, los guarda en caché y reintenta si
      falla. Lo configuramos para que reintente UNA sola vez y
      para que no vuelva a pedir todo cada vez que volvés a la
      pestaña del navegador.
   4) <BrowserRouter> → React Router. Lee la URL del navegador y
      le avisa a App qué ruta está activa. Envuelve a App para que
      cualquier componente pueda usar NavLink o useNavigate.
   5) <AuthProvider> → la sesión del coordinador (quién es y su
      token). Va adentro de QueryClientProvider porque al cerrar
      sesión vacía la caché de TanStack Query.

   FRASE PARA DECIR: "main.tsx es el arranque: engancha React al
   HTML y deja lista la configuración global de la app."
   ═══════════════════════════════════════════════════════════════ */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import AuthProvider from './shared/auth/AuthProvider'
import App from './App'
import './index.css'

// Cliente de TanStack Query: el "administrador" central de los
// datos que se piden a la API del backend.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)