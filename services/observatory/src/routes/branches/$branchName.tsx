import { Link, createFileRoute, useRouter } from '@tanstack/react-router'
import {
  ArrowLeft,
  Clock,
  Database,
  GitBranch,
  GitCommit,
  GitCompare,
  RefreshCw,
  Table2,
} from 'lucide-react'
import { useState } from 'react'
import type { Branch, LogEntry } from '@/server/nessie.server'
import { Badge } from '@/components/ui/badge'
import { Button, buttonVariants } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'
import {
  compareBranches,
  getBranch,
  getCommits,
  getContents,
} from '@/server/nessie.server'

export const Route = createFileRoute('/branches/$branchName')({
  loader: async ({
    params,
  }): Promise<{
    branch: Branch | { error: string }
    commits: Array<LogEntry> | { error: string }
    contents: Array<object> | { error: string }
  }> => {
    const branchName = decodeURIComponent(params.branchName)
    const [branch, commits, contents] = await Promise.all([
      getBranch({ data: branchName }),
      getCommits({ data: { branch: branchName, limit: 50 } }),
      getContents({ data: { branch: branchName } }),
    ])
    return { branch, commits, contents }
  },
  component: BranchDetailPage,
})

interface ContentEntry {
  name: { elements: Array<string> }
  type: string
}

function BranchDetailPage() {
  const { branchName } = Route.useParams()
  const { branch, commits, contents } = Route.useLoaderData()
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<
    'commits' | 'contents' | 'compare'
  >('commits')
  const [compareToBranch, setCompareToBranch] = useState<string>('')
  const [diffData, setDiffData] = useState<object | null>(null)
  const [loadingDiff, setLoadingDiff] = useState(false)

  const decodedBranchName = decodeURIComponent(branchName)
  const hasError = 'error' in branch
  const commitList = 'error' in commits ? [] : commits
  const contentList = (
    'error' in contents ? [] : contents
  ) as Array<ContentEntry>

  const handleCompare = async (targetBranch: string) => {
    setCompareToBranch(targetBranch)
    setLoadingDiff(true)
    try {
      const result = await compareBranches({
        data: { fromBranch: decodedBranchName, toBranch: targetBranch },
      })
      setDiffData(result)
    } catch {
      setDiffData(null)
    } finally {
      setLoadingDiff(false)
    }
  }

  if (hasError) {
    return (
      <div className="p-6">
        <Link
          to="/branches"
          className={cn(
            buttonVariants({ variant: 'ghost', size: 'sm' }),
            'gap-2 mb-6',
          )}
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Branches
        </Link>
        <Card className="border-destructive/30 bg-destructive/10">
          <CardContent className="p-8 text-center">
            <GitBranch className="w-12 h-12 mx-auto mb-4 text-destructive opacity-60" />
            <h2 className="text-xl font-semibold mb-2">Branch Not Found</h2>
            <p className="text-muted-foreground">{branch.error}</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <Link
          to="/branches"
          className={cn(
            buttonVariants({ variant: 'ghost', size: 'sm' }),
            'gap-2 mb-4',
          )}
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Branches
        </Link>
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <GitBranch className="w-6 h-6 text-primary" />
              <h1 className="text-3xl font-bold">{decodedBranchName}</h1>
              {branch.type === 'TAG' && <Badge variant="outline">tag</Badge>}
            </div>
            <p className="text-muted-foreground mt-2 font-mono text-sm">
              Hash: {branch.hash}
            </p>
          </div>
          <Button variant="outline" onClick={() => router.invalidate()}>
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <StatCard
          icon={<GitCommit className="w-5 h-5 text-cyan-400" />}
          label="Commits"
          value={commitList.length.toString()}
          subtitle="In history"
        />
        <StatCard
          icon={<Table2 className="w-5 h-5 text-green-400" />}
          label="Tables"
          value={contentList
            .filter((c) => c.type === 'ICEBERG_TABLE')
            .length.toString()}
          subtitle="Iceberg tables"
        />
        <StatCard
          icon={<Database className="w-5 h-5 text-purple-400" />}
          label="Total Entries"
          value={contentList.length.toString()}
          subtitle="Objects in catalog"
        />
      </div>

      <Tabs
        value={activeTab}
        onValueChange={(value) =>
          setActiveTab(value as 'commits' | 'contents' | 'compare')
        }
      >
        <TabsList>
          <TabsTrigger value="commits">
            <GitCommit className="size-4" />
            Commits
            <Badge variant="secondary" className="text-muted-foreground ml-1">
              {commitList.length}
            </Badge>
          </TabsTrigger>
          <TabsTrigger value="contents">
            <Table2 className="size-4" />
            Contents
            <Badge variant="secondary" className="text-muted-foreground ml-1">
              {contentList.length}
            </Badge>
          </TabsTrigger>
          <TabsTrigger value="compare">
            <GitCompare className="size-4" />
            Compare
          </TabsTrigger>
        </TabsList>

        <Card className="overflow-hidden">
          <TabsContent value="commits">
            <CommitsTab commits={commitList} />
          </TabsContent>
          <TabsContent value="contents">
            <ContentsTab contents={contentList} />
          </TabsContent>
          <TabsContent value="compare">
            <CompareTab
              branchName={decodedBranchName}
              compareToBranch={compareToBranch}
              diffData={diffData}
              loading={loadingDiff}
              onCompare={handleCompare}
            />
          </TabsContent>
        </Card>
      </Tabs>
    </div>
  )
}

// Stat Card Component
interface StatCardProps {
  icon: React.ReactNode
  label: string
  value: string
  subtitle: string
}

function StatCard({ icon, label, value, subtitle }: StatCardProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription className="flex items-center gap-2">
          {icon}
          <span>{label}</span>
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-0">
        <CardTitle className="text-2xl">{value}</CardTitle>
        <div className="text-xs text-muted-foreground mt-1">{subtitle}</div>
      </CardContent>
    </Card>
  )
}

