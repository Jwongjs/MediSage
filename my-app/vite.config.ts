import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tsconfigPaths from 'vite-tsconfig-paths';
import path from 'path';

export default defineConfig({
  plugins: [
    react({ include: /\.[jt]sx?$/ }),
    tsconfigPaths(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    open: false,
    proxy: {
      // /diagnosis is BOTH an SPA page route and an API prefix. The regex
      // requires a sub-path so only the API calls proxy; a bare '/diagnosis'
      // prefix would swallow the page and serve the browser a raw FastAPI 404.
      // Dev only -- in production nginx serves the SPA and the API is a
      // separate origin via VITE_API_URL.
      '^/diagnosis/.+': 'http://localhost:8000',
      '/patient': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
});
