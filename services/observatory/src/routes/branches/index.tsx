import { Link, createFileRoute, useRouter } from '@tanstack/react-router'
import {
  AlertTriangle,
  Clock,
  ExternalLink,
  GitBranch,
  GitCommit,
  GitMerge,
  Plus,
  RefreshCw,
  Trash2,
  Wifi,
  WifiOff,
} from 'lucide-react'
import { useState } from 'react'
import type { Branch, LogEntry, NessieConfig } from '@/server/nessie.server'
import { Badge } from '@/components/ui/badge'
import { Button, buttonVariants } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'
import { getEffectiveObservatorySettings } from '@/utils/effectiveSettings'
import {
  checkNessieConnection,
  createBranch,
  deleteBranch,
  getBranches,
  getCommits,
  mergeBranch,
} from '@/server/nessie.server'
import { useObservatorySettings } from '@/hooks/useObservatorySettings'

export const Route = createFileRoute('/branches/')({
  loader: async (): Promise<{
    connection: NessieConfig
    branches: Array<Branch> | { error: string }
  }> => {
    const settings = await getEffectiveObservatorySettings()
    const nessieUrl = settings.connections.nessieUrl
    const [connection, branches] = await Promise.all([
      checkNessieConnection({ data: { nessieUrl } }),
      getBranches({ data: { nessieUrl } }),
    ])
    return { connection, branches }
  },
  component: BranchesPage,
})

