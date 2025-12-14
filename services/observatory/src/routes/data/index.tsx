import { createFileRoute, redirect } from '@tanstack/react-router'

import { checkNessieConnection } from '@/server/nessie.server'

export const Route = createFileRoute('/data/')({
  beforeLoad: async () => {
    const connection = await checkNessieConnection()
    const defaultBranch = connection.defaultBranch || 'main'
    throw redirect({
      to: '/data/$branchName',
      params: { branchName: encodeURIComponent(defaultBranch) },
    })
  },
})
