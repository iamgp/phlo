import { createFileRoute } from '@tanstack/react-router'
import { AlertCircle, CheckCircle2, Clock3, ListChecks } from 'lucide-react'
import { useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import type { ObservatoryRun } from '@/observatory/api/types'
import { getObservatoryRunRecords } from '@/observatory/api/resources'
import { ObservatoryPage } from '@/observatory/components/ObservatoryPage'
import { useLiveResource } from '@/observatory/routes/liveResource'

export const Route = createFileRoute('/runs')({
  component: Runs,
})

export function Runs() {
  const result = useLiveResource(getObservatoryRunRecords, 60_000, 'v2:runs')
  const runs = useMemo(
    () => [...(result.data ?? [])].sort(compareRuns),
    [result.data],
  )
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const selected =
    runs.find((run) => run.id === selectedId) ??
    runs.find((run) => run.status === 'failed') ??
    runs[0] ??
    null
  const counts = useMemo(() => countRuns(runs), [runs])

  return (
    <ObservatoryPage
      kicker="Runs"
      title="Orchestrator runs"
      description="Pipeline run history with linked assets, checks, logs, and evidence."
      action={<span className="phlo-observatory-pill">{runs.length} runs</span>}
    >
      <section className="phlo-observatory-command phlo-observatory-runs-shell">
        <div className="phlo-observatory-command-primary phlo-observatory-run-list-surface">
          <div className="phlo-observatory-command-strip phlo-observatory-run-summary">
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

          <div className="phlo-observatory-timeline">
            {runs.map((run) => (
              <RunLine
                key={run.id}
                onSelect={setSelectedId}
                run={run}
                selected={run.id === selected?.id}
              />
            ))}
            {runs.length === 0 && (
              <div className="phlo-observatory-operation-empty">
                <div>
                  <span className="phlo-observatory-inspector-label">
                    No runs returned
                  </span>
                  <h2>Run history is quiet.</h2>
                  <p>
                    Runs will appear here after a workflow starts or your
                    orchestrator reports recent activity.
                  </p>
                </div>
                <div className="phlo-observatory-detail-list">
                  <div className="phlo-observatory-mini-row">
                    <span>Contract</span>
                    <small>/api/observatory/runs</small>
                  </div>
                  <div className="phlo-observatory-mini-row">
                    <span>Rows</span>
                    <small>0 returned</small>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <aside className="phlo-observatory-inspector">
          <div className="phlo-observatory-inspector-label">Selected run</div>
          {selected ? (
            <>
              <h2>{selected.name}</h2>
              <p>{runNarrative(selected)}</p>
              <dl className="phlo-observatory-facts">
                <Fact label="Status" value={selected.status} />
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
              {runFailureReason(selected) && (
                <div className="phlo-observatory-detail-list">
                  <div className="phlo-observatory-mini-row">
                    <span>Failure reason</span>
                    <small>{runFailureReason(selected)}</small>
                  </div>
                </div>
              )}
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
            <div className="phlo-observatory-panel-footer">{result.error}</div>
          )}
        </aside>
      </section>
    </ObservatoryPage>
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
    <div className="phlo-observatory-command-metric">
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
  run: ObservatoryRun
  onSelect: (id: string) => void
  selected: boolean
}) {
  return (
    <button
      className="phlo-observatory-run-row"
      data-active={selected}
      data-status={run.status}
      onClick={() => onSelect(run.id)}
      type="button"
    >
      <span
        className="phlo-observatory-dot"
        data-state={stateForStatus(run.status)}
      />
      <div className="phlo-observatory-run-row-main">
        <div className="phlo-observatory-row-title">
          <ListChecks className="size-4" />
          {run.name}
        </div>
        <div className="phlo-observatory-row-meta">
          {run.assets.length} assets · {run.checks.length} checks ·{' '}
          {run.completed_at ?? run.started_at ?? 'not timestamped'}
        </div>
      </div>
      <span className="phlo-observatory-pill">{run.status}</span>
    </button>
  )
}

function RelatedList({
  title,
  refs,
}: {
  title: string
  refs: ObservatoryRun['assets']
}) {
  return (
    <div className="phlo-observatory-detail-list">
      <div className="phlo-observatory-mini-row">
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

function countRuns(
  runs: Array<ObservatoryRun>,
): Record<ObservatoryRun['status'], number> {
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

function stateForStatus(status: ObservatoryRun['status']) {
  if (status === 'succeeded') return 'ok'
  if (status === 'failed' || status === 'cancelled') return 'error'
  if (status === 'running' || status === 'queued') return 'warning'
  return 'unknown'
}

function compareRuns(left: ObservatoryRun, right: ObservatoryRun): number {
  return runScore(right) - runScore(left)
}

function runScore(run: ObservatoryRun): number {
  const time = Date.parse(run.completed_at ?? run.started_at ?? '')
  let score = Number.isNaN(time) ? 0 : time / 1_000_000
  if (run.status === 'failed') score += 1_000_000
  if (run.status === 'running') score += 500_000
  return score
}

function runNarrative(run: ObservatoryRun): string {
  const assetCount = `${run.assets.length} asset${run.assets.length === 1 ? '' : 's'}`
  const checkCount = `${run.checks.length} check${run.checks.length === 1 ? '' : 's'}`
  if (run.status === 'failed') {
    return `Failed run with ${assetCount}, ${checkCount}, and ${run.logs.length} linked logs.`
  }
  if (run.status === 'succeeded') {
    return `Succeeded run with ${assetCount} and ${checkCount}.`
  }
  return `${run.status} run with ${assetCount} and ${checkCount}.`
}

function runFailureReason(run: ObservatoryRun): string | null {
  const reason = run.metadata.failure_reason ?? run.metadata.error
  return typeof reason === 'string' && reason ? reason : null
}
