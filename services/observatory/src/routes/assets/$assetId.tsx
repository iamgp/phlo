import { Link, createFileRoute } from '@tanstack/react-router'
import {
  ArrowLeft,
  Calendar,
  Clock,
  Columns2,
  Database,
  GitBranch,
  History,
  Info,
  Shield,
  Table,
} from 'lucide-react'
import { useState } from 'react'
import type { AssetDetails } from '@/server/dagster.server'
import type { QualityCheck } from '@/server/quality.server'
import { DataPreview } from '@/components/data/DataPreview'
import { DataJourney } from '@/components/provenance/DataJourney'
import { MaterializationTimeline } from '@/components/provenance/MaterializationTimeline'
import { getAssetDetails } from '@/server/dagster.server'
import { getAssetChecks } from '@/server/quality.server'

export const Route = createFileRoute('/assets/$assetId')({
  loader: async ({ params }) => {
    const asset = await getAssetDetails({ data: params.assetId })

    // Fetch checks but don't fail the whole page if it errors
    let checks: Array<QualityCheck> | { error: string } = {
      error: 'Not loaded',
    }
    try {
      checks = await getAssetChecks({
        data: { assetKey: params.assetId.split('/') },
      })
    } catch {
      // Quality checks are optional, don't block page load
      checks = { error: 'Failed to load checks' }
    }

    return { asset, checks }
  },
  component: AssetDetailPage,
})

type Tab = 'overview' | 'journey' | 'data' | 'quality'

