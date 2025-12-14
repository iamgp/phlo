import { GitBranch, Loader2 } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'

import type { Branch, NessieConfig } from '@/server/nessie.server'
import { checkNessieConnection, getBranches } from '@/server/nessie.server'

interface BranchSelectorProps {
  branch: string
  onChange: (branch: string) => void
}

export function BranchSelector({ branch, onChange }: BranchSelectorProps) {
  const [connection, setConnection] = useState<NessieConfig | null>(null)
  const [branches, setBranches] = useState<Array<Branch>>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      setLoading(true)
      const [conn, refs] = await Promise.all([
        checkNessieConnection(),
        getBranches(),
      ])

      setConnection(conn)
      if (!('error' in refs)) {
        setBranches(refs.filter((b) => b.type === 'BRANCH'))
      } else {
        setBranches([])
      }
      setLoading(false)
    }

    load()
  }, [])

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
      <GitBranch className="w-4 h-4 text-primary" />
      {loading ? (
        <span className="inline-flex items-center gap-2">
          <Loader2 className="w-3.5 h-3.5 animate-spin text-muted-foreground" />
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