function BranchesPage() {
  const { connection, branches } = Route.useLoaderData()
  const router = useRouter()
  const { settings } = useObservatorySettings()
  const [selectedBranch, setSelectedBranch] = useState<string | null>(null)
  const [commits, setCommits] = useState<Array<LogEntry> | null>(null)
  const [loadingCommits, setLoadingCommits] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showMergeModal, setShowMergeModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState<Branch | null>(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  const isConnected = connection.connected
  const branchList = 'error' in branches ? [] : branches

  const handleSelectBranch = async (branchName: string) => {
    setSelectedBranch(branchName)
    setLoadingCommits(true)
    setCommits(null)
    try {
      const result = await getCommits({
        data: {
          branch: branchName,
          limit: 20,
          nessieUrl: settings.connections.nessieUrl,
        },
      })
      if ('error' in result) {
        setCommits([])
      } else {
        setCommits(result)
      }
    } catch {
      setCommits([])
    } finally {
      setLoadingCommits(false)
    }
  }

  const handleCreateBranch = async (name: string, fromBranch: string) => {
    setActionLoading(true)
    setActionError(null)
    try {
      const result = await createBranch({
        data: { name, fromBranch, nessieUrl: settings.connections.nessieUrl },
      })
      if ('error' in result) {
        setActionError(result.error)
      } else {
        setShowCreateModal(false)
        router.invalidate()
      }
    } catch (e) {
      setActionError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setActionLoading(false)
    }
  }

  const handleDeleteBranch = async (branch: Branch) => {
    setActionLoading(true)
    setActionError(null)
    try {
      const result = await deleteBranch({
        data: {
          name: branch.name,
          hash: branch.hash,
          nessieUrl: settings.connections.nessieUrl,
        },
      })
      if ('error' in result) {
        setActionError(result.error)
      } else {
        setShowDeleteModal(null)
        if (selectedBranch === branch.name) {
          setSelectedBranch(null)
          setCommits(null)
        }
        router.invalidate()
      }
    } catch (e) {
      setActionError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setActionLoading(false)
    }
  }

  const handleMergeBranch = async (
    fromBranch: string,
    intoBranch: string,
    message: string,
  ) => {
    setActionLoading(true)
    setActionError(null)
    try {
      const result = await mergeBranch({
        data: {
          fromBranch,
          intoBranch,
          message: message || undefined,
          nessieUrl: settings.connections.nessieUrl,
        },
      })
      if ('error' in result) {
        setActionError(result.error)
      } else {
        setShowMergeModal(false)
        router.invalidate()
        if (selectedBranch === intoBranch) {
          handleSelectBranch(intoBranch)
        }
      }
    } catch (e) {
      setActionError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setActionLoading(false)
    }
  }

  return (
    <div className="h-full overflow-auto">
      <div className="mx-auto w-full max-w-6xl px-4 py-6">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 mb-6">
          <div>
            <h1 className="text-3xl font-bold">Version Control</h1>
            <p className="text-muted-foreground">
              Git-like branching for your data lakehouse
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => setShowMergeModal(true)}
              disabled={!isConnected || branchList.length < 2}
            >
              <GitMerge className="size-4" />
              Merge
            </Button>
            <Button
              onClick={() => setShowCreateModal(true)}
              disabled={!isConnected}
              variant="outline"
            >
              <Plus className="size-4" />
              New Branch
            </Button>
            <Button variant="outline" onClick={() => router.invalidate()}>
              <RefreshCw className="size-4" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Connection Banner */}
        <NessieConnectionBanner connection={connection} />

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Branch List */}
          <div className="lg:col-span-1">
            <Card className="overflow-hidden">
              <CardHeader className="py-4">
                <CardTitle className="text-base flex items-center gap-2">
                  <GitBranch className="size-4 text-primary" />
                  Branches
                  <Badge
                    variant="secondary"
                    className="ml-auto text-muted-foreground"
                  >
                    {branchList.length}
                  </Badge>
                </CardTitle>
              </CardHeader>
              {!isConnected ? (
                <div className="p-8 text-center text-muted-foreground">
                  <WifiOff className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>Connect to Nessie to view branches</p>
                </div>
              ) : branchList.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground">
                  <GitBranch className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No branches found</p>
                </div>
              ) : (
                <div className="divide-y">
                  {branchList.map((branch) => (
                    <BranchRow
                      key={branch.name}
                      branch={branch}
                      isDefault={branch.name === connection.defaultBranch}
                      isSelected={selectedBranch === branch.name}
                      onSelect={() => handleSelectBranch(branch.name)}
                      onDelete={() => setShowDeleteModal(branch)}
                    />
                  ))}
                </div>
              )}
            </Card>
          </div>

          {/* Commit History */}
          <div className="lg:col-span-2">
            <Card className="overflow-hidden">
              <CardHeader className="py-4">
                <CardTitle className="text-base flex items-center gap-2">
                  <GitCommit className="size-4 text-primary" />
                  Commit History
                  {selectedBranch && (
                    <span className="text-sm text-muted-foreground ml-2">
                      • {selectedBranch}
                    </span>
                  )}
                </CardTitle>
              </CardHeader>
              {!selectedBranch ? (
                <div className="p-12 text-center text-muted-foreground">
                  <GitCommit className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p className="text-lg mb-1">Select a branch</p>
                  <p className="text-sm">
                    View the commit history for any branch
                  </p>
                </div>
              ) : loadingCommits ? (
                <div className="p-12 text-center text-muted-foreground">
                  <RefreshCw className="w-8 h-8 mx-auto mb-2 animate-spin" />
                  <p>Loading commits...</p>
                </div>
              ) : !commits || commits.length === 0 ? (
                <div className="p-12 text-center text-muted-foreground">
                  <GitCommit className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No commits found</p>
                </div>
              ) : (
                <div className="divide-y">
                  {commits.map((entry, index) => (
                    <CommitRow
                      key={entry.commitMeta.hash}
                      entry={entry}
                      isFirst={index === 0}
                    />
                  ))}
                </div>
              )}
            </Card>
          </div>
        </div>

        {/* Create Branch Modal */}
        {showCreateModal && (
          <CreateBranchModal
            branches={branchList}
            defaultBranch={connection.defaultBranch || 'main'}
            loading={actionLoading}
            error={actionError}
            onClose={() => {
              setShowCreateModal(false)
              setActionError(null)
            }}
            onCreate={handleCreateBranch}
          />
        )}

        {/* Merge Modal */}
        {showMergeModal && (
          <MergeBranchModal
            branches={branchList}
            loading={actionLoading}
            error={actionError}
            onClose={() => {
              setShowMergeModal(false)
              setActionError(null)
            }}
            onMerge={handleMergeBranch}
          />
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteModal && (
          <DeleteBranchModal
            branch={showDeleteModal}
            loading={actionLoading}
            error={actionError}
            onClose={() => {
              setShowDeleteModal(null)
              setActionError(null)
            }}
            onConfirm={() => handleDeleteBranch(showDeleteModal)}
          />
        )}
      </div>
    </div>
  )
}