function AssetDetailPage() {
  const { asset, checks } = Route.useLoaderData()
  const params = Route.useParams()
  const [activeTab, setActiveTab] = useState<Tab>('overview')

  const hasError = 'error' in asset
  const assetData = hasError ? null : asset
  const checksData = 'error' in checks ? [] : checks

  if (hasError) {
    return (
      <div className="p-8">
        <Link
          to="/assets"
          className="flex items-center gap-2 text-slate-400 hover:text-slate-100 mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Assets
        </Link>
        <div className="p-6 bg-red-900/20 border border-red-700/50 rounded-xl">
          <h2 className="text-xl font-bold text-red-300 mb-2">
            Asset Not Found
          </h2>
          <p className="text-red-400">{(asset as { error: string }).error}</p>
        </div>
      </div>
    )
  }

  const tabs: Array<{ id: Tab; label: string; icon: React.ReactNode }> = [
    { id: 'overview', label: 'Overview', icon: <Info className="w-4 h-4" /> },
    {
      id: 'journey',
      label: 'Journey',
      icon: <GitBranch className="w-4 h-4" />,
    },
    { id: 'data', label: 'Data', icon: <Database className="w-4 h-4" /> },
    { id: 'quality', label: 'Quality', icon: <Shield className="w-4 h-4" /> },
  ]

  return (
    <div className="p-8">
      <Link
        to="/assets"
        className="flex items-center gap-2 text-slate-400 hover:text-slate-100 mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Assets
      </Link>

      {/* Header */}
      <div className="mb-6">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-cyan-500/10 rounded-xl">
            <Database className="w-8 h-8 text-cyan-400" />
          </div>
          <div className="flex-1">
            <h1 className="text-3xl font-bold mb-2">{params.assetId}</h1>
            {assetData?.description && (
              <p className="text-slate-400">{assetData.description}</p>
            )}
            <div className="flex items-center gap-4 mt-3">
              {assetData?.groupName && (
                <span className="px-2 py-1 text-xs font-medium bg-slate-700 text-slate-300 rounded">
                  {assetData.groupName}
                </span>
              )}
              {assetData?.computeKind && (
                <span className="px-2 py-1 text-xs font-medium bg-purple-900/50 text-purple-300 rounded">
                  {assetData.computeKind}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-700 mb-6">
        <nav className="flex gap-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-cyan-400 text-cyan-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-600'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && <OverviewTab assetData={assetData} />}
      {activeTab === 'journey' && <JourneyTab assetKey={params.assetId} />}
      {activeTab === 'data' && <DataTab assetKey={params.assetId} />}
      {activeTab === 'quality' && <QualityTab checks={checksData} />}
    </div>
  )
}

// Overview Tab (existing content)
function OverviewTab({ assetData }: { assetData: AssetDetails | null }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-6">
        <section className="bg-slate-800 rounded-xl border border-slate-700 p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Info className="w-5 h-5 text-slate-400" />
            Metadata
          </h2>
          {assetData?.metadata && assetData.metadata.length > 0 ? (
            <div className="space-y-3">
              {assetData.metadata.map((entry, idx) => (
                <div key={idx} className="flex items-start gap-4">
                  <span className="text-slate-400 text-sm min-w-[120px]">
                    {entry.key}
                  </span>
                  <span className="text-slate-200 text-sm font-mono break-all">
                    {entry.value}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-slate-500">No metadata available</p>
          )}
        </section>

        <section className="bg-slate-800 rounded-xl border border-slate-700 p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Table className="w-5 h-5 text-slate-400" />
            Ops
          </h2>
          {assetData?.opNames && assetData.opNames.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {assetData.opNames.map((op, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 text-sm bg-slate-700 text-slate-300 rounded-lg font-mono"
                >
                  {op}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-slate-500">No ops defined</p>
          )}
        </section>

        {/* Columns Section */}
        <section className="bg-slate-800 rounded-xl border border-slate-700 p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Columns2 className="w-5 h-5 text-slate-400" />
            Columns
            {assetData?.columns && (
              <span className="px-2 py-0.5 text-xs font-medium bg-cyan-900/50 text-cyan-300 rounded">
                {assetData.columns.length}
              </span>
            )}
          </h2>
          {assetData?.columns && assetData.columns.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="text-left py-2 px-3 font-medium text-slate-400">
                      Name
                    </th>
                    <th className="text-left py-2 px-3 font-medium text-slate-400">
                      Type
                    </th>
                    <th className="text-left py-2 px-3 font-medium text-slate-400">
                      Source
                    </th>
                    <th className="text-left py-2 px-3 font-medium text-slate-400">
                      Description
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {assetData.columns.map((col, idx) => {
                    const deps = assetData.columnLineage?.[col.name]
                    return (
                      <tr
                        key={idx}
                        className="border-b border-slate-700/50 hover:bg-slate-700/30"
                      >
                        <td className="py-2 px-3 font-mono text-cyan-300">
                          {col.name}
                        </td>
                        <td className="py-2 px-3 font-mono text-amber-300">
                          {col.type}
                        </td>
                        <td className="py-2 px-3">
                          {deps && deps.length > 0 ? (
                            <div className="flex flex-col gap-1">
                              {deps.map((dep, depIdx) => (
                                <Link
                                  key={depIdx}
                                  to="/assets/$assetId"
                                  params={{ assetId: dep.assetKey.join('/') }}
                                  className="text-xs text-purple-300 hover:text-purple-200 hover:underline"
                                >
                                  {dep.assetKey[dep.assetKey.length - 1]}.
                                  {dep.columnName}
                                </Link>
                              ))}
                            </div>
                          ) : (
                            <span className="text-slate-500 text-xs">—</span>
                          )}
                        </td>
                        <td className="py-2 px-3 text-slate-400">
                          {col.description || '—'}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-slate-500">No column schema available</p>
          )}
        </section>
      </div>

      <div className="space-y-6">
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-6">
          <h3 className="text-sm font-medium text-slate-400 mb-4">Status</h3>
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <Clock className="w-5 h-5 text-slate-500" />
              <div>
                <div className="text-sm text-slate-400">Last Materialized</div>
                <div className="text-slate-200">
                  {assetData?.lastMaterialization
                    ? new Date(
                        Number(assetData.lastMaterialization.timestamp),
                      ).toLocaleString()
                    : 'Never'}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Calendar className="w-5 h-5 text-slate-500" />
              <div>
                <div className="text-sm text-slate-400">Partitioned</div>
                <div className="text-slate-200">
                  {assetData?.partitionDefinition ? 'Yes' : 'No'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Journey Tab
function JourneyTab({ assetKey }: { assetKey: string }) {
  return (
    <div className="space-y-6">
      <section className="bg-slate-800 rounded-xl border border-slate-700 p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <GitBranch className="w-5 h-5 text-cyan-400" />
          Data Lineage
        </h2>
        <p className="text-sm text-slate-400 mb-4">
          Shows where this data comes from and where it goes
        </p>
        <DataJourney assetKey={assetKey} />
      </section>

      <section className="bg-slate-800 rounded-xl border border-slate-700 p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <History className="w-5 h-5 text-cyan-400" />
          Materialization History
        </h2>
        <MaterializationTimeline assetKey={assetKey} limit={10} />
      </section>
    </div>
  )
}

// Data Tab
function DataTab({ assetKey }: { assetKey: string }) {
  // Extract table name from asset key (last segment)
  const tableName = assetKey.split('/').pop() || assetKey

  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Database className="w-5 h-5 text-cyan-400" />
          Data Preview
        </h2>
        <DataPreview table={tableName} />
      </section>
    </div>
  )
}

// Quality Tab
function QualityTab({ checks }: { checks: Array<QualityCheck> }) {
  return (
    <div className="space-y-6">
      <section className="bg-slate-800 rounded-xl border border-slate-700 p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-cyan-400" />
          Quality Checks
          {checks.length > 0 && (
            <span className="text-xs px-2 py-0.5 bg-cyan-900/50 text-cyan-300 rounded">
              {checks.length}
            </span>
          )}
        </h2>
        {checks.length > 0 ? (
          <div className="space-y-3">
            {checks.map((check) => (
              <div
                key={check.name}
                className={`p-3 rounded-lg border ${
                  check.status === 'PASSED'
                    ? 'bg-green-900/20 border-green-700/50'
                    : check.status === 'FAILED'
                      ? 'bg-red-900/20 border-red-700/50'
                      : 'bg-slate-700/50 border-slate-600'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{check.name}</span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded ${
                      check.status === 'PASSED'
                        ? 'bg-green-800 text-green-300'
                        : check.status === 'FAILED'
                          ? 'bg-red-800 text-red-300'
                          : 'bg-slate-600 text-slate-300'
                    }`}
                  >
                    {check.status}
                  </span>
                </div>
                {check.description && (
                  <p className="text-sm text-slate-400 mt-1">
                    {check.description}
                  </p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-slate-500">
            <Shield className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No quality checks configured</p>
            <p className="text-sm mt-1">
              Add{' '}
              <code className="bg-slate-700 px-1 rounded">@phlo.quality</code>{' '}
              decorators to enable checks
            </p>
          </div>
        )}
      </section>
    </div>
  )
}
