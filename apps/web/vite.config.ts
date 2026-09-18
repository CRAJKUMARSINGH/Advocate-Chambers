import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@schema': path.resolve(__dirname, '../../packages/schema'),
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/health': 'http://localhost:8000',
      '/projects': 'http://localhost:8000',
      '/validate': 'http://localhost:8000',
      '/generate': 'http://localhost:8000',
      '/jobs': 'http://localhost:8000',
      '/artifacts': 'http://localhost:8000',
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    target: 'es2022',
  },
});
