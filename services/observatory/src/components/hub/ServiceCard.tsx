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
import { Badge } from '@/components/ui/badge'
import { Button, buttonVariants } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'

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
    <Card className={cn(isUnhealthy && 'border-destructive/40')}>
      <CardHeader className="space-y-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <Badge
              variant="outline"
              className={
                categoryColors[service.category] ?? categoryColors.core
              }
            >
              {service.category}
            </Badge>
            {service.default && (
              <Badge variant="secondary" className="text-muted-foreground">
                default
              </Badge>
            )}
          </div>
          <div
            className={cn(
              'flex items-center gap-1.5 text-xs',
              currentStatus.color,
            )}
          >
            {currentStatus.icon}
            <span className="font-medium">{currentStatus.label}</span>
          </div>
        </div>

        <div>
          <CardTitle className="text-lg">{service.name}</CardTitle>
          <CardDescription className="line-clamp-2">
            {service.description}
          </CardDescription>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {service.ports.length > 0 && (
          <div className="flex items-center justify-between gap-3">
            <div className="text-sm text-muted-foreground">
              Port:{' '}
              <span className="text-foreground">{service.ports[0].host}</span>
            </div>
            {service.url && isRunning && (
              <a
                href={service.url}
                target="_blank"
                rel="noopener noreferrer"
                className={cn(
                  buttonVariants({ variant: 'outline', size: 'xs' }),
                  'gap-1',
                )}
              >
                <ExternalLink className="size-3" />
                Open
              </a>
            )}
          </div>
        )}

        {hasCredentials && (
          <>
            <Separator />
            <div>
              <Button
                variant="ghost"
                size="sm"
                className="w-full justify-between"
                onClick={() => setShowCredentials(!showCredentials)}
              >
                <span className="flex items-center gap-2">
                  <Key className="size-4" />
                  Credentials ({credentials.length})
                </span>
                {showCredentials ? (
                  <ChevronUp className="size-4" />
                ) : (
                  <ChevronDown className="size-4" />
                )}
              </Button>

              {showCredentials && (
                <div className="mt-3 space-y-2">
                  {credentials.map((cred) => (
                    <div
                      key={cred.name}
                      className="text-xs bg-muted rounded-none p-2"
                    >
                      <div className="text-muted-foreground mb-0.5">
                        {cred.name}
                      </div>
                      <code className="text-foreground">{cred.value}</code>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </CardContent>

      <CardFooter className="gap-2">
        {isRunning || isUnhealthy ? (
          <>
            <Button
              variant="destructive"
              className="flex-1"
              onClick={() => onStop(service.name)}
              disabled={isLoading}
            >
              {isLoading ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Power className="size-4" />
              )}
              Stop
            </Button>
            <Button
              variant="outline"
              size="icon-sm"
              onClick={() => onRestart(service.name)}
              disabled={isLoading}
            >
              {isLoading ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <RefreshCw className="size-4" />
              )}
            </Button>
          </>
        ) : (
          <Button
            className="flex-1"
            onClick={() => onStart(service.name)}
            disabled={isLoading}
          >
            {isLoading ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Play className="size-4" />
            )}
            Start
          </Button>
        )}
      </CardFooter>
    </Card>
  )
}
