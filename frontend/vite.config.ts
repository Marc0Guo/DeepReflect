import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:7733',
    },
  },
  build: {
    outDir: 'dist',
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return
          if (id.includes('@xyflow')) return 'xyflow'
          if (id.includes('react-markdown') || id.includes('remark-gfm')) return 'markdown'
          if (id.includes('react-router')) return 'router'
          if (id.includes('react-dom')) return 'react-dom'
          if (id.includes('/react/')) return 'react'
        },
      },
    },
  },
})
