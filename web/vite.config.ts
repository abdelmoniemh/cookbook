import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The FastAPI server (cookbook-serve) runs on :8000. `npm run dev:mock` points this at the mock API instead.
const target = process.env.VITE_API_TARGET ?? 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    proxy: {
      '/api': { target, changeOrigin: true },
      '/images': { target, changeOrigin: true },
    },
  },
  preview: {
    proxy: {
      '/api': { target, changeOrigin: true },
      '/images': { target, changeOrigin: true },
    },
  },
  build: { outDir: 'dist', sourcemap: false },
})
