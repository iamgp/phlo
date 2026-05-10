import { createFileRoute } from '@tanstack/react-router'
import { Check, CheckCircle2, FileCode2, WandSparkles } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import type { ChangeEvent } from 'react'

import type {
  V2ResourceResult,
  V2WorkflowApplyAction,
  V2WorkflowProposal,
  V2WorkflowWizardContribution,
  V2WorkflowWizardField,
  V2WorkflowWizardPayload,
} from '@/v2/api/types'
import {
  createV2WorkflowProposal,
  getV2WorkflowWizard,
  runV2WorkflowAction,
} from '@/v2/api/resources'
import { V2Page } from '@/v2/components/V2Page'
import { loadCachedResource } from '@/v2/routes/liveResource'

export const Route = createFileRoute('/v2/workflows/new')({
  component: WorkflowWizard,
})

type FormValues = Record<string, Record<string, string>>

const STAGE_LABELS: Record<string, string> = {
  source: 'Source',
  transform: 'Transform',
  quality: 'Quality',
  publish: 'Publish',
}

function WorkflowWizard() {
  const [wizard, setWizard] = useState<
    V2ResourceResult<V2WorkflowWizardPayload>
  >({ data: null, error: null })
  const [selected, setSelected] = useState<Record<string, Array<string>>>({})
  const [values, setValues] = useState<FormValues>({})
  const [workflowName, setWorkflowName] = useState('customer_health')
  const [domain, setDomain] = useState('customers')
  const [proposal, setProposal] = useState<
    V2ResourceResult<V2WorkflowProposal>
  >({
    data: null,
    error: null,
  })
  const [proposalLoading, setProposalLoading] = useState(false)
  const [actionMessage, setActionMessage] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    void loadCachedResource('v2:workflow-wizard', getV2WorkflowWizard, {
      force: true,
      staleMs: 60_000,
    }).then((next) => {
      if (cancelled) return
      setWizard(next)
      const contributions = next.data?.contributions ?? []
      const source = contributions.find((item) => item.stage === 'source')
      const transforms = contributions
        .filter((item) => item.stage === 'transform')
        .map((item) => item.id)
      setSelected({
        ...(source ? { source: [source.id] } : {}),
        ...(transforms.length ? { transform: transforms } : {}),
      })
      setValues(defaultValues(contributions))
    })
    return () => {
      cancelled = true
    }
  }, [])

  const contributions = wizard.data?.contributions ?? []
  const byStage = useMemo(() => groupByStage(contributions), [contributions])

  function updateField(contributionId: string, field: string, value: string) {
    setValues((current) => ({
      ...current,
      [contributionId]: {
        ...(current[contributionId] ?? {}),
        [field]: value,
      },
    }))
  }

  function buildRequest() {
    const selections: Record<
      string,
      Array<{ contribution_id: string; values: Record<string, string> }>
    > = {}
    for (const [stage, contributionIds] of Object.entries(selected)) {
      const entries = contributionIds.filter(Boolean).map((contributionId) => ({
        contribution_id: contributionId,
        values: values[contributionId] ?? {},
      }))
      if (entries.length) selections[stage] = entries
    }
    return { workflow_name: workflowName, domain, selections }
  }

  function generateProposal() {
    setActionMessage(null)
    setProposalLoading(true)
    void createV2WorkflowProposal({ data: buildRequest() })
      .then(setProposal)
      .finally(() => setProposalLoading(false))
  }

  function runAction(action: V2WorkflowApplyAction) {
    if (!proposal.data || !action.enabled) return
    void runV2WorkflowAction({
      data: { actionId: action.id, proposal: proposal.data },
    }).then((result) => {
      setActionMessage(
        result.data?.message ?? result.error ?? 'Action finished',
      )
    })
  }

  return (
    <V2Page
      action={<span className="phlo-v2-pill">proposal first</span>}
      description="Compose a complete workflow from package-provided source and transform steps, preview generated files, then apply guarded actions."
      kicker="Workflows"
      title="New workflow wizard"
    >
      <section
        className="phlo-v2-diff-metrics phlo-workflow-summary"
        aria-label="Wizard summary"
      >
        <Metric label="Contributions" value={contributions.length} />
        <Metric label="Stages" value={wizard.data?.stages.length ?? 0} />
        <Metric
          label="Files previewed"
          value={proposal.data?.files.length ?? 0}
        />
      </section>

      {wizard.error && <div className="phlo-v2-callout">{wizard.error}</div>}

      <section className="phlo-workflow-shell">
        <div className="phlo-workflow-main">
          <div className="phlo-v2-panel phlo-workflow-card">
            <div className="phlo-v2-panel-header phlo-workflow-card-header">
              <div>
                <h2>Workflow identity</h2>
                <p>
                  Name the workflow and choose the domain used for generated
                  files.
                </p>
              </div>
              <WandSparkles className="size-4" aria-hidden />
            </div>
            <div className="phlo-workflow-form-grid phlo-workflow-form-grid--identity">
              <label className="phlo-workflow-field">
                <span>Workflow name</span>
                <input
                  className="phlo-workflow-input"
                  onChange={(event) => setWorkflowName(event.target.value)}
                  value={workflowName}
                />
              </label>
              <label className="phlo-workflow-field">
                <span>Domain</span>
                <input
                  className="phlo-workflow-input"
                  onChange={(event) => setDomain(event.target.value)}
                  value={domain}
                />
              </label>
            </div>
          </div>

          {['source', 'transform', 'quality', 'publish'].map((stage) => (
            <StagePanel
              contributions={byStage[stage] ?? []}
              key={stage}
              onFieldChange={updateField}
              onSelect={(id) =>
                setSelected((current) => ({
                  ...current,
                  [stage]: toggleStageSelection(
                    stage,
                    current[stage] ?? [],
                    id,
                  ),
                }))
              }
              selectedIds={selected[stage] ?? []}
              stage={stage}
              values={values}
            />
          ))}

          <button
            className="phlo-v2-primary-button phlo-workflow-generate"
            disabled={proposalLoading}
            onClick={generateProposal}
          >
            {proposalLoading ? 'Generating proposal...' : 'Generate proposal'}
          </button>
        </div>

        <aside className="phlo-workflow-review">
          <ReviewPanel
            actionMessage={actionMessage}
            loading={proposalLoading}
            onGenerate={generateProposal}
            onRunAction={runAction}
            proposal={proposal}
          />
        </aside>
      </section>
    </V2Page>
  )
}