// Commits Tab
function CommitsTab({ commits }: { commits: Array<LogEntry> }) {
  if (commits.length === 0) {
    return (
      <div className="p-12 text-center text-slate-500">
        <GitCommit className="w-12 h-12 mx-auto mb-3 opacity-30" />
        <p>No commits found</p>
      </div>
    )
  }

  return (
    <div className="divide-y divide-slate-700">
      {commits.map((entry, index) => {
        const { commitMeta } = entry
        const date = new Date(commitMeta.commitTime)

        return (
          <div
            key={commitMeta.hash}
            className="p-4 hover:bg-slate-700/30 transition-colors"
          >
            <div className="flex items-start gap-3">
              <div className="mt-1">
                <div
                  className={`w-3 h-3 rounded-full border-2 ${
                    index === 0
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
                {commitMeta.parentCommitHashes.length > 0 && (
                  <div className="mt-1 text-xs text-slate-600">
                    Parent: {commitMeta.parentCommitHashes[0].slice(0, 8)}
                  </div>
                )}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

// Contents Tab
function ContentsTab({ contents }: { contents: Array<ContentEntry> }) {
  if (contents.length === 0) {
    return (
      <div className="p-12 text-center text-slate-500">
        <Table2 className="w-12 h-12 mx-auto mb-3 opacity-30" />
        <p>No contents found</p>
        <p className="text-sm mt-1">Tables and namespaces will appear here</p>
      </div>
    )
  }

  // Group by namespace
  const grouped: Record<string, Array<ContentEntry>> = {}
  for (const entry of contents) {
    const namespace = entry.name.elements.slice(0, -1).join('.') || 'default'
    if (!grouped[namespace]) grouped[namespace] = []
    grouped[namespace].push(entry)
  }

  return (
    <div className="divide-y divide-slate-700">
      {Object.entries(grouped).map(([namespace, entries]) => (
        <div key={namespace}>
          <div className="px-4 py-2 bg-slate-850 border-b border-slate-700">
            <span className="text-sm font-medium text-slate-400">
              {namespace}
            </span>
          </div>
          {entries.map((entry) => {
            const tableName =
              entry.name.elements[entry.name.elements.length - 1]
            const isTable = entry.type === 'ICEBERG_TABLE'
            const isView = entry.type === 'ICEBERG_VIEW'

            return (
              <div
                key={entry.name.elements.join('.')}
                className="px-4 py-3 hover:bg-slate-700/30 transition-colors flex items-center gap-3"
              >
                {isTable ? (
                  <Table2 className="w-4 h-4 text-green-400" />
                ) : isView ? (
                  <Database className="w-4 h-4 text-blue-400" />
                ) : (
                  <Database className="w-4 h-4 text-slate-500" />
                )}
                <span className="font-mono">{tableName}</span>
                <span className="text-xs text-slate-500 ml-auto px-2 py-0.5 bg-slate-700 rounded">
                  {entry.type.replace('ICEBERG_', '').toLowerCase()}
                </span>
              </div>
            )
          })}
        </div>
      ))}
    </div>
  )
}

// Compare Tab
interface CompareTabProps {
  branchName: string
  compareToBranch: string
  diffData: object | null
  loading: boolean
  onCompare: (branch: string) => void
}

function CompareTab({
  branchName,
  compareToBranch,
  diffData,
  loading,
  onCompare,
}: CompareTabProps) {
  const [inputBranch, setInputBranch] = useState(compareToBranch)

  return (
    <div className="p-6">
      <div className="flex gap-3 mb-6">
        <input
          type="text"
          value={inputBranch}
          onChange={(e) => setInputBranch(e.target.value)}
          placeholder="Enter branch name to compare"
          className="flex-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
        />
        <button
          onClick={() => onCompare(inputBranch)}
          disabled={!inputBranch.trim() || loading}
          className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-600 disabled:cursor-not-allowed rounded-lg transition-colors"
        >
          {loading ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <GitCompare className="w-4 h-4" />
          )}
          Compare
        </button>
      </div>

      {compareToBranch && !loading && diffData && !('error' in diffData) && (
        <div>
          <div className="mb-4 p-3 bg-slate-700 rounded-lg">
            <div className="text-sm text-slate-400">Comparing</div>
            <div className="flex items-center gap-2 mt-1">
              <span className="font-mono text-cyan-400">{branchName}</span>
              <span className="text-slate-500">→</span>
              <span className="font-mono text-purple-400">
                {compareToBranch}
              </span>
            </div>
          </div>
          <pre className="bg-slate-900 rounded-lg p-4 overflow-auto text-sm text-slate-300">
            {JSON.stringify(diffData, null, 2)}
          </pre>
        </div>
      )}

      {compareToBranch && !loading && diffData && 'error' in diffData && (
        <div className="p-4 bg-red-900/30 border border-red-700/50 rounded-lg text-red-300">
          {(diffData as { error: string }).error}
        </div>
      )}

      {!compareToBranch && !loading && (
        <div className="text-center text-slate-500 py-12">
          <GitCompare className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p>
            Enter a branch name to compare with <strong>{branchName}</strong>
          </p>
        </div>
      )}
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
