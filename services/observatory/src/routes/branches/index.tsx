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
  X,
} from 'lucide-react'
import { useState } from 'react'
import type { Branch, LogEntry, NessieConfig } from '@/server/nessie.server'
import {
  checkNessieConnection,
  createBranch,
  deleteBranch,
  getBranches,
  getCommits,
  mergeBranch,
} from '@/server/nessie.server'

export const Route = createFileRoute('/branches/')({
  loader: async (): Promise<{
    connection: NessieConfig
    branches: Array<Branch> | { error: string }
  }> => {
    const [connection, branches] = await Promise.all([
      checkNessieConnection(),
      getBranches(),
    ])
    return { connection, branches }
  },
  component: BranchesPage,
})

function BranchesPage() {
  const { connection, branches } = Route.useLoaderData()
  const router = useRouter()
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
        data: { branch: branchName, limit: 20 },
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
      const result = await createBranch({ data: { name, fromBranch } })
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
        data: { name: branch.name, hash: branch.hash },
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
        data: { fromBranch, intoBranch, message: message || undefined },
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
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Version Control</h1>
          <p className="text-slate-400">
            Git-like branching for your data lakehouse
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowMergeModal(true)}
            disabled={!isConnected || branchList.length < 2}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:bg-slate-600 disabled:cursor-not-allowed rounded-lg transition-colors"
          >
            <GitMerge className="w-4 h-4" />
            Merge
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            disabled={!isConnected}
            className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-600 disabled:cursor-not-allowed rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Branch
          </button>
          <button
            onClick={() => router.invalidate()}
            className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Connection Banner */}
      <NessieConnectionBanner connection={connection} />

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Branch List */}
        <div className="lg:col-span-1">
          <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
            <div className="p-4 border-b border-slate-700">
              <h2 className="font-semibold flex items-center gap-2">
                <GitBranch className="w-5 h-5 text-cyan-400" />
                Branches
                <span className="ml-auto text-sm text-slate-400 bg-slate-700 px-2 py-0.5 rounded">
                  {branchList.length}
                </span>
              </h2>
            </div>
            {!isConnected ? (
              <div className="p-8 text-center text-slate-500">
                <WifiOff className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>Connect to Nessie to view branches</p>
              </div>
            ) : branchList.length === 0 ? (
              <div className="p-8 text-center text-slate-500">
                <GitBranch className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No branches found</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-700">
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
          </div>
        </div>

        {/* Commit History */}
        <div className="lg:col-span-2">
          <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
            <div className="p-4 border-b border-slate-700">
              <h2 className="font-semibold flex items-center gap-2">
                <GitCommit className="w-5 h-5 text-cyan-400" />
                Commit History
                {selectedBranch && (
                  <span className="text-sm text-cyan-400 ml-2">
                    • {selectedBranch}
                  </span>
                )}
              </h2>
            </div>
            {!selectedBranch ? (
              <div className="p-12 text-center text-slate-500">
                <GitCommit className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p className="text-lg mb-1">Select a branch</p>
                <p className="text-sm">
                  View the commit history for any branch
                </p>
              </div>
            ) : loadingCommits ? (
              <div className="p-12 text-center text-slate-500">
                <RefreshCw className="w-8 h-8 mx-auto mb-2 animate-spin" />
                <p>Loading commits...</p>
              </div>
            ) : !commits || commits.length === 0 ? (
              <div className="p-12 text-center text-slate-500">
                <GitCommit className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No commits found</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-700">
                {commits.map((entry, index) => (
                  <CommitRow
                    key={entry.commitMeta.hash}
                    entry={entry}
                    isFirst={index === 0}
                  />
                ))}
              </div>
            )}
          </div>
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
  )
}

