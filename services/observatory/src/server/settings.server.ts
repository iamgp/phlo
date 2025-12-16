import { createServerFn } from '@tanstack/react-start'

import type { ObservatorySettings } from '@/lib/observatorySettings'
import { getFallbackObservatorySettings } from '@/lib/observatorySettings'

export const getObservatorySettingsDefaults = createServerFn().handler(
  (): ObservatorySettings => {
    const fallback = getFallbackObservatorySettings()

    return {
      ...fallback,
      connections: {
        dagsterGraphqlUrl:
          process.env.DAGSTER_GRAPHQL_URL ||
          fallback.connections.dagsterGraphqlUrl,
        trinoUrl: process.env.TRINO_URL || fallback.connections.trinoUrl,
        nessieUrl: process.env.NESSIE_URL || fallback.connections.nessieUrl,
      },
    }
  },
)
