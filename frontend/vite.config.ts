import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import { loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '')
  return {
    plugins: [react()],
    server: {
      proxy: {
        '/api': { target: env.VITE_PROXY_TARGET ?? 'http://localhost:8000', changeOrigin: true },
      },
    },
    test: {
      environment: 'jsdom',
      setupFiles: './src/testSetup.ts',
    },
  }
})