// Connection Banner Component
function NessieConnectionBanner({ connection }: { connection: NessieConfig }) {
  if (connection.connected) {
    return (
      <div className="mb-6 p-4 bg-green-900/20 border border-green-700/50 rounded-xl flex items-center gap-3">
        <Wifi className="w-5 h-5 text-green-400" />
        <span className="text-green-300">
          Connected to Nessie • Default branch:{' '}
          <strong>{connection.defaultBranch}</strong>
        </span>
      </div>
    )
  }

  return (
    <div className="mb-6 p-4 bg-yellow-900/20 border border-yellow-700/50 rounded-xl">
      <div className="flex items-center gap-3">
        <WifiOff className="w-5 h-5 text-yellow-400" />
        <span className="text-yellow-300">Cannot connect to Nessie</span>
      </div>
      {connection.error && (
        <p className="mt-2 text-sm text-yellow-400/70">{connection.error}</p>
      )}
      <p className="mt-2 text-sm text-slate-500">
        Make sure Nessie is running:{' '}
        <code className="px-2 py-0.5 bg-slate-800 rounded">
          docker compose up nessie
        </code>
      </p>
    </div>
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
        isSelected ? 'bg-cyan-900/30' : 'hover:bg-slate-700/50'
      }`}
      onClick={onSelect}
    >
      <div className="flex items-center gap-3">
        <GitBranch
          className={`w-4 h-4 ${isSelected ? 'text-cyan-400' : 'text-slate-500'}`}
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium truncate">{branch.name}</span>
            {isDefault && (
              <span className="text-xs bg-cyan-600 text-white px-1.5 py-0.5 rounded">
                default
              </span>
            )}
            {branch.type === 'TAG' && (
              <span className="text-xs bg-purple-600 text-white px-1.5 py-0.5 rounded">
                tag
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 font-mono mt-0.5">
            {branch.hash.slice(0, 12)}
          </p>
        </div>
        {!isDefault && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              onDelete()
            }}
            className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-600/20 rounded transition-all"
            title="Delete branch"
          >
            <Trash2 className="w-4 h-4 text-red-400" />
          </button>
        )}
        <Link
          to="/branches/$branchName"
          params={{ branchName: encodeURIComponent(branch.name) }}
          onClick={(e) => e.stopPropagation()}
          className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-cyan-600/20 rounded transition-all"
          title="View branch details"
        >
          <ExternalLink className="w-4 h-4 text-cyan-400" />
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
    <div className="p-4 hover:bg-slate-700/30 transition-colors">
      <div className="flex items-start gap-3">
        <div className="mt-1">
          <div
            className={`w-3 h-3 rounded-full border-2 ${
              isFirst
                ? 'bg-cyan-400 border-cyan-400'
                : 'bg-slate-800 border-slate-500'
            }`}
          />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-slate-200">
            {commitMeta.message || 'No commit message'}
          </p>
          <div className="flex items-center gap-4 mt-2 text-sm text-slate-500">
            <span className="font-mono text-cyan-400">
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
          <label className="block text-sm font-medium text-slate-300 mb-1">
            Branch Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="feature/my-new-branch"
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
            autoFocus
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">
            From Branch
          </label>
          <select
            value={fromBranch}
            onChange={(e) => setFromBranch(e.target.value)}
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
          >
            {branches.map((b) => (
              <option key={b.name} value={b.name}>
                {b.name}
              </option>
            ))}
          </select>
        </div>

        {error && (
          <div className="p-3 bg-red-900/30 border border-red-700/50 rounded-lg flex items-center gap-2 text-red-300">
            <AlertTriangle className="w-4 h-4" />
            {error}
          </div>
        )}

        <div className="flex gap-3 justify-end pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={() => onCreate(name, fromBranch)}
            disabled={!name.trim() || loading}
            className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-600 disabled:cursor-not-allowed rounded-lg transition-colors"
          >
            {loading && <RefreshCw className="w-4 h-4 animate-spin" />}
            Create Branch
          </button>
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
          <label className="block text-sm font-medium text-slate-300 mb-1">
            From Branch
          </label>
          <select
            value={fromBranch}
            onChange={(e) => setFromBranch(e.target.value)}
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
          >
            {branches.map((b) => (
              <option key={b.name} value={b.name}>
                {b.name}
              </option>
            ))}
          </select>
        </div>
        <div className="text-center text-slate-500">
          <GitMerge className="w-5 h-5 mx-auto" />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">
            Into Branch
          </label>
          <select
            value={intoBranch}
            onChange={(e) => setIntoBranch(e.target.value)}
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
          >
            {branches.map((b) => (
              <option key={b.name} value={b.name}>
                {b.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">
            Commit Message (optional)
          </label>
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder={`Merge ${fromBranch} into ${intoBranch}`}
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
          />
        </div>

        {error && (
          <div className="p-3 bg-red-900/30 border border-red-700/50 rounded-lg flex items-center gap-2 text-red-300">
            <AlertTriangle className="w-4 h-4" />
            {error}
          </div>
        )}

        {fromBranch === intoBranch && (
          <div className="p-3 bg-yellow-900/30 border border-yellow-700/50 rounded-lg flex items-center gap-2 text-yellow-300">
            <AlertTriangle className="w-4 h-4" />
            Cannot merge a branch into itself
          </div>
        )}

        <div className="flex gap-3 justify-end pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={() => onMerge(fromBranch, intoBranch, message)}
            disabled={
              !fromBranch || !intoBranch || fromBranch === intoBranch || loading
            }
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:bg-slate-600 disabled:cursor-not-allowed rounded-lg transition-colors"
          >
            {loading && <RefreshCw className="w-4 h-4 animate-spin" />}
            Merge
          </button>
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
        <p className="text-slate-300">
          Are you sure you want to delete the branch{' '}
          <strong className="text-white">{branch.name}</strong>?
        </p>
        <p className="text-sm text-slate-500">
          This action cannot be undone. All commits on this branch that are not
          merged will be lost.
        </p>

        {error && (
          <div className="p-3 bg-red-900/30 border border-red-700/50 rounded-lg flex items-center gap-2 text-red-300">
            <AlertTriangle className="w-4 h-4" />
            {error}
          </div>
        )}

        <div className="flex gap-3 justify-end pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-500 disabled:bg-slate-600 disabled:cursor-not-allowed rounded-lg transition-colors"
          >
            {loading && <RefreshCw className="w-4 h-4 animate-spin" />}
            Delete Branch
          </button>
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
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative bg-slate-800 border border-slate-700 rounded-xl shadow-2xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <h3 className="text-lg font-semibold">{title}</h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-slate-700 rounded transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-4">{children}</div>
      </div>
    </div>
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
