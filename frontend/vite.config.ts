import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

/** Momento do `vite build` ou do start do `vite dev` (America/Sao_Paulo). */
const appBuildAt = new Date().toLocaleString('pt-BR', {
  dateStyle: 'short',
  timeStyle: 'short',
  timeZone: 'America/Sao_Paulo',
})

export default defineConfig({
  define: {
    'import.meta.env.VITE_APP_BUILD_AT': JSON.stringify(appBuildAt),
  },
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
