import { Loader2, Play, Trash2 } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import type { DataPreviewResult } from '@/server/trino.server'
import { executeQuery } from '@/server/trino.server'

interface QueryEditorProps {
  defaultQuery?: string
  onResults: (results: DataPreviewResult | null) => void
  branch: string
  autoRun?: boolean // Auto-execute when defaultQuery changes (phlo-gxl)
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

  // Sync query when defaultQuery changes from external source (phlo-gxl)
  useEffect(() => {
    if (defaultQuery) {
      setQuery(defaultQuery)
    }
  }, [defaultQuery])

  // Auto-execute query when autoRun is enabled and defaultQuery changes (phlo-gxl)
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
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={`SELECT * FROM iceberg."${branch}".table_name LIMIT 100`}
          className="w-full h-32 p-3 bg-slate-900 border border-slate-700 rounded-lg font-mono text-sm resize-none focus:outline-none focus:border-cyan-500"
          spellCheck={false}
        />
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between mt-2">
        <div className="flex items-center gap-2">
          <button
            onClick={runQuery}
            disabled={loading || !query.trim()}
            className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-700 disabled:text-slate-500 rounded-lg transition-colors text-sm font-medium"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            Run Query
          </button>
          <span className="text-xs text-slate-500">⌘+Enter</span>
        </div>

        <button
          onClick={() => {
            setQuery('')
            setError(null)
            onResults(null)
          }}
          className="p-2 text-slate-500 hover:text-slate-300 hover:bg-slate-800 rounded transition-colors"
          title="Clear"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="mt-3 p-3 bg-red-900/20 border border-red-700/50 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}
    </div>
  )
}