// Connection Banner Component
function NessieConnectionBanner({ connection }: { connection: NessieConfig }) {
  if (connection.connected) {
    return (
      <Card className="mb-6 border-green-500/30 bg-green-500/5">
        <CardContent className="p-4 flex items-center gap-3">
          <Wifi className="size-5 text-green-400" />
          <span className="text-green-300">
            Connected to Nessie • Default branch:{' '}
            <strong>{connection.defaultBranch}</strong>
          </span>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="mb-6 border-yellow-500/30 bg-yellow-500/5">
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <WifiOff className="size-5 text-yellow-400" />
          <span className="text-yellow-300">Cannot connect to Nessie</span>
        </div>
        {connection.error && (
          <p className="mt-2 text-sm text-yellow-400/70">{connection.error}</p>
        )}
        <p className="mt-2 text-sm text-muted-foreground">
          Make sure Nessie is running:{' '}
          <code className="px-2 py-0.5 bg-muted rounded-none">
            docker compose up nessie
          </code>
        </p>
      </CardContent>
    </Card>
  )
}

// Branch Row Component
interface BranchRowProps {
  branch: Branch
  isDefault: boolean
  isSelected: boolean
  onSelect: () => void
  onDelete: () => void
}

function BranchRow({
  branch,
  isDefault,
  isSelected,
  onSelect,
  onDelete,
}: BranchRowProps) {
  return (
    <div
      className={`group p-4 cursor-pointer transition-colors ${
        isSelected ? 'bg-muted' : 'hover:bg-muted/50'
      }`}
      onClick={onSelect}
    >
      <div className="flex items-center gap-3">
        <GitBranch
          className={`w-4 h-4 ${isSelected ? 'text-primary' : 'text-muted-foreground'}`}
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium truncate">{branch.name}</span>
            {isDefault && (
              <Badge variant="secondary" className="text-muted-foreground">
                default
              </Badge>
            )}
            {branch.type === 'TAG' && <Badge variant="outline">tag</Badge>}
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            {branch.hash.slice(0, 12)}
          </p>
        </div>
        {!isDefault && (
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={(e) => {
              e.stopPropagation()
              onDelete()
            }}
            className="opacity-0 group-hover:opacity-100 transition-all"
            title="Delete branch"
          >
            <Trash2 className="w-4 h-4 text-destructive" />
          </Button>
        )}
        <Link
          to="/branches/$branchName"
          params={{ branchName: encodeURIComponent(branch.name) }}
          onClick={(e) => e.stopPropagation()}
          className={cn(
            'opacity-0 group-hover:opacity-100 transition-all',
            buttonVariants({ variant: 'ghost', size: 'icon-sm' }),
          )}
          title="View branch details"
        >
          <ExternalLink className="w-4 h-4" />
        </Link>
      </div>
    </div>
  )
}

// Commit Row Component
interface CommitRowProps {
  entry: LogEntry
  isFirst: boolean
}

function CommitRow({ entry, isFirst }: CommitRowProps) {
  const { commitMeta } = entry
  const date = new Date(commitMeta.commitTime)

  return (
    <div className="p-4 hover:bg-muted/50 transition-colors">
      <div className="flex items-start gap-3">
        <div className="mt-1">
          <div
            className={`w-3 h-3 rounded-full border-2 ${
              isFirst
                ? 'bg-primary border-primary'
                : 'bg-card border-muted-foreground'
            }`}
          />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-medium">
            {commitMeta.message || 'No commit message'}
          </p>
          <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
            <span className="font-mono text-primary">
              {commitMeta.hash.slice(0, 8)}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {formatRelativeTime(date)}
            </span>
            {commitMeta.authors.length > 0 && (
              <span>{commitMeta.authors.join(', ')}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// Create Branch Modal
interface CreateBranchModalProps {
  branches: Array<Branch>
  defaultBranch: string
  loading: boolean
  error: string | null
  onClose: () => void
  onCreate: (name: string, fromBranch: string) => void
}

function CreateBranchModal({
  branches,
  defaultBranch,
  loading,
  error,
  onClose,
  onCreate,
}: CreateBranchModalProps) {
  const [name, setName] = useState('')
  const [fromBranch, setFromBranch] = useState(defaultBranch)

  return (
    <Modal title="Create New Branch" onClose={onClose}>
      <div className="space-y-4">
        <div>
          <Label>Branch Name</Label>
          <Input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="feature/my-new-branch"
            autoFocus
          />
        </div>
        <div>
          <Label>From Branch</Label>
          <select
            value={fromBranch}
            onChange={(e) => setFromBranch(e.target.value)}
            className="w-full h-8 px-3 bg-input/30 border border-input text-xs outline-none"
          >
            {branches.map((b) => (
              <option key={b.name} value={b.name}>
                {b.name}
              </option>
            ))}
          </select>
        </div>

        {error && (
          <div className="p-3 bg-destructive/10 border border-destructive/30 flex items-center gap-2 text-destructive">
            <AlertTriangle className="w-4 h-4" />
            {error}
          </div>
        )}

        <div className="flex gap-3 justify-end pt-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={() => onCreate(name, fromBranch)}
            disabled={!name.trim() || loading}
          >
            {loading && <RefreshCw className="w-4 h-4 animate-spin" />}
            Create Branch
          </Button>
        </div>
      </div>
    </Modal>
  )
}

// Merge Branch Modal
interface MergeBranchModalProps {
  branches: Array<Branch>
  loading: boolean
  error: string | null
  onClose: () => void
  onMerge: (fromBranch: string, intoBranch: string, message: string) => void
}

function MergeBranchModal({
  branches,
  loading,
  error,
  onClose,
  onMerge,
}: MergeBranchModalProps) {
  const [fromBranch, setFromBranch] = useState(branches[0]?.name || '')
  const [intoBranch, setIntoBranch] = useState(
    branches[1]?.name || branches[0]?.name || '',
  )
  const [message, setMessage] = useState('')

  return (
    <Modal title="Merge Branches" onClose={onClose}>
      <div className="space-y-4">
        <div>
          <Label>From Branch</Label>
          <select
            value={fromBranch}
            onChange={(e) => setFromBranch(e.target.value)}
            className="w-full h-8 px-3 bg-input/30 border border-input text-xs outline-none"
          >
            {branches.map((b) => (
              <option key={b.name} value={b.name}>
                {b.name}
              </option>
            ))}
          </select>
        </div>
        <div className="text-center text-muted-foreground">
          <GitMerge className="w-5 h-5 mx-auto" />
        </div>
        <div>
          <Label>Into Branch</Label>
          <select
            value={intoBranch}
            onChange={(e) => setIntoBranch(e.target.value)}
            className="w-full h-8 px-3 bg-input/30 border border-input text-xs outline-none"
          >
            {branches.map((b) => (
              <option key={b.name} value={b.name}>
                {b.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <Label>Commit Message (optional)</Label>
          <Input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder={`Merge ${fromBranch} into ${intoBranch}`}
          />
        </div>

        {error && (
          <div className="p-3 bg-destructive/10 border border-destructive/30 flex items-center gap-2 text-destructive">
            <AlertTriangle className="w-4 h-4" />
            {error}
          </div>
        )}

        {fromBranch === intoBranch && (
          <div className="p-3 bg-yellow-500/10 border border-yellow-500/30 flex items-center gap-2 text-yellow-400">
            <AlertTriangle className="w-4 h-4" />
            Cannot merge a branch into itself
          </div>
        )}

        <div className="flex gap-3 justify-end pt-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={() => onMerge(fromBranch, intoBranch, message)}
            disabled={
              !fromBranch || !intoBranch || fromBranch === intoBranch || loading
            }
          >
            {loading && <RefreshCw className="w-4 h-4 animate-spin" />}
            Merge
          </Button>
        </div>
      </div>
    </Modal>
  )
}

// Delete Branch Modal
interface DeleteBranchModalProps {
  branch: Branch
  loading: boolean
  error: string | null
  onClose: () => void
  onConfirm: () => void
}

function DeleteBranchModal({
  branch,
  loading,
  error,
  onClose,
  onConfirm,
}: DeleteBranchModalProps) {
  return (
    <Modal title="Delete Branch" onClose={onClose}>
      <div className="space-y-4">
        <p>
          Are you sure you want to delete the branch{' '}
          <strong>{branch.name}</strong>?
        </p>
        <p className="text-sm text-muted-foreground">
          This action cannot be undone. All commits on this branch that are not
          merged will be lost.
        </p>

        {error && (
          <div className="p-3 bg-destructive/10 border border-destructive/30 flex items-center gap-2 text-destructive">
            <AlertTriangle className="w-4 h-4" />
            {error}
          </div>
        )}

        <div className="flex gap-3 justify-end pt-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={onConfirm} disabled={loading} variant="destructive">
            {loading && <RefreshCw className="w-4 h-4 animate-spin" />}
            Delete Branch
          </Button>
        </div>
      </div>
    </Modal>
  )
}

// Modal Component
interface ModalProps {
  title: string
  children: React.ReactNode
  onClose: () => void
}

function Modal({ title, children, onClose }: ModalProps) {
  return (
    <Dialog
      open={true}
      onOpenChange={(open) => {
        if (!open) onClose()
      }}
    >
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>
        {children}
      </DialogContent>
    </Dialog>
  )
}

// Utility function
function formatRelativeTime(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}
