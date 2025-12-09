/**
 * CommandPalette Component
 *
 * Global search dialog using cmdk.
 * Triggered with ⌘K / Ctrl+K.
 */

import { useNavigate } from '@tanstack/react-router'
import { Command } from 'cmdk'
import { ArrowRight, Database, GitBranch, Search } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import type { Asset } from '@/server/dagster.server'

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
    <div className="fixed inset-0 z-50 bg-black/50 flex items-start justify-center pt-[20vh]">
      <Command
        className="w-full max-w-xl bg-slate-800 rounded-xl border border-slate-700 shadow-2xl overflow-hidden"
        shouldFilter={true}
        onKeyDown={(e) => {
          if (e.key === 'Escape') {
            onOpenChange(false)
          }
        }}
      >
        <div className="flex items-center gap-2 px-4 border-b border-slate-700">
          <Search className="w-5 h-5 text-slate-500" />
          <Command.Input
            value={search}
            onValueChange={setSearch}
            placeholder="Search assets, navigate..."
            className="w-full py-4 bg-transparent text-slate-100 placeholder-slate-500 outline-none text-lg"
            autoFocus
          />
          <kbd className="px-2 py-1 text-xs font-medium bg-slate-700 text-slate-400 rounded">
            Esc
          </kbd>
        </div>

        <Command.List className="max-h-80 overflow-y-auto p-2">
          <Command.Empty className="py-6 text-center text-slate-500">
            No results found.
          </Command.Empty>

          {/* Navigation */}
          <Command.Group
            heading="Navigation"
            className="text-xs text-slate-500 px-2 py-1.5 font-medium"
          >
            <Command.Item
              value="nav:dashboard"
              onSelect={handleSelect}
              className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-300 cursor-pointer data-[selected=true]:bg-cyan-600/20 data-[selected=true]:text-cyan-300"
            >
              <ArrowRight className="w-4 h-4" />
              <span>Go to Dashboard</span>
            </Command.Item>
            <Command.Item
              value="nav:assets"
              onSelect={handleSelect}
              className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-300 cursor-pointer data-[selected=true]:bg-cyan-600/20 data-[selected=true]:text-cyan-300"
            >
              <Database className="w-4 h-4" />
              <span>Go to Assets</span>
            </Command.Item>
            <Command.Item
              value="nav:graph"
              onSelect={handleSelect}
              className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-300 cursor-pointer data-[selected=true]:bg-cyan-600/20 data-[selected=true]:text-cyan-300"
            >
              <GitBranch className="w-4 h-4" />
              <span>Go to Lineage Graph</span>
            </Command.Item>
          </Command.Group>

          {/* Assets */}
          {assets.length > 0 && (
            <Command.Group
              heading="Assets"
              className="text-xs text-slate-500 px-2 py-1.5 font-medium mt-2"
            >
              {assets.slice(0, 20).map((asset) => (
                <Command.Item
                  key={asset.id}
                  value={`asset:${asset.keyPath}`}
                  onSelect={handleSelect}
                  className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-300 cursor-pointer data-[selected=true]:bg-cyan-600/20 data-[selected=true]:text-cyan-300"
                >
                  <Database className="w-4 h-4 text-cyan-400" />
                  <div className="flex-1 min-w-0">
                    <div className="truncate">{asset.keyPath}</div>
                    {asset.description && (
                      <div className="text-xs text-slate-500 truncate">
                        {asset.description}
                      </div>
                    )}
                  </div>
                  {asset.groupName && (
                    <span className="text-xs bg-slate-700 text-slate-400 px-1.5 py-0.5 rounded">
                      {asset.groupName}
                    </span>
                  )}
                </Command.Item>
              ))}
            </Command.Group>
          )}

          {/* Graph Focus Actions */}
          {search && assets.length > 0 && (
            <Command.Group
              heading="Focus in Graph"
              className="text-xs text-slate-500 px-2 py-1.5 font-medium mt-2"
            >
              {assets.slice(0, 5).map((asset) => (
                <Command.Item
                  key={`graph-${asset.id}`}
                  value={`graph:${asset.keyPath}`}
                  onSelect={handleSelect}
                  className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-300 cursor-pointer data-[selected=true]:bg-cyan-600/20 data-[selected=true]:text-cyan-300"
                >
                  <GitBranch className="w-4 h-4 text-purple-400" />
                  <span>Show {asset.keyPath} in graph</span>
                </Command.Item>
              ))}
            </Command.Group>
          )}
        </Command.List>

        <div className="border-t border-slate-700 px-4 py-2 text-xs text-slate-500 flex items-center gap-4">
          <span>
            <kbd className="px-1.5 py-0.5 bg-slate-700 rounded mr-1">↑↓</kbd>{' '}
            navigate
          </span>
          <span>
            <kbd className="px-1.5 py-0.5 bg-slate-700 rounded mr-1">↵</kbd>{' '}
            select
          </span>
          <span>
            <kbd className="px-1.5 py-0.5 bg-slate-700 rounded mr-1">esc</kbd>{' '}
            close
          </span>
        </div>
      </Command>
    </div>
  )
}

// Hook for using command palette state
export function useCommandPalette() {
  const [open, setOpen] = useState(false)
  return { open, setOpen }
}
