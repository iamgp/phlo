import { createFileRoute } from '@tanstack/react-router'
import { AlertCircle, CheckCircle2, Clock3, ListChecks } from 'lucide-react'
import { useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import type { V2Run } from '@/v2/api/types'
import { getV2RunRecords } from '@/v2/api/resources'
import { V2Page } from '@/v2/components/V2Page'
import { useLiveResource } from '@/v2/routes/liveResource'

export const Route = createFileRoute('/v2/runs')({
  component: Runs,
})

export function Runs() {
  const result = useLiveResource(getV2RunRecords, 60_000, 'v2:runs')
  const runs = result.data ?? []
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const selected = runs.find((run) => run.id === selectedId) ?? runs[0] ?? null
  const counts = useMemo(() => countRuns(runs), [runs])

  return (
    <V2Page
      kicker="Runs"
      title="Orchestrator runs"
      description="Pipeline run history with linked assets, checks, logs, and evidence."
      action={<span className="phlo-v2-pill">{runs.length} runs</span>}
    >
      <section className="phlo-v2-command phlo-v2-runs-shell">
        <div className="phlo-v2-command-primary phlo-v2-run-list-surface">
          <div className="phlo-v2-command-strip phlo-v2-run-summary">
            <Metric
              icon={<CheckCircle2 className="size-4" />}
              label="Succeeded"
              value={counts.succeeded}
            />
            <Metric
              icon={<AlertCircle className="size-4" />}
              label="Failed"
              value={counts.failed}
            />
            <Metric
              icon={<Clock3 className="size-4" />}
              label="Running"
              value={counts.running}
            />
          </div>

          <div className="phlo-v2-timeline">
            {runs.map((run) => (
              <RunLine
                key={run.id}
                onSelect={setSelectedId}
                run={run}
                selected={run.id === selected?.id}
              />
            ))}
            {runs.length === 0 && (
              <div className="phlo-v2-operation-empty">
                <div>
                  <span className="phlo-v2-inspector-label">
                    No runs returned
                  </span>
                  <h2>Run history is quiet.</h2>
                  <p>
                    Runs will appear here after a workflow starts or your
                    orchestrator reports recent activity.
                  </p>
                </div>
                <div className="phlo-v2-detail-list">
                  <div className="phlo-v2-mini-row">
                    <span>Contract</span>
                    <small>/api/observatory/v2/runs</small>
                  </div>
                  <div className="phlo-v2-mini-row">
                    <span>Rows</span>
                    <small>0 returned</small>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <aside className="phlo-v2-inspector">
          <div className="phlo-v2-inspector-label">Selected run</div>
          {selected ? (
            <>
              <h2>{selected.name}</h2>
              <p>{selected.status}</p>
              <dl className="phlo-v2-facts">
                <Fact label="Started" value={selected.started_at ?? 'n/a'} />
                <Fact
                  label="Completed"
                  value={selected.completed_at ?? 'not completed'}
                />
                <Fact
                  label="Duration"
                  value={
                    selected.duration_seconds === null ||
                    selected.duration_seconds === undefined
                      ? 'n/a'
                      : `${selected.duration_seconds}s`
                  }
                />
                <Fact label="Assets" value={selected.assets.length} />
                <Fact label="Checks" value={selected.checks.length} />
                <Fact label="Logs" value={selected.logs.length} />
              </dl>
              <RelatedList title="Assets" refs={selected.assets} />
              <RelatedList title="Checks" refs={selected.checks} />
              <RelatedList title="Logs" refs={selected.logs} />
            </>
          ) : (
            <>
              <h2>No run selected</h2>
              <p>There are no runs to inspect yet.</p>
            </>
          )}
          {result.error && (
            <div className="phlo-v2-panel-footer">{result.error}</div>
          )}
        </aside>
      </section>
    </V2Page>
  )
}

function Metric({
  icon,
  label,
  value,
}: {
  icon: ReactNode
  label: string
  value: string | number
}) {
  return (
    <div className="phlo-v2-command-metric">
      {icon}
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function RunLine({
  run,
  onSelect,
  selected,
}: {
  run: V2Run
  onSelect: (id: string) => void
  selected: boolean
}) {
  return (
    <button
      className="phlo-v2-timeline-row"
      data-active={selected}
      onClick={() => onSelect(run.id)}
      type="button"
    >
      <span className="phlo-v2-dot" data-state={stateForStatus(run.status)} />
      <div>
        <div className="phlo-v2-row-title">
          <ListChecks className="size-4" />
          {run.name}
        </div>
        <div className="phlo-v2-row-meta">
          {run.assets.length} assets · {run.checks.length} checks ·{' '}
          {run.completed_at ?? run.started_at ?? 'not timestamped'}
        </div>
      </div>
      <span className="phlo-v2-pill">{run.status}</span>
    </button>
  )
}

function RelatedList({
  title,
  refs,
}: {
  title: string
  refs: V2Run['assets']
}) {
  return (
    <div className="phlo-v2-detail-list">
      <div className="phlo-v2-mini-row">
        <span>{title}</span>
        <small>
          {refs.length > 0 ? refs.map((ref) => ref.label).join(', ') : 'none'}
        </small>
      </div>
    </div>
  )
}

function Fact({
  label,
  value,
}: {
  label: string
  value: string | number | boolean | null
}) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value === null ? 'n/a' : String(value)}</dd>
    </>
  )
}

function countRuns(runs: Array<V2Run>): Record<V2Run['status'], number> {
  return runs.reduce(
    (counts, run) => {
      counts[run.status] += 1
      return counts
    },
    {
      queued: 0,
      running: 0,
      succeeded: 0,
      failed: 0,
      cancelled: 0,
      unknown: 0,
    },
  )
}

function stateForStatus(status: V2Run['status']) {
  if (status === 'succeeded') return 'ok'
  if (status === 'failed' || status === 'cancelled') return 'error'
  if (status === 'running' || status === 'queued') return 'warning'
  return 'unknown'
}
