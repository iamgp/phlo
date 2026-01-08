import { createServerFn } from '@tanstack/react-start'

import { apiGet, apiPut } from '@/server/phlo-api'

export type ObservatorySettingsResponse = {
  settings: Record<string, unknown> | null
  updated_at: string | null
}

export const getObservatorySettings = createServerFn().handler(
  async (): Promise<ObservatorySettingsResponse> => {
    return apiGet<ObservatorySettingsResponse>(
      '/api/observatory/settings',
      undefined,
      200,
    )
  },
)

export const putObservatorySettings = createServerFn().handler(
  async ({ data }: { data: { settings: Record<string, unknown> } }) => {
    return apiPut<ObservatorySettingsResponse>(
      '/api/observatory/settings',
      data,
      200,
    )
  },
)
