import tailwindcss from '@tailwindcss/vite'
import { devtools } from '@tanstack/devtools-vite'
import { tanstackStart } from '@tanstack/react-start/plugin/vite'
import viteReact from '@vitejs/plugin-react'
import { nitro } from 'nitro/vite'
import { defineConfig } from 'vite'
import viteTsConfigPaths from 'vite-tsconfig-paths'

const devHost = process.env.DEV_HOST ?? 'localhost'
const devHmrHost = process.env.DEV_HMR_HOST ?? devHost
const devHmrClientPort = process.env.DEV_HMR_CLIENT_PORT
const devAllowedHosts = (process.env.DEV_ALLOWED_HOSTS ?? devHost)
  .split(',')
  .flatMap((host) => {
    const trimmed = host.trim()
    return trimmed ? [trimmed] : []
  })

const config = defineConfig({
  server: {
    port: 3001,
    allowedHosts: devAllowedHosts,
    host: devHost,
    hmr: {
      host: devHmrHost,
      ...(devHmrClientPort
        ? { clientPort: Number.parseInt(devHmrClientPort, 10) }
        : {}),
      protocol: 'ws',
    },
  },
  ssr: {
    noExternal: ['@primer/react'],
  },
  plugins: [
    devtools(),
    nitro(),
    // this is the plugin that enables path aliases
    viteTsConfigPaths({
      projects: ['./tsconfig.json'],
    }),
    tailwindcss(),
    tanstackStart(),
    viteReact(),
  ],
})

export default config
