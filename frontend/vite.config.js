import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd())

  return {
    plugins: [
      react(),
      {
        name: 'apk-middleware',
        configureServer(server) {
          server.middlewares.use((req, res, next) => {
            if (req.url && req.url.includes('.apk')) {
              res.setHeader('Content-Type', 'application/vnd.android.package-archive');
              res.setHeader('Content-Disposition', 'attachment; filename="word2latex-app.apk"');
            }
            next();
          });
        }
      }
    ],
    server: {
      port: 5173,
      strictPort: true,
      host: true,
      allowedHosts: [
        '.ngrok-free.dev',
        '.trycloudflare.com',
        'word2latex.id.vn',
        'api.word2latex.id.vn'
      ],
      open: false,
      headers: {
        'Cross-Origin-Opener-Policy': 'unsafe-none',
        'Cross-Origin-Embedder-Policy': 'unsafe-none'
      },
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
          headers: {
            'ngrok-skip-browser-warning': 'true',
            'Bypass-Tunnel-Reminder': 'true'
          }
        }
      }
    },
  build: {
    // Tắt minification sử dụng eval trong development
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: false
      }
    }
  }
  }
})
