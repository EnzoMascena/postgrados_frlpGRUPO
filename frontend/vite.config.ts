import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000, // puerto del DOCKER
    host: true, // escucha en todas las interfaces, así responde desde el contenedor
    // El front llama siempre a /api/v1/... en su mismo origen y Vite
    // reenvía el pedido al back: así no hay CORS. En local el back
    // está en localhost:8000; en Docker, el compose pone
    // VITE_PROXY_TARGET=http://backend:8000.
    proxy: {
      '/api': {
        target: process.env.VITE_PROXY_TARGET ?? 'http://localhost:8000',
        changeOrigin: true,
      },
    },
    // En Docker sobre Windows Vite no se entera de los cambios en
    // los archivos: con VITE_USE_POLLING=true los revisa cada tanto.
    watch: process.env.VITE_USE_POLLING === 'true' ? { usePolling: true } : undefined,
  },
})
