import { createServerFn } from '@tanstack/react-start'

import { authMiddleware } from '@/server/auth.server'
import { apiGet, apiPut } from '@/server/phlo-api'

export type ObservatorySettingsResponse = {
  // eslint-disable-next-line @typescript-eslint/no-empty-object-type
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
  // eslint-disable-next-line @typescript-eslint/no-empty-object-type
  .inputValidator((input: { settings: Record<string, {}> }) => input)
  .handler(async ({ data }) => {
    return apiPut<ObservatorySettingsResponse>(
      '/api/observatory/settings',
      data,
    )
  })
