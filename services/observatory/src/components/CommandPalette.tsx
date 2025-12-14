/**
 * CommandPalette Component
 *
 * Global search dialog using cmdk.
 * Triggered with ⌘K / Ctrl+K.
 */

import { useNavigate } from '@tanstack/react-router'
import { ArrowRight, Database, GitBranch } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import type { Asset } from '@/server/dagster.server'
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

interface CommandPaletteProps {
  assets: Array<Asset>
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function CommandPalette({
  assets,
  open,
  onOpenChange,
}: CommandPaletteProps) {
  const navigate = useNavigate()
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
      } else if (value === 'nav:dashboard') {
        navigate({ to: '/' })
      } else if (value === 'nav:assets') {
        navigate({ to: '/assets' })
      } else if (value === 'nav:graph') {
        navigate({ to: '/graph' })
      }
    },
    [navigate, onOpenChange],
  )

  if (!open) return null

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange} className="max-w-xl">
      <Command shouldFilter={true}>
        <CommandInput
          value={search}
          onValueChange={setSearch}
          placeholder="Search assets, navigate..."
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
            <CommandItem value="nav:graph" onSelect={handleSelect}>
              <GitBranch />
              <span>Go to Lineage Graph</span>
            </CommandItem>
          </CommandGroup>

          {assets.length > 0 && <CommandSeparator />}

          {assets.length > 0 && (
            <CommandGroup heading="Assets">
              {assets.slice(0, 20).map((asset) => (
                <CommandItem
                  key={asset.id}
                  value={`asset:${asset.keyPath}`}
                  onSelect={handleSelect}
                >
                  <Database />
                  <span className="truncate">{asset.keyPath}</span>
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
