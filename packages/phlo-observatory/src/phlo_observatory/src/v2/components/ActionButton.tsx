import { AlertTriangle, Play } from 'lucide-react'

import type { V2Action } from '@/v2/api/types'

export function ActionButton({
  action,
  onRun,
}: {
  action: V2Action
  onRun: (actionId: string) => void
}) {
  const Icon =
    action.risk_level === 'high' || action.risk_level === 'critical'
      ? AlertTriangle
      : Play
  const title = action.reason ?? action.equivalent_cli_command ?? action.label

  return (
    <button
      aria-label={action.label}
      className="phlo-v2-action-button"
      disabled={!action.enabled}
      onClick={() => onRun(action.id)}
      title={title}
      type="button"
    >
      <Icon className="size-4" aria-hidden="true" />
      <span>{action.label}</span>
    </button>
  )
}
