import { createFileRoute, redirect } from '@tanstack/react-router'

import { checkNessieConnection } from '@/server/nessie.server'

export const Route = createFileRoute('/data/$schema/$table')({
  beforeLoad: async ({ params, search }) => {
    const connection = await checkNessieConnection()
    const defaultBranch = connection.defaultBranch || 'main'
    throw redirect({
      to: '/data/$branchName/$schema/$table',
      params: {
        branchName: encodeURIComponent(defaultBranch),
        schema: params.schema,
        table: params.table,
      },
      search,
    })
  },
})
