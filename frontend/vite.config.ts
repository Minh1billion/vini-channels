import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

const apiTarget = process.env.VITE_API_PROXY ?? 'http://localhost:8000';

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { '@': path.resolve(__dirname, 'src') } },
  server: {
    port: 5173,
    host: true,
    watch: { usePolling: process.env.CHOKIDAR_USEPOLLING === 'true' },
    proxy: { '/api': { target: apiTarget, changeOrigin: true } },
  },
});
