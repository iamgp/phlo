/**
 * CommandPalette Component
 *
 * Global search dialog using cmdk.
 * Triggered with ⌘K / Ctrl+K.
 * Searches across assets, tables, and columns.
 */

import { useNavigate } from '@tanstack/react-router'
import {
  ArrowRight,
  Clipboard,
  Database,
  FileCode,
  GitBranch,
  LayoutGrid,
  Settings,
  Table2,
} from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'

import type { SearchIndex } from '@/server/search.types'
import {
  Command,
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
  CommandShortcut,
} from '@/components/ui/command'
import { useToast } from '@/hooks/use-toast'

interface CommandPaletteProps {
  searchIndex: SearchIndex | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function CommandPalette({
  searchIndex,
  open,
  onOpenChange,
}: CommandPaletteProps) {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [search, setSearch] = useState('')

  // Handle keyboard shortcut
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        onOpenChange(!open)
      }
    }

    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [open, onOpenChange])

  const handleSelect = useCallback(
    (value: string) => {
      onOpenChange(false)
      setSearch('')

      // Parse the action from the value
      if (value.startsWith('asset:')) {
        const assetKey = value.replace('asset:', '')
        navigate({ to: '/assets/$assetId', params: { assetId: assetKey } })
      } else if (value.startsWith('graph:')) {
        const assetKey = value.replace('graph:', '')
        navigate({ to: '/graph', search: { focus: assetKey } })
      } else if (value.startsWith('table:')) {
        // Navigate to data explorer for this table
        const [schema, table] = value.replace('table:', '').split('/')
        navigate({
          to: '/data/$schema/$table',
          params: { schema, table },
        })
      } else if (value.startsWith('sql:')) {
        // Copy SQL template to clipboard
        const fullName = value.replace('sql:', '')
        const sqlTemplate = `SELECT * FROM ${fullName} LIMIT 100`
        navigator.clipboard.writeText(sqlTemplate).then(() => {
          toast({
            title: 'SQL Copied',
            description: 'Query template copied to clipboard',
          })
        })
      } else if (value === 'nav:dashboard') {
        navigate({ to: '/' })
      } else if (value === 'nav:assets') {
        navigate({ to: '/assets' })
      } else if (value === 'nav:graph') {
        navigate({ to: '/graph' })
      } else if (value === 'nav:data') {
        navigate({ to: '/data' })
      } else if (value === 'nav:quality') {
        navigate({ to: '/quality' })
      } else if (value === 'nav:hub') {
        navigate({ to: '/hub' })
      } else if (value === 'nav:branches') {
        navigate({ to: '/branches' })
      } else if (value === 'nav:settings') {
        navigate({ to: '/settings' })
      }
    },
    [navigate, onOpenChange, toast],
  )

  // Filter items based on search - cmdk handles this, but we limit results
  const assets = useMemo(() => searchIndex?.assets ?? [], [searchIndex])
  const tables = useMemo(() => searchIndex?.tables ?? [], [searchIndex])
  const columns = useMemo(() => searchIndex?.columns ?? [], [searchIndex])

  // Only show columns when user is searching
  const showColumns = search.length >= 2 && columns.length > 0

  if (!open) return null

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange} className="max-w-xl">
      <Command shouldFilter={true}>
        <CommandInput
          value={search}
          onValueChange={setSearch}
          placeholder="Search assets, tables, columns..."
          autoFocus
        />

        <CommandList>
          <CommandEmpty>No results found.</CommandEmpty>

          <CommandGroup heading="Navigation">
            <CommandItem value="nav:dashboard" onSelect={handleSelect}>
              <ArrowRight />
              <span>Go to Dashboard</span>
              <CommandShortcut>↵</CommandShortcut>
            </CommandItem>
            <CommandItem value="nav:assets" onSelect={handleSelect}>
              <Database />
              <span>Go to Assets</span>
            </CommandItem>
            <CommandItem value="nav:data" onSelect={handleSelect}>
              <Table2 />
              <span>Go to Data Explorer</span>
            </CommandItem>
            <CommandItem value="nav:graph" onSelect={handleSelect}>
              <GitBranch />
              <span>Go to Lineage Graph</span>
            </CommandItem>
            <CommandItem value="nav:quality" onSelect={handleSelect}>
              <FileCode />
              <span>Go to Quality Center</span>
            </CommandItem>
            <CommandItem value="nav:hub" onSelect={handleSelect}>
              <LayoutGrid />
              <span>Go to Hub</span>
            </CommandItem>
            <CommandItem value="nav:branches" onSelect={handleSelect}>
              <GitBranch />
              <span>Go to Branches</span>
            </CommandItem>
            <CommandItem value="nav:settings" onSelect={handleSelect}>
              <Settings />
              <span>Go to Settings</span>
            </CommandItem>
          </CommandGroup>

          {assets.length > 0 && <CommandSeparator />}

          {assets.length > 0 && (
            <CommandGroup heading="Assets">
              {assets.slice(0, 15).map((asset) => (
                <CommandItem
                  key={asset.id}
                  value={`asset:${asset.keyPath}`}
                  onSelect={handleSelect}
                >
                  <Database />
                  <span className="truncate">{asset.keyPath}</span>
                  {asset.groupName && (
                    <span className="ml-auto text-xs text-muted-foreground">
                      {asset.groupName}
                    </span>
                  )}
                </CommandItem>
              ))}
            </CommandGroup>
          )}

          {tables.length > 0 && <CommandSeparator />}

          {tables.length > 0 && (
            <CommandGroup heading="Tables">
              {tables.slice(0, 10).map((table) => (
                <CommandItem
                  key={table.fullName}
                  value={`table:${table.schema}/${table.name}`}
                  onSelect={handleSelect}
                  keywords={[table.name, table.schema, table.layer]}
                >
                  <Table2 />
                  <span className="truncate">
                    {table.schema}.{table.name}
                  </span>
                  <span className="ml-auto text-xs text-muted-foreground">
                    {table.layer}
                  </span>
                </CommandItem>
              ))}
            </CommandGroup>
          )}

          {showColumns && <CommandSeparator />}

          {showColumns && (
            <CommandGroup heading="Columns">
              {columns.slice(0, 8).map((col, index) => (
                <CommandItem
                  key={`${col.tableName}-${col.name}-${index}`}
                  value={`table:${col.tableSchema}/${col.tableName}`}
                  onSelect={handleSelect}
                  keywords={[col.name, col.tableName, col.type]}
                >
                  <FileCode />
                  <span className="truncate font-mono text-sm">{col.name}</span>
                  <span className="ml-auto text-xs text-muted-foreground">
                    {col.tableName} · {col.type}
                  </span>
                </CommandItem>
              ))}
            </CommandGroup>
          )}

          {search && tables.length > 0 && <CommandSeparator />}

          {search && tables.length > 0 && (
            <CommandGroup heading="SQL Templates">
              {tables.slice(0, 5).map((table) => (
                <CommandItem
                  key={`sql-${table.fullName}`}
                  value={`sql:${table.fullName}`}
                  onSelect={handleSelect}
                  keywords={[table.name, table.schema, 'select', 'query']}
                >
                  <Clipboard />
                  <span className="truncate">
                    Copy SELECT * FROM {table.name}
                  </span>
                </CommandItem>
              ))}
            </CommandGroup>
          )}

          {search && assets.length > 0 && <CommandSeparator />}

          {search && assets.length > 0 && (
            <CommandGroup heading="Focus in Graph">
              {assets.slice(0, 5).map((asset) => (
                <CommandItem
                  key={`graph-${asset.id}`}
                  value={`graph:${asset.keyPath}`}
                  onSelect={handleSelect}
                >
                  <GitBranch />
                  <span className="truncate">
                    Show {asset.keyPath} in graph
                  </span>
                </CommandItem>
              ))}
            </CommandGroup>
          )}
        </CommandList>

        <div className="border-t p-2 text-xs text-muted-foreground flex items-center gap-3">
          <span>
            <kbd className="px-1.5 py-0.5 bg-muted rounded mr-1">↑↓</kbd>{' '}
            navigate
          </span>
          <span>
            <kbd className="px-1.5 py-0.5 bg-muted rounded mr-1">↵</kbd> select
          </span>
          <span className="ml-auto">
            <kbd className="px-1.5 py-0.5 bg-muted rounded mr-1">esc</kbd> close
          </span>
        </div>
      </Command>
    </CommandDialog>
  )
}

// Hook for using command palette state
export function useCommandPalette() {
  const [open, setOpen] = useState(false)
  return { open, setOpen }
}
