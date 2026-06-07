import { defineConfig } from 'vite'
import type { Connect } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

function spaFallback(): {
  name: string
  configureServer: (server: { middlewares: Connect.Server }) => void
} {
  const proxied = ['/auth', '/users', '/video']
  return {
    name: 'spa-fallback',
    configureServer(server) {
      server.middlewares.use((req, _res, next) => {
        const url = req.url ?? '/'
        const isFile = url.includes('.')
        const isProxied = proxied.some((p) => url.startsWith(p))
        if (!isFile && !isProxied) {
          req.url = '/index.html'
        }
        next()
      })
    },
  }
}

export default defineConfig({
  plugins: [react(), tailwindcss(), spaFallback()],
  server: {
    proxy: {
      '/auth': 'http://localhost:8000',
      '/users': 'http://localhost:8000',
      '/video': 'http://localhost:8000',
    },
  },
})
