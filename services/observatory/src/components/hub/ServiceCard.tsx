/**
 * ServiceCard Component
 *
 * Displays a single service with status, controls, and credentials.
 */

import {
  AlertCircle,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Circle,
  ExternalLink,
  Key,
  Loader2,
  Play,
  Power,
  RefreshCw,
} from 'lucide-react'
import { useState } from 'react'
import type { ServiceWithStatus } from '@/server/services.server'

interface ServiceCardProps {
  service: ServiceWithStatus
  onStart: (name: string) => Promise<void>
  onStop: (name: string) => Promise<void>
  onRestart: (name: string) => Promise<void>
  isLoading?: boolean
}

export function ServiceCard({
  service,
  onStart,
  onStop,
  onRestart,
  isLoading,
}: ServiceCardProps) {
  const [showCredentials, setShowCredentials] = useState(false)

  const status = service.containerStatus?.status ?? 'stopped'
  const isRunning = status === 'running'
  const isUnhealthy = status === 'unhealthy'

  // Category badge colors
  const categoryColors: Record<string, string> = {
    core: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    api: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
    bi: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
    observability: 'bg-green-500/20 text-green-300 border-green-500/30',
    admin: 'bg-slate-500/20 text-slate-300 border-slate-500/30',
    orchestration: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
  }

  // Status indicator colors
  const statusConfig: Record<
    string,
    { color: string; icon: React.ReactNode; label: string }
  > = {
    running: {
      color: 'text-green-400',
      icon: <CheckCircle className="w-4 h-4" />,
      label: 'Running',
    },
    stopped: {
      color: 'text-slate-400',
      icon: <Circle className="w-4 h-4" />,
      label: 'Stopped',
    },
    unhealthy: {
      color: 'text-red-400',
      icon: <AlertCircle className="w-4 h-4" />,
      label: 'Unhealthy',
    },
    starting: {
      color: 'text-yellow-400',
      icon: <Loader2 className="w-4 h-4 animate-spin" />,
      label: 'Starting',
    },
    unknown: {
      color: 'text-slate-500',
      icon: <Circle className="w-4 h-4" />,
      label: 'Unknown',
    },
  }

  const currentStatus = statusConfig[status] ?? statusConfig.unknown

  // Filter credentials (secrets + their related username/email vars)
  const credentials = (() => {
    const secrets = service.envVars.filter((ev) => ev.secret)
    const secretNames = new Set(secrets.map((s) => s.name))

    // For each password, look for related user/email vars
    const relatedVars: typeof secrets = []
    for (const secret of secrets) {
      const baseName = secret.name.replace(/_PASSWORD$/, '')
      // Look for USER, USERNAME, EMAIL variants
      for (const suffix of [
        '_USER',
        '_USERNAME',
        '_EMAIL',
        '_ADMIN_USER',
        '_ADMIN_EMAIL',
      ]) {
        const relatedName = baseName + suffix
        // Also check without the prefix part (e.g., SUPERSET_ADMIN_PASSWORD -> SUPERSET_ADMIN_USER)
        const adminRelated = secret.name.replace(
          '_PASSWORD',
          suffix.replace('_ADMIN', ''),
        )
        const envVar = service.envVars.find(
          (ev) =>
            (ev.name === relatedName || ev.name === adminRelated) &&
            !secretNames.has(ev.name),
        )
        if (envVar && !relatedVars.some((r) => r.name === envVar.name)) {
          relatedVars.push(envVar)
        }
      }
    }

    // Return related vars first (usernames), then secrets (passwords)
    return [...relatedVars, ...secrets]
  })()
  const hasCredentials = credentials.length > 0

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden hover:border-slate-600 transition-colors">
      {/* Header */}
      <div className="p-4 border-b border-slate-700">
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <span
              className={`px-2 py-0.5 text-xs rounded-full border ${categoryColors[service.category] ?? categoryColors.core}`}
            >
              {service.category}
            </span>
            {service.default && (
              <span className="px-2 py-0.5 text-xs bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 rounded-full">
                default
              </span>
            )}
          </div>
          <div className={`flex items-center gap-1.5 ${currentStatus.color}`}>
            {currentStatus.icon}
            <span className="text-xs font-medium">{currentStatus.label}</span>
          </div>
        </div>

        <h3 className="text-lg font-semibold text-slate-100">{service.name}</h3>
        <p className="text-sm text-slate-400 mt-1 line-clamp-2">
          {service.description}
        </p>
      </div>

      {/* Port & Link */}
      {service.ports.length > 0 && (
        <div className="px-4 py-3 border-b border-slate-700/50 bg-slate-800/50">
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-500">
              Port:{' '}
              <span className="text-slate-300">{service.ports[0].host}</span>
            </span>
            {service.url && isRunning && (
              <a
                href={service.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-xs text-cyan-400 hover:text-cyan-300"
              >
                <ExternalLink className="w-3 h-3" />
                Open
              </a>
            )}
          </div>
        </div>
      )}

      {/* Credentials (collapsible) */}
      {hasCredentials && (
        <div className="border-b border-slate-700/50">
          <button
            onClick={() => setShowCredentials(!showCredentials)}
            className="w-full px-4 py-2 flex items-center justify-between text-sm text-slate-400 hover:bg-slate-700/30 transition-colors"
          >
            <span className="flex items-center gap-2">
              <Key className="w-4 h-4" />
              Credentials ({credentials.length})
            </span>
            {showCredentials ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>
          {showCredentials && (
            <div className="px-4 pb-3 space-y-2">
              {credentials.map((cred) => (
                <div
                  key={cred.name}
                  className="text-xs bg-slate-900/50 rounded p-2"
                >
                  <div className="text-slate-500 mb-0.5">{cred.name}</div>
                  <code className="text-slate-300 font-mono">{cred.value}</code>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="p-3 flex gap-2">
        {isRunning || isUnhealthy ? (
          <>
            <button
              onClick={() => onStop(service.name)}
              disabled={isLoading}
              className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-red-500/10 text-red-400 hover:bg-red-500/20 rounded-lg transition-colors disabled:opacity-50"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Power className="w-4 h-4" />
              )}
              <span className="text-sm">Stop</span>
            </button>
            <button
              onClick={() => onRestart(service.name)}
              disabled={isLoading}
              className="flex items-center justify-center gap-2 px-3 py-2 bg-slate-700/50 text-slate-300 hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
            </button>
          </>
        ) : (
          <button
            onClick={() => onStart(service.name)}
            disabled={isLoading}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-green-500/10 text-green-400 hover:bg-green-500/20 rounded-lg transition-colors disabled:opacity-50"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            <span className="text-sm">Start</span>
          </button>
        )}
      </div>
    </div>
  )
}
