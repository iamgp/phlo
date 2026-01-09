import { createServerFn } from '@tanstack/react-start'

import { authMiddleware } from '@/server/auth.server'
import { apiGet, apiPut } from '@/server/phlo-api'

export type ExtensionSettingsResponse = {
  settings: Record<string, {}> | null
  updated_at: string | null
}

export const getExtensionSettings = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: { name: string }) => input)
  .handler(async ({ data }): Promise<ExtensionSettingsResponse> => {
    return apiGet<ExtensionSettingsResponse>(
      `/api/observatory/extensions/${data.name}/settings`,
    )
  })

export const putExtensionSettings = createServerFn()
  .middleware([authMiddleware])
  .inputValidator(
    (input: { name: string; settings: Record<string, {}> }) => input,
  )
  .handler(async ({ data }) => {
    return apiPut<ExtensionSettingsResponse>(
      `/api/observatory/extensions/${data.name}/settings`,
      { settings: data.settings },
    )
  })
