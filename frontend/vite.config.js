import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';
import { quasar, transformAssetUrls } from '@quasar/vite-plugin';
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_');
  const apiUrl = process.env.VITE_API_URL || env.VITE_API_URL || 'http://127.0.0.1:8000/api';
  return {
    plugins: [vue({ template: { transformAssetUrls } }), quasar()],
    resolve: { preserveSymlinks: true },
    test: { environment: 'jsdom', setupFiles: ['./src/test-setup.js'] },
    server: {
      port: 5173,
      strictPort: true,
      proxy: {
        '/api': { target: new URL(apiUrl, 'http://127.0.0.1:8000').origin },
      },
    },
  };
});