function StagePanel({
  stage,
  contributions,
  selectedIds,
  values,
  onSelect,
  onFieldChange,
}: {
  stage: string
  contributions: Array<V2WorkflowWizardContribution>
  selectedIds: Array<string>
  values: FormValues
  onSelect: (id: string) => void
  onFieldChange: (contributionId: string, field: string, value: string) => void
}) {
  const selected = contributions.filter((item) => selectedIds.includes(item.id))

  return (
    <section className="phlo-v2-panel phlo-workflow-card">
      <div className="phlo-v2-panel-header phlo-workflow-card-header">
        <div>
          <h2>{STAGE_LABELS[stage]}</h2>
          <p>{stageDescription(stage)}</p>
        </div>
        <span className="phlo-v2-pill">{contributions.length} options</span>
      </div>
      {contributions.length === 0 ? (
        <div className="phlo-workflow-empty-stage">
          <div>No contribution available</div>
          <p>This stage can be skipped in the first workflow wizard slice.</p>
        </div>
      ) : (
        <div className="phlo-workflow-options">
          {contributions.map((contribution) => (
            <button
              className="phlo-workflow-option"
              data-selected={selectedIds.includes(contribution.id)}
              key={contribution.id}
              onClick={() => onSelect(contribution.id)}
            >
              <span className="phlo-workflow-check" aria-hidden>
                {selectedIds.includes(contribution.id) ? (
                  <Check className="size-3" />
                ) : null}
              </span>
              <div>
                <strong>{contribution.label}</strong>
                <p>{contribution.description}</p>
              </div>
              <span>{contribution.package}</span>
            </button>
          ))}
        </div>
      )}
      {selected.map((contribution) => (
        <div className="phlo-workflow-form-grid" key={contribution.id}>
          {contribution.fields.map((field) => (
            <DynamicField
              contributionId={contribution.id}
              field={field}
              key={field.name}
              onChange={onFieldChange}
              value={values[contribution.id]?.[field.name] ?? ''}
            />
          ))}
        </div>
      ))}
    </section>
  )
}

