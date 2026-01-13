/**
 * Shared Journey Node component for React Flow visualizations.
 * Used by DataJourney and RowJourney components.
 */
import { Handle, Position } from '@xyflow/react'
import { Database } from 'lucide-react'

import type { NodeProps } from '@xyflow/react'

import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

export interface JourneyNodeData {
  label: string
  isCurrent: boolean
  computeKind?: string
  lastMaterialized?: string
  assetKey?: string
  onSelect?: (assetKey: string) => void
  [key: string]: unknown
}

export function JourneyNode({ data }: NodeProps) {
  const {
    label,
    isCurrent,
    computeKind,
    lastMaterialized,
    assetKey,
    onSelect,
  } = data as JourneyNodeData

  const isClickable = onSelect && assetKey

  const handleClick = () => {
    if (isClickable && assetKey != null) {
      onSelect(assetKey)
    }
  }

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (isClickable && (event.key === 'Enter' || event.key === ' ')) {
      event.preventDefault()
      handleClick()
    }
  }

  return (
    <div
      onClick={isClickable ? handleClick : undefined}
      onKeyDown={isClickable ? handleKeyDown : undefined}
      role={isClickable ? 'button' : undefined}
      tabIndex={isClickable ? 0 : undefined}
      aria-current={isCurrent ? 'true' : undefined}
      className={cn(
        'border bg-card transition-colors',
        isClickable ? 'cursor-pointer' : '',
        isClickable
          ? cn(
              'border-2',
              isCurrent
                ? 'border-primary shadow-sm ring-1 ring-primary/20'
                : 'border-border hover:border-primary/50 hover:bg-muted/50',
            )
          : cn(
              'border-border border-l-4 shadow-sm hover:bg-muted/50',
              isCurrent
                ? 'border-l-primary ring-2 ring-primary/40'
                : 'border-l-border',
            ),
      )}
    >
      <Handle type="target" position={Position.Left} className="!bg-border" />

      <div className="px-4 py-3">
        <div className="flex items-center gap-2 mb-1">
          <Database
            className={cn(
              'w-4 h-4',
              isCurrent ? 'text-primary' : 'text-muted-foreground',
            )}
          />
          <span className="font-medium text-sm text-foreground">{label}</span>
        </div>

        <div className="flex items-center gap-2 text-xs">
          {computeKind && (
            <Badge variant={isClickable ? 'secondary' : 'outline'}>
              {computeKind}
            </Badge>
          )}
          {lastMaterialized && (
            <span className="text-muted-foreground">{lastMaterialized}</span>
          )}
        </div>
      </div>

      <Handle type="source" position={Position.Right} className="!bg-border" />
    </div>
  )
}
