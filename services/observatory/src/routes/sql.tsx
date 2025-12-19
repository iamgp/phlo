/**
 * SQL Query Route
 *
 * Standalone SQL query editor page for running queries without a table selected.
 */
import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/sql')({
  beforeLoad: async () => {
    // Redirect to data explorer with SQL tab open
    throw redirect({
      to: '/data/$branchName',
      params: { branchName: 'main' },
      search: { tab: 'query' },
    })
  },
  component: () => null,
})
