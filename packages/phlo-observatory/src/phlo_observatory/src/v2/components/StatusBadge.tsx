import type { V2HealthState, V2ServiceStatus } from '@/v2/api/types'

type StatusValue = V2HealthState | V2ServiceStatus

export function StatusBadge({
  label,
  state,
}: {
  label: string
  state: StatusValue
}) {
  return (
    <span className="phlo-v2-pill">
      <span className="phlo-v2-dot" data-state={state} />
      {label}
    </span>
  )
}
