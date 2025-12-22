/**
 * Save Query Dialog component
 *
 * Modal dialog for saving a SQL query with name, description, and tags.
 */

import { Save } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useSavedQueries } from '@/hooks/useSavedQueries'

interface SaveQueryDialogProps {
  query: string
  branch?: string
  onSaved?: (queryId: string) => void
  trigger?: React.ReactElement
}

export function SaveQueryDialog({
  query,
  branch,
  onSaved,
  trigger,
}: SaveQueryDialogProps) {
  const { saveQuery } = useSavedQueries()
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [tagsInput, setTagsInput] = useState('')

  const handleSave = () => {
    if (!name.trim() || !query.trim()) return

    const tags = tagsInput
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean)

    const saved = saveQuery({
      name: name.trim(),
      query: query.trim(),
      description: description.trim() || undefined,
      tags: tags.length > 0 ? tags : undefined,
      branch,
    })

    setOpen(false)
    setName('')
    setDescription('')
    setTagsInput('')
    onSaved?.(saved.id)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        render={
          trigger ?? (
            <Button variant="outline" size="sm" disabled={!query.trim()}>
              <Save className="w-4 h-4 mr-2" />
              Save Query
            </Button>
          )
        }
      />
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Save Query</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="space-y-2">
            <Label htmlFor="query-name">Name</Label>
            <Input
              id="query-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My useful query"
              autoFocus
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="query-description">Description (optional)</Label>
            <Textarea
              id="query-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What does this query do?"
              className="h-20 resize-none"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="query-tags">Tags (comma-separated)</Label>
            <Input
              id="query-tags"
              value={tagsInput}
              onChange={(e) => setTagsInput(e.target.value)}
              placeholder="analytics, daily, metrics"
            />
          </div>

          <div className="space-y-2">
            <Label>Query Preview</Label>
            <div className="bg-muted p-2 text-xs font-mono max-h-24 overflow-y-auto whitespace-pre-wrap break-all">
              {query || 'No query'}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={!name.trim() || !query.trim()}>
            Save
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
