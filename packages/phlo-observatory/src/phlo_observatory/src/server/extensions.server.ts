import { createServerFn } from '@tanstack/react-start'

import { apiGet } from '@/server/phlo-api'

export type ObservatoryExtensionRoute = {
  path: string
  module: string
  export: string
}

export type ObservatoryExtensionNavItem = {
  title: string
  to: string
}

export type ObservatoryExtensionSlot = {
  slot_id: string
  module: string
  export: string
}

export type ObservatoryExtensionManifest = {
  name: string
  version: string
  compat: {
    observatory_min: string
  }
  settings?: {
    schema: Record<string, {}>
    defaults?: Record<string, {}>
  }
  ui?: {
    routes?: Array<ObservatoryExtensionRoute>
    nav?: Array<ObservatoryExtensionNavItem>
    slots?: Array<ObservatoryExtensionSlot>
  }
}

export type ObservatoryExtensionDescriptor = {
  manifest: ObservatoryExtensionManifest
  assets_base_path: string
}

export type ObservatoryExtensionResponse = {
  extensions: Array<ObservatoryExtensionDescriptor>
}

const PHLO_API_URL = process.env.PHLO_API_URL || 'http://localhost:4000'

function withAssetUrl(basePath: string, path: string): string {
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  const normalized = path.startsWith('/') ? path : `/${path}`
  return `${PHLO_API_URL}${basePath}${normalized}`
}

export type ObservatoryExtension = {
  manifest: ObservatoryExtensionManifest
  assetsBasePath: string
  assetsBaseUrl: string
}

export const getObservatoryExtensions = createServerFn().handler(
  async (): Promise<Array<ObservatoryExtension>> => {
    const response = await apiGet<ObservatoryExtensionResponse>(
      '/api/observatory/extensions',
    )

    return response.extensions.map((entry) => {
      const basePath = entry.assets_base_path
      const assetsBaseUrl = `${PHLO_API_URL}${basePath}`
      const ui = entry.manifest.ui

      if (ui?.routes) {
        ui.routes = ui.routes.map((route) => ({
          ...route,
          module: withAssetUrl(basePath, route.module),
        }))
      }

      if (ui?.slots) {
        ui.slots = ui.slots.map((slot) => ({
          ...slot,
          module: withAssetUrl(basePath, slot.module),
        }))
      }

      return {
        manifest: entry.manifest,
        assetsBasePath: basePath,
        assetsBaseUrl,
      }
    })
  },
)
