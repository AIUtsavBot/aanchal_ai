import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    cors: true
  },
  // ADD THE PREVIEW CONFIGURATION BLOCK HERE
  preview: {
    // Allows the specified host to access the preview server
    allowedHosts: ['.hello-xo.nl']
  },
  build: {
    outDir: 'dist',
    sourcemap: false
  }
})