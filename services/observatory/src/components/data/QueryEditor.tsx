import { Loader2, Play, Trash2 } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import type { DataPreviewResult } from '@/server/trino.server'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { executeQuery } from '@/server/trino.server'

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
  const lastAutoRunQueryRef = useRef<string | null>(null)

  // Sync query when defaultQuery changes from external source
  useEffect(() => {
    if (defaultQuery) {
      setQuery(defaultQuery)
    }
  }, [defaultQuery])

  // Auto-execute query when autoRun is enabled and defaultQuery changes
  useEffect(() => {
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
  }, [autoRun, defaultQuery, loading])

  const runQueryInternal = async (queryToRun: string) => {
    if (!queryToRun.trim()) return

    setLoading(true)
    setError(null)
    onResults(null)

    try {
      const result = await executeQuery({ data: { query: queryToRun, branch } })
      if ('error' in result) {
        setError(result.error)
      } else {
        onResults(result)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Query failed')
    } finally {
      setLoading(false)
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
          placeholder={`SELECT * FROM iceberg."${branch}".table_name LIMIT 100`}
          className="h-32 text-xs resize-none"
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
          <span className="text-xs text-muted-foreground">⌘+Enter</span>
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

      {/* Error */}
      {error && (
        <div className="mt-3 p-3 bg-destructive/10 border border-destructive/30 text-destructive text-sm">
          {error}
        </div>
      )}
    </div>
  )
}
