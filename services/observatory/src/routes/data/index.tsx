import { createFileRoute, redirect } from '@tanstack/react-router'

import { checkNessieConnection } from '@/server/nessie.server'
import { getEffectiveObservatorySettings } from '@/utils/effectiveSettings'

export const Route = createFileRoute('/data/')({
  beforeLoad: async () => {
    const settings = await getEffectiveObservatorySettings()
    const connection = await checkNessieConnection({
      data: { nessieUrl: settings.connections.nessieUrl },
    })
    const defaultBranch =
      settings.defaults.branch || connection.defaultBranch || 'main'
    throw redirect({
      to: '/data/$branchName',
      params: { branchName: encodeURIComponent(defaultBranch) },
    })
  },
})
