// Launch the existing UI with all Vite caches in the new extension folder.
import { createServer } from '../frontend/node_modules/vite/dist/node/index.js';
import { fileURLToPath } from 'node:url';
const frontend = fileURLToPath(new URL('../frontend/', import.meta.url));
process.chdir(frontend);
const server = await createServer({
  root: frontend,
  configFile: fileURLToPath(new URL('../frontend/vite.config.ts', import.meta.url)),
  configLoader: 'runner',
  cacheDir: fileURLToPath(new URL('./runtime/vite-cache/', import.meta.url)),
  server: { host: '127.0.0.1', port: 5173, strictPort: true },
});
await server.listen();
server.printUrls();