function DynamicField({
  contributionId,
  field,
  value,
  onChange,
}: {
  contributionId: string
  field: V2WorkflowWizardField
  value: string
  onChange: (contributionId: string, field: string, value: string) => void
}) {
  const common = {
    onChange: (
      event: ChangeEvent<
        HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
      >,
    ) => onChange(contributionId, field.name, event.target.value),
    placeholder: field.description ?? field.label,
    value,
  }
  return (
    <label className="phlo-workflow-field">
      <span>
        {field.label}
        {field.required ? ' *' : ''}
      </span>
      {field.description && <small>{field.description}</small>}
      {field.field_type === 'select' ? (
        <select className="phlo-workflow-input" {...common}>
          {field.options.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      ) : field.field_type === 'fields' || field.field_type === 'textarea' ? (
        <textarea className="phlo-workflow-input" rows={3} {...common} />
      ) : (
        <input className="phlo-workflow-input" type="text" {...common} />
      )}
    </label>
  )
}

function ReviewPanel({
  proposal,
  actionMessage,
  loading,
  onGenerate,
  onRunAction,
}: {
  proposal: V2ResourceResult<V2WorkflowProposal>
  actionMessage: string | null
  loading: boolean
  onGenerate: () => void
  onRunAction: (action: V2WorkflowApplyAction) => void
}) {
  if (proposal.error) {
    return (
      <div className="phlo-v2-panel phlo-workflow-review-card">
        <div className="phlo-v2-panel-header phlo-workflow-review-header">
          <div>
            <h2>Review</h2>
            <p>Proposal generation needs attention.</p>
          </div>
        </div>
        <div className="phlo-v2-panel-footer">{proposal.error}</div>
        <button
          className="phlo-v2-primary-button phlo-workflow-apply"
          disabled={loading}
          onClick={onGenerate}
        >
          <FileCode2 className="size-4" />
          {loading ? 'Generating proposal...' : 'Try again'}
        </button>
      </div>
    )
  }
  if (!proposal.data) {
    return (
      <div className="phlo-v2-panel phlo-workflow-review-card">
        <div className="phlo-v2-panel-header phlo-workflow-review-header">
          <div>
            <h2>Review</h2>
            <p>Generated files and guarded actions appear here.</p>
          </div>
          <FileCode2 className="size-4" aria-hidden />
        </div>
        <div className="phlo-workflow-empty-review">
          {loading
            ? 'Generating a proposal from the selected package contributions...'
            : 'Generate a proposal to preview the files before anything is written.'}
        </div>
        <button
          className="phlo-v2-primary-button phlo-workflow-apply"
          disabled={loading}
          onClick={onGenerate}
        >
          <FileCode2 className="size-4" />
          {loading ? 'Generating proposal...' : 'Generate proposal'}
        </button>
      </div>
    )
  }

  return (
    <div className="phlo-v2-panel phlo-workflow-review-card">
      <div className="phlo-v2-panel-header phlo-workflow-review-header">
        <div>
          <h2>Review proposal</h2>
          <p>
            {proposal.data.planned_assets.length} asset,{' '}
            {proposal.data.planned_models.length} model
          </p>
        </div>
        <span className="phlo-v2-pill">{proposal.data.files.length} files</span>
      </div>
      <div className="phlo-workflow-file-list">
        {proposal.data.files.map((file) => (
          <details className="phlo-workflow-file" key={file.path}>
            <summary>
              <FileCode2 className="size-4" />
              <span>{file.path}</span>
              <em>{file.mode}</em>
            </summary>
            <pre>{file.content}</pre>
          </details>
        ))}
      </div>
      {proposal.data.warnings.map((warning) => (
        <div className="phlo-v2-panel-footer" key={warning}>
          {warning}
        </div>
      ))}
      {proposal.data.actions.map((action) => (
        <button
          className="phlo-v2-primary-button phlo-workflow-apply"
          disabled={loading || !action.enabled}
          key={action.id}
          onClick={() => onRunAction(action)}
        >
          <CheckCircle2 className="size-4" />
          {action.label}
        </button>
      ))}
      <button
        className="phlo-workflow-secondary-action"
        disabled={loading}
        onClick={onGenerate}
      >
        {loading ? 'Refreshing proposal...' : 'Refresh proposal'}
      </button>
      {actionMessage && (
        <div className="phlo-v2-panel-footer">{actionMessage}</div>
      )}
    </div>
  )
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="phlo-v2-diff-metric phlo-workflow-metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function stageDescription(stage: string) {
  if (stage === 'source') return 'Choose where the workflow starts.'
  if (stage === 'transform')
    return 'Compose dbt setup, sources, models, tests, and docs.'
  if (stage === 'quality')
    return 'Attach validation when a provider contributes it.'
  if (stage === 'publish') return 'Expose downstream outputs when available.'
  return ''
}

function toggleStageSelection(
  stage: string,
  current: Array<string>,
  id: string,
) {
  if (stage === 'source') return [id]
  if (current.includes(id)) return current.filter((item) => item !== id)
  return [...current, id]
}

function groupByStage(contributions: Array<V2WorkflowWizardContribution>) {
  return contributions.reduce<
    Record<string, Array<V2WorkflowWizardContribution>>
  >((groups, contribution) => {
    groups[contribution.stage] = groups[contribution.stage] ?? []
    groups[contribution.stage].push(contribution)
    return groups
  }, {})
}

function defaultValues(contributions: Array<V2WorkflowWizardContribution>) {
  return contributions.reduce<FormValues>((next, contribution) => {
    next[contribution.id] = contribution.fields.reduce<Record<string, string>>(
      (fieldValues, field) => {
        fieldValues[field.name] =
          field.default === undefined || field.default === null
            ? defaultFieldValue(field)
            : String(field.default)
        return fieldValues
      },
      {},
    )
    return next
  }, {})
}

function defaultFieldValue(field: V2WorkflowWizardField) {
  if (field.name === 'domain') return 'customers'
  if (field.name === 'table_name') return 'orders'
  if (field.name === 'unique_key') return 'order_id'
  if (field.name === 'response_path') return ''
  if (field.name === 'pagination') return 'none'
  if (field.name === 'auth') return 'none'
  if (field.name === 'project_name') return 'analytics'
  if (field.name === 'source_name') return 'raw'
  if (field.name === 'model_name') return 'stg_orders'
  if (field.name === 'source_relation') return 'raw.orders'
  if (field.name === 'fields') return 'total:float\ncreated_at:datetime'
  return ''
}
