import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { quasar, transformAssetUrls } from '@quasar/vite-plugin';
export default defineConfig({
  plugins: [vue({ template: { transformAssetUrls } }), quasar()],
  resolve: { preserveSymlinks: true },
  test: { environment: 'jsdom', setupFiles: ['./src/test-setup.js'] },
  server: { port: 5173, strictPort: true },
});
