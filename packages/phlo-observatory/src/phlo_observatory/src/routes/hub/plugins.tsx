/**
 * Plugins Hub Route
 *
 * Displays installed and available plugins.
 */

import { Await, Link, createFileRoute, defer } from '@tanstack/react-router'
import { Boxes, CircleCheck, Package } from 'lucide-react'
import { Suspense } from 'react'

import type { PluginInfo } from '@/server/plugins.server'
import { getAvailablePlugins } from '@/server/plugins.server'
import { Badge } from '@/components/ui/badge'
import { buttonVariants } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { cn } from '@/lib/utils'

export const Route = createFileRoute('/hub/plugins')({
  loader: () => ({ data: defer(getAvailablePlugins()) }),
  component: PluginsPage,
})

function PluginsPage() {
  const { data } = Route.useLoaderData()

  return (
    <Suspense fallback={<LoadingState message="Loading plugins..." />}>
      <Await promise={data}>
        {(resolved) => <PluginsContent {...resolved} />}
      </Await>
    </Suspense>
  )
}

function PluginsContent({
  installed,
  available,
}: {
  installed: Array<PluginInfo>
  available: Array<PluginInfo>
}) {
  const installedByType = groupByType(installed)
  const availableByType = groupByType(available)

  const installedCount = installed.length
  const availableCount = available.length
  const verifiedCount = available.filter((plugin) => plugin.verified).length

  return (
    <div className="h-full overflow-auto">
      <div className="mx-auto w-full max-w-6xl px-4 py-6">
        <div className="flex items-start justify-between gap-4 mb-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Boxes className="size-7 text-primary" />
              <h1 className="text-3xl font-bold">Plugin Registry</h1>
            </div>
            <p className="text-muted-foreground">
              Discover, install, and manage Phlo plugins across your stack.
            </p>
          </div>
          <Link
            to="/hub"
            className={cn(buttonVariants({ variant: 'outline' }))}
          >
            Back to Hub
          </Link>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
          <StatCard
            label="Installed"
            value={installedCount}
            icon={<CircleCheck className="w-5 h-5" />}
          />
          <StatCard
            label="Available"
            value={availableCount}
            icon={<Package className="w-5 h-5" />}
          />
          <StatCard
            label="Verified"
            value={verifiedCount}
            icon={<CircleCheck className="w-5 h-5" />}
          />
        </div>

        <Section title="Installed Plugins" pluginsByType={installedByType} />
        <Section title="Registry Plugins" pluginsByType={availableByType} />
      </div>
    </div>
  )
}

function LoadingState({ message }: { message: string }) {
  return (
    <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
      {message}
    </div>
  )
}

function groupByType(plugins: Array<PluginInfo>) {
  return plugins.reduce(
    (acc, plugin) => {
      if (!acc[plugin.type]) acc[plugin.type] = []
      acc[plugin.type].push(plugin)
      return acc
    },
    {} as Record<string, Array<PluginInfo>>,
  )
}

function Section({
  title,
  pluginsByType,
}: {
  title: string
  pluginsByType: Record<string, Array<PluginInfo>>
}) {
  const typeOrder: Array<PluginInfo['type']> = [
    'service',
    'source',
    'quality',
    'transform',
  ]
  const sortedTypes = typeOrder.filter((type) => pluginsByType[type]?.length)

  return (
    <div className="mb-8">
      <h2 className="text-xl font-semibold mb-4">{title}</h2>
      {sortedTypes.length === 0 ? (
        <div className="text-muted-foreground text-sm">No plugins found.</div>
      ) : (
        sortedTypes.map((type) => (
          <div key={type} className="mb-6">
            <h3 className="text-lg font-medium capitalize mb-3">{type}</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {pluginsByType[type].map((plugin) => (
                <PluginCard key={`${type}-${plugin.name}`} plugin={plugin} />
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  )
}

function PluginCard({ plugin }: { plugin: PluginInfo }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          {plugin.name}
          <Badge variant="secondary" className="capitalize">
            {plugin.type}
          </Badge>
          {plugin.verified && <Badge variant="outline">verified</Badge>}
          {plugin.core && <Badge variant="outline">core</Badge>}
        </CardTitle>
        <CardDescription className="text-sm text-muted-foreground">
          {plugin.description || 'No description provided.'}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2 text-xs text-muted-foreground">
        <div className="flex flex-wrap gap-2">
          <span>Version: {plugin.version}</span>
          {plugin.author && <span>Author: {plugin.author}</span>}
          {plugin.package && <span>Package: {plugin.package}</span>}
        </div>
        {plugin.category && (
          <div className="flex flex-wrap gap-2">
            <span>Category: {plugin.category}</span>
            {plugin.profile && <span>Profile: {plugin.profile}</span>}
            {plugin.default && <span>Default</span>}
          </div>
        )}
        {plugin.tags?.length ? (
          <div className="flex flex-wrap gap-2">
            {plugin.tags.map((tag) => (
              <Badge key={tag} variant="secondary" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}

interface StatCardProps {
  label: string
  value: number
  icon: React.ReactNode
}

function StatCard({ label, value, icon }: StatCardProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription className="flex items-center justify-between gap-2">
          <span>{label}</span>
          <span className="text-primary">{icon}</span>
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-0">
        <CardTitle className="text-2xl">{value}</CardTitle>
      </CardContent>
    </Card>
  )
}
