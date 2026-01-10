import { createServerFn } from '@tanstack/react-start'
import type { Register, ValidateSerializableInput } from '@tanstack/router-core'

import { authMiddleware } from '@/server/auth.server'
import { apiGet, apiPut } from '@/server/phlo-api'

export type ObservatorySettingsResponse = {
  settings: Record<string, unknown> | null
  updated_at: string | null
}

type ObservatorySettingsResponseSerializable = ValidateSerializableInput<
  Register,
  ObservatorySettingsResponse
>

export const getObservatorySettings = createServerFn()
  .middleware([authMiddleware])
  .handler(async (): Promise<ObservatorySettingsResponseSerializable> => {
    const response = await apiGet<ObservatorySettingsResponse>(
      '/api/observatory/settings',
    )
    return response as ObservatorySettingsResponseSerializable
  })

export const putObservatorySettings = createServerFn()
  .middleware([authMiddleware])
  // TODO: Keep lightweight client validation; backend enforces the schema.
  .inputValidator((input: { settings: Record<string, unknown> }) => input)
  .handler(
    async ({ data }): Promise<ObservatorySettingsResponseSerializable> => {
      const response = await apiPut<ObservatorySettingsResponse>(
        '/api/observatory/settings',
        data,
      )
      return response as ObservatorySettingsResponseSerializable
    },
  )
