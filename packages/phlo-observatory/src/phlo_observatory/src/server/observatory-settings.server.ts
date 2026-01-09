import { createServerFn } from '@tanstack/react-start'

import { authMiddleware } from '@/server/auth.server'
import { apiGet, apiPut } from '@/server/phlo-api'

export type ObservatorySettingsResponse = {
  settings: Record<string, {}> | null
  updated_at: string | null
}

export const getObservatorySettings = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: Record<string, never> = {}) => input)
  .handler(async (): Promise<ObservatorySettingsResponse> => {
    return apiGet<ObservatorySettingsResponse>('/api/observatory/settings')
  })

export const putObservatorySettings = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: { settings: Record<string, {}> }) => input)
  .handler(async ({ data }) => {
    return apiPut<ObservatorySettingsResponse>(
      '/api/observatory/settings',
      data,
    )
  })
