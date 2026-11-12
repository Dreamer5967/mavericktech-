import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      // P4-04: AI/VQA question service and Camera API (port 8001) — must be listed
      // BEFORE the general /api rule so the more-specific path wins.
      '/api/v1/questions': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/api/v1/frames': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
});

