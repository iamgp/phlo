import { createServerFn } from '@tanstack/react-start'
import { z } from 'zod'
import type { Register, ValidateSerializableInput } from '@tanstack/router-core'

import { observatorySettingsSchema } from '@/lib/observatorySettings'
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

const observatorySettingsInputSchema = z.object({
  settings: observatorySettingsSchema,
})

type ObservatorySettingsInput = z.infer<typeof observatorySettingsInputSchema>

export const getObservatorySettings = createServerFn()
  .middleware([authMiddleware])
  .handler(async (): Promise<ObservatorySettingsResponseSerializable> => {
    const response = await apiGet<ObservatorySettingsResponse>(
      '/api/observatory/preferences',
    )
    return response as ObservatorySettingsResponseSerializable
  })

export const putObservatorySettings = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: ObservatorySettingsInput) =>
    observatorySettingsInputSchema.parse(input),
  )
  .handler(
    async ({ data }): Promise<ObservatorySettingsResponseSerializable> => {
      const response = await apiPut<ObservatorySettingsResponse>(
        '/api/observatory/preferences',
        data,
      )
      return response as ObservatorySettingsResponseSerializable
    },
  )
