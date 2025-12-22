import { ChevronDown, Loader2, Play, Trash2 } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import type { DataPreviewResult } from '@/server/trino.server'
import { SaveQueryDialog } from '@/components/data/SaveQueryDialog'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Textarea } from '@/components/ui/textarea'
import { useObservatorySettings } from '@/hooks/useObservatorySettings'
import { useSavedQueries } from '@/hooks/useSavedQueries'
import { executeQuery } from '@/server/trino.server'
import { quoteIdentifier } from '@/utils/sqlIdentifiers'

interface QueryEditorProps {
  defaultQuery?: string
  onResults: (results: DataPreviewResult | null) => void
  branch: string
  autoRun?: boolean // Auto-execute when defaultQuery changes
}

export function QueryEditor({
  defaultQuery = '',
  onResults,
  branch,
  autoRun = false,
}: QueryEditorProps) {
  const [query, setQuery] = useState(defaultQuery)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [effectiveQuery, setEffectiveQuery] = useState<string | null>(null)
  const [confirmState, setConfirmState] = useState<{
    statement: string
  } | null>(null)
  const lastAutoRunQueryRef = useRef<string | null>(null)
  const { settings } = useObservatorySettings()
  const { queries: savedQueries } = useSavedQueries()

  // Sync query when defaultQuery changes from external source
  useEffect(() => {
    if (defaultQuery) {
      setQuery(defaultQuery)
    }
  }, [defaultQuery])

  // Auto-execute query when autoRun is enabled and defaultQuery changes
  useEffect(() => {
    // Wait for settings to be loaded
    if (!settings?.defaults?.catalog) return

    if (
      autoRun &&
      defaultQuery &&
      defaultQuery !== lastAutoRunQueryRef.current &&
      !loading
    ) {
      lastAutoRunQueryRef.current = defaultQuery
      // Small delay to ensure render is complete
      const timer = setTimeout(() => {
        runQueryInternal(defaultQuery)
      }, 300)
      return () => clearTimeout(timer)
    }
  }, [autoRun, defaultQuery, loading, settings])

  const runQueryInternal = async (queryToRun: string) => {
    if (!queryToRun.trim()) return

    setLoading(true)
    setError(null)
    setEffectiveQuery(null)
    onResults(null)

    try {
      const result = await executeQuery({
        data: {
          query: queryToRun,
          branch,
          catalog: settings.defaults.catalog,
          trinoUrl: settings.connections.trinoUrl,
          timeoutMs: settings.query.timeoutMs,
          readOnlyMode: settings.query.readOnlyMode,
          defaultLimit: settings.query.defaultLimit,
          maxLimit: settings.query.maxLimit,
        },
      })
      if ('error' in result) {
        const err = result
        if (err.kind === 'confirm_required' && err.effectiveQuery) {
          setConfirmState({ statement: err.effectiveQuery })
        } else {
          setError(result.error)
        }
      } else {
        onResults(result)
        setEffectiveQuery(result.effectiveQuery ?? null)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Query failed')
    } finally {
      setLoading(false)
    }
  }

  const runConfirmedUnsafeQuery = async () => {
    if (!confirmState) return
    setLoading(true)
    setError(null)
    setEffectiveQuery(null)
    onResults(null)
    try {
      const result = await executeQuery({
        data: {
          query: confirmState.statement,
          branch,
          catalog: settings.defaults.catalog,
          trinoUrl: settings.connections.trinoUrl,
          timeoutMs: settings.query.timeoutMs,
          readOnlyMode: settings.query.readOnlyMode,
          defaultLimit: settings.query.defaultLimit,
          maxLimit: settings.query.maxLimit,
          allowUnsafe: true,
        },
      })
      if ('error' in result) {
        setError(result.error)
      } else {
        onResults(result)
        setEffectiveQuery(result.effectiveQuery ?? null)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Query failed')
    } finally {
      setLoading(false)
      setConfirmState(null)
    }
  }

  const runQuery = () => runQueryInternal(query)

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Cmd/Ctrl + Enter to run
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault()
      runQuery()
    }
  }

  return (
    <div className="flex flex-col">
      {/* Editor */}
      <div className="relative">
        <Textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={`SELECT * FROM ${quoteIdentifier(settings.defaults.catalog)}.${quoteIdentifier(branch)}.table_name LIMIT ${settings.query.defaultLimit}`}
          className="min-h-[100px] md:h-32 text-xs resize-none"
          spellCheck={false}
        />
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between mt-2">
        <div className="flex items-center gap-2">
          <Button onClick={runQuery} disabled={loading || !query.trim()}>
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            Run Query
          </Button>
          <SaveQueryDialog query={query} branch={branch} />
          {savedQueries.length > 0 && (
            <DropdownMenu>
              <DropdownMenuTrigger
                render={
                  <Button variant="outline" size="sm">
                    Load Query
                    <ChevronDown className="w-4 h-4 ml-1" />
                  </Button>
                }
              />
              <DropdownMenuContent
                align="start"
                className="max-h-64 overflow-auto"
              >
                {savedQueries.map((sq) => (
                  <DropdownMenuItem
                    key={sq.id}
                    onClick={() => setQuery(sq.query)}
                  >
                    <span className="truncate max-w-[200px]">{sq.name}</span>
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
          <span className="text-xs text-muted-foreground">⌘+Enter</span>
          <span className="text-xs text-muted-foreground">
            {settings.query.readOnlyMode ? 'Read-only' : 'Unsafe allowed'}
          </span>
        </div>

        <Button
          variant="ghost"
          size="icon-sm"
          onClick={() => {
            setQuery('')
            setError(null)
            onResults(null)
          }}
          title="Clear"
        >
          <Trash2 className="w-4 h-4" />
        </Button>
      </div>

      {effectiveQuery && (
        <div className="mt-2 text-xs text-muted-foreground">
          Effective query enforced by guardrails.
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mt-3 p-3 bg-destructive/10 border border-destructive/30 text-destructive text-sm">
          {error}
        </div>
      )}

      {confirmState && (
        <Dialog open={true} onOpenChange={() => setConfirmState(null)}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Confirm unsafe query</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                This statement is not read-only. Running it may mutate data or
                metadata.
              </p>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setConfirmState(null)}>
                  Cancel
                </Button>
                <Button
                  onClick={() => void runConfirmedUnsafeQuery()}
                  disabled={loading}
                >
                  Run anyway
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  )
}
