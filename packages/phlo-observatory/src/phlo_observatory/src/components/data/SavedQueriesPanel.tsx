/**
 * Saved Queries Panel component
 *
 * Sidebar panel displaying saved queries with actions to run, edit, delete.
 */

import {
  ChevronDown,
  ChevronRight,
  Copy,
  Database,
  MoreHorizontal,
  Pencil,
  Play,
  Search,
  Trash2,
} from 'lucide-react'
import { useState } from 'react'

import type { SavedQuery } from '@/lib/savedQueries'
import { Button } from '@/components/ui/button'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Input } from '@/components/ui/input'
import { useSavedQueries } from '@/hooks/useSavedQueries'
import { cn } from '@/lib/utils'

interface SavedQueriesPanelProps {
  onRunQuery: (query: string, branch?: string) => void
  className?: string
}

export function SavedQueriesPanel({
  onRunQuery,
  className,
}: SavedQueriesPanelProps) {
  const { queries, deleteQuery, updateQuery } = useSavedQueries()
  const [searchTerm, setSearchTerm] = useState('')
  const [isOpen, setIsOpen] = useState(true)
  const [editingQuery, setEditingQuery] = useState<SavedQuery | null>(null)
  const [editName, setEditName] = useState('')

  // Filter queries by search term
  const filteredQueries = queries.filter(
    (q) =>
      q.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      q.query.toLowerCase().includes(searchTerm.toLowerCase()) ||
      q.tags?.some((t) => t.toLowerCase().includes(searchTerm.toLowerCase())),
  )

  // Group by tags (use 'Uncategorized' for queries without tags)
  const groupedQueries = filteredQueries.reduce(
    (acc, query) => {
      const tag = query.tags?.[0] ?? 'Uncategorized'
      if (!acc[tag]) acc[tag] = []
      acc[tag].push(query)
      return acc
    },
    {} as Record<string, Array<SavedQuery>>,
  )

  const handleCopyQuery = (query: string) => {
    navigator.clipboard.writeText(query)
  }

  const handleEditQuery = (query: SavedQuery) => {
    setEditingQuery(query)
    setEditName(query.name)
  }

  const handleSaveEdit = () => {
    if (editingQuery && editName.trim()) {
      updateQuery(editingQuery.id, { name: editName.trim() })
      setEditingQuery(null)
    }
  }

  const handleDeleteQuery = (id: string) => {
    deleteQuery(id)
  }

  return (
    <div className={cn('flex flex-col', className)}>
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger
          render={
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-start gap-2 px-2"
            >
              {isOpen ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
              <Database className="w-4 h-4" />
              <span className="font-medium">Saved Queries</span>
              <span className="ml-auto text-xs text-muted-foreground">
                {queries.length}
              </span>
            </Button>
          }
        />

        <CollapsibleContent className="pl-4 pt-2">
          {/* Search */}
          <div className="relative mb-2">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3 h-3 text-muted-foreground" />
            <Input
              placeholder="Search queries..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="h-7 pl-7 text-xs"
            />
          </div>

          {/* Queries list */}
          <div className="space-y-1 max-h-64 overflow-y-auto">
            {Object.entries(groupedQueries).map(([tag, tagQueries]) => (
              <div key={tag} className="space-y-0.5">
                <div className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide px-2 py-1">
                  {tag}
                </div>
                {tagQueries.map((query) => (
                  <div
                    key={query.id}
                    className="flex items-center gap-1 px-2 py-1 hover:bg-muted group"
                  >
                    <button
                      className="flex-1 text-left text-xs truncate"
                      onClick={() => onRunQuery(query.query, query.branch)}
                    >
                      {query.name}
                    </button>

                    <DropdownMenu>
                      <DropdownMenuTrigger
                        render={
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            className="opacity-0 group-hover:opacity-100 h-5 w-5"
                          >
                            <MoreHorizontal className="w-3 h-3" />
                          </Button>
                        }
                      />
                      <DropdownMenuContent align="end" className="w-40">
                        <DropdownMenuItem
                          onClick={() => onRunQuery(query.query, query.branch)}
                        >
                          <Play className="w-3 h-3 mr-2" />
                          Run
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => handleCopyQuery(query.query)}
                        >
                          <Copy className="w-3 h-3 mr-2" />
                          Copy SQL
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => handleEditQuery(query)}
                        >
                          <Pencil className="w-3 h-3 mr-2" />
                          Rename
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => handleDeleteQuery(query.id)}
                          className="text-destructive"
                        >
                          <Trash2 className="w-3 h-3 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                ))}
              </div>
            ))}

            {filteredQueries.length === 0 && (
              <div className="text-xs text-muted-foreground text-center py-4">
                {searchTerm ? 'No matching queries' : 'No saved queries yet'}
              </div>
            )}
          </div>
        </CollapsibleContent>
      </Collapsible>

      {/* Edit dialog */}
      <Dialog
        open={editingQuery !== null}
        onOpenChange={(open) => !open && setEditingQuery(null)}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Rename Query</DialogTitle>
          </DialogHeader>
          <Input
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            placeholder="Query name"
            className="mt-2"
          />
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setEditingQuery(null)}>
              Cancel
            </Button>
            <Button onClick={handleSaveEdit} disabled={!editName.trim()}>
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
