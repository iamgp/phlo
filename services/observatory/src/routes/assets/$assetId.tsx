import { getAssetDetails, type AssetDetails } from '@/server/dagster.server'
import { createFileRoute, Link } from '@tanstack/react-router'
import {
  ArrowLeft,
  Calendar,
  Clock,
  Columns2,
  Database,
  Info,
  Shield,
  Table,
} from 'lucide-react'

export const Route = createFileRoute('/assets/$assetId')({
  loader: async ({ params }) => {
    // Call server function with the asset key path
    const asset = await getAssetDetails({ data: params.assetId })
    return { asset }
  },
  component: AssetDetailPage,
})

function AssetDetailPage() {
  const { asset } = Route.useLoaderData()
  const params = Route.useParams()

  const hasError = 'error' in asset
  const assetData = hasError ? null : (asset as AssetDetails)

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

  return (
    <div className="p-8">
      <Link
        to="/assets"
        className="flex items-center gap-2 text-slate-400 hover:text-slate-100 mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Assets
      </Link>

      <div className="mb-8">
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
                  <div className="text-sm text-slate-400">
                    Last Materialized
                  </div>
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

          <div className="bg-slate-800 rounded-xl border border-slate-700 border-dashed p-6">
            <h3 className="text-sm font-medium text-slate-400 mb-4 flex items-center gap-2">
              <Shield className="w-4 h-4" />
              Quality Checks
            </h3>
            <p className="text-slate-500 text-sm">Coming in Phase 4</p>
          </div>
        </div>
      </div>
    </div>
  )
}
