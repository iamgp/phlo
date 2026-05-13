import { GitBranch, Loader2 } from 'lucide-react'
import { useEffect, useMemo, useReducer } from 'react'

import type { Branch, NessieConfig } from '@/server/nessie.server'
import { checkNessieConnection, getBranches } from '@/server/nessie.server'
import { useObservatorySettings } from '@/hooks/useObservatorySettings'

interface BranchSelectorProps {
  branch: string
  onChange: (branch: string) => void
}

export function BranchSelector({ branch, onChange }: BranchSelectorProps) {
  const [{ branches, connection, loading }, dispatch] = useReducer(
    (
      state: {
        branches: Array<Branch>
        connection: NessieConfig | null
        loading: boolean
      },
      action:
        | { type: 'loading' }
        | { type: 'loaded'; branches: Array<Branch>; connection: NessieConfig },
    ) => {
      switch (action.type) {
        case 'loading':
          return { ...state, loading: true }
        case 'loaded':
          return {
            branches: action.branches,
            connection: action.connection,
            loading: false,
          }
      }
    },
    { branches: [], connection: null, loading: true },
  )
  const { settings } = useObservatorySettings()

  useEffect(() => {
    let cancelled = false

    async function load() {
      dispatch({ type: 'loading' })
      try {
        const [conn, refs] = await Promise.all([
          checkNessieConnection({
            data: { nessieUrl: settings.connections.nessieUrl },
          }),
          getBranches({ data: { nessieUrl: settings.connections.nessieUrl } }),
        ])

        if (cancelled) return
        dispatch({
          type: 'loaded',
          connection: conn,
          branches:
            'error' in refs ? [] : refs.filter((b) => b.type === 'BRANCH'),
        })
      } catch {
        if (cancelled) return
        dispatch({
          type: 'loaded',
          connection: { connected: false },
          branches: [],
        })
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [settings.connections.nessieUrl])

  const options = useMemo(() => {
    const names = new Set(branches.map((b) => b.name))
    names.add(branch)
    if (connection?.defaultBranch) {
      names.add(connection.defaultBranch)
    }
    return Array.from(names).sort()
  }, [branches, branch, connection?.defaultBranch])

  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <GitBranch className="size-4 text-primary" />
      {loading ? (
        <span className="inline-flex items-center gap-2">
          <Loader2 className="size-3.5 animate-spin text-muted-foreground" />
          Loading branches…
        </span>
      ) : connection?.connected === false ? (
        <span className="text-muted-foreground">Offline</span>
      ) : (
        <select
          value={branch}
          onChange={(e) => onChange(e.target.value)}
          className="h-8 bg-input/30 border border-input px-2 text-xs text-foreground outline-none"
        >
          {options.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
      )}
    </div>
  )
}
