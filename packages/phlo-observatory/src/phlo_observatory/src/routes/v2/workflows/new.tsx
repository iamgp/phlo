import { createFileRoute } from '@tanstack/react-router'
import { Button, IconButton } from '@primer/react'
import {
  ArrowDownIcon,
  ArrowUpIcon,
  CheckCircleIcon,
  FileCodeIcon,
  PlusIcon,
  TrashIcon,
} from '@primer/octicons-react'
import { WandSparkles } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import type { ChangeEvent, ReactNode } from 'react'

import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import type {
  V2ResourceResult,
  V2WorkflowApplyAction,
  V2WorkflowGraph,
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
  component: WorkflowCanvasBuilder,
})

type WorkflowNodeData = {
  contributionId: string
  description: string
  label: string
  packageName: string
  stage: 'source' | 'transform' | 'quality' | 'publish'
}

type WorkflowNode = {
  id: string
  data: WorkflowNodeData
}
type FormValues = Record<string, Record<string, string>>
type WizardStep = 'info' | 'graph' | 'proposal'

const STAGE_LABELS: Record<string, string> = {
  source: 'Source',
  transform: 'Transform',
  quality: 'Quality',
  publish: 'Publish',
}

const WORKFLOW_STEPS: Array<{
  id: WizardStep
  label: string
  description: string
}> = [
  {
    id: 'info',
    label: 'Workflow info',
    description: 'Name and domain',
  },
  {
    id: 'graph',
    label: 'Build graph',
    description: 'Pipeline nodes',
  },
  {
    id: 'proposal',
    label: 'Review proposal',
    description: 'Files and apply action',
  },
]

function WorkflowCanvasBuilder() {
  const [wizard, setWizard] = useState<
    V2ResourceResult<V2WorkflowWizardPayload>
  >({
    data: null,
    error: null,
  })
  const [nodes, setNodes] = useState<Array<WorkflowNode>>([])
  const [values, setValues] = useState<FormValues>({})
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [insertIndex, setInsertIndex] = useState<number | null>(null)
  const [addMenuOpen, setAddMenuOpen] = useState(false)
  const [inspectorOpen, setInspectorOpen] = useState(false)
  const [workflowName, setWorkflowName] = useState('recipe_catalog')
  const [domain, setDomain] = useState('recipes')
  const [activeStep, setActiveStep] = useState<WizardStep>('info')
  const [proposal, setProposal] = useState<
    V2ResourceResult<V2WorkflowProposal>
  >({
    data: null,
    error: null,
  })
  const [proposalLoading, setProposalLoading] = useState(false)
  const [actionMessage, setActionMessage] = useState<string | null>(null)
  const activeStepIndex = WORKFLOW_STEPS.findIndex(
    (step) => step.id === activeStep,
  )

  useEffect(() => {
    let cancelled = false
    void loadCachedResource('v2:workflow-wizard', getV2WorkflowWizard, {
      force: true,
      staleMs: 60_000,
    }).then((next) => {
      if (cancelled) return
      setWizard(next)
      const contributions = next.data?.contributions ?? []
      const starterNodes = starterGraph(contributions).nodes
      setNodes(starterNodes)
      setValues(starterValues(contributions, starterNodes))
      setSelectedNodeId(starterNodes[0]?.id ?? null)
      setInsertIndex(starterNodes.length)
    })
    return () => {
      cancelled = true
    }
  }, [])

  const contributions = wizard.data?.contributions ?? []
  const contributionById = useMemo(
    () => new Map(contributions.map((item) => [item.id, item])),
    [contributions],
  )
  const selectedNode = nodes.find((node) => node.id === selectedNodeId) ?? null
  const selectedContribution = selectedNode
    ? contributionById.get(selectedNode.data.contributionId)
    : null

  function addContribution(contribution: V2WorkflowWizardContribution) {
    const nodeId = `${contribution.id}-${crypto.randomUUID()}`
    const node = toCanvasNode(contribution, nodeId)
    setNodes((current) => {
      const next = [...current]
      const targetIndex =
        insertIndex === null
          ? current.length
          : Math.max(0, Math.min(insertIndex, current.length))
      next.splice(targetIndex, 0, node)
      setInsertIndex(targetIndex + 1)
      return next
    })
    setValues((current) => ({
      ...current,
      [nodeId]: defaultsForContribution(contribution),
    }))
    setSelectedNodeId(nodeId)
    setInspectorOpen(true)
    setAddMenuOpen(false)
  }

  function removeNode(nodeId: string) {
    setNodes((current) => {
      const next = current.filter((node) => node.id !== nodeId)
      setInsertIndex(Math.min(insertIndex ?? next.length, next.length))
      return next
    })
    setValues((current) => {
      const next = { ...current }
      delete next[nodeId]
      return next
    })
    if (selectedNodeId === nodeId) {
      setSelectedNodeId(null)
      setInspectorOpen(false)
    }
  }

  function moveNode(nodeId: string, direction: -1 | 1) {
    setNodes((current) => {
      const index = current.findIndex((node) => node.id === nodeId)
      const target = index + direction
      if (index < 0 || target < 0 || target >= current.length) return current
      const next = [...current]
      const [node] = next.splice(index, 1)
      next.splice(target, 0, node)
      setInsertIndex(target + 1)
      return next
    })
  }

  function updateNodeField(nodeId: string, field: string, value: string) {
    setValues((current) => ({
      ...current,
      [nodeId]: {
        ...(current[nodeId] ?? {}),
        [field]: value,
      },
    }))
  }

  function buildGraph(): V2WorkflowGraph {
    return {
      nodes: nodes.map((node) => ({
        id: node.id,
        contribution_id: node.data.contributionId,
        stage: node.data.stage,
        values: values[node.id] ?? {},
      })),
      edges: nodes.slice(0, -1).map((node, index) => ({
        id: `${node.id}-${nodes[index + 1].id}`,
        source: node.id,
        target: nodes[index + 1].id,
      })),
    }
  }

  function generateProposal() {
    setActionMessage(null)
    setProposalLoading(true)
    void createV2WorkflowProposal({
      data: {
        workflow_name: workflowName,
        domain,
        graph: buildGraph(),
      },
    })
      .then((next) => {
        setProposal(next)
        setActiveStep('proposal')
      })
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
      description="Compose package-provided workflow nodes, configure each step, preview generated files, then apply guarded actions."
      kicker="Workflows"
      title="New workflow"
    >
      {wizard.error && <div className="phlo-v2-callout">{wizard.error}</div>}

      <nav className="phlo-workflow-stepper" aria-label="Workflow wizard steps">
        {WORKFLOW_STEPS.map((step, index) => (
          <Button
            alignContent="start"
            block
            className="phlo-workflow-step"
            data-active={activeStep === step.id}
            data-complete={index < activeStepIndex}
            key={step.id}
            onClick={() => setActiveStep(step.id)}
            type="button"
          >
            <span className="phlo-workflow-step-index">{index + 1}</span>
            <span className="phlo-workflow-step-copy">
              <strong>{step.label}</strong>
              <em>{step.description}</em>
            </span>
          </Button>
        ))}
      </nav>

      {activeStep === 'info' && (
        <section className="phlo-v2-panel phlo-workflow-step-panel">
          <div className="phlo-v2-panel-header phlo-workflow-card-header">
            <div>
              <h2>Workflow info</h2>
              <p>Set the workflow identity before arranging package nodes.</p>
            </div>
            <WandSparkles className="size-4" aria-hidden />
          </div>
          <div className="phlo-workflow-info-grid">
            <label>
              <span>Workflow</span>
              <input
                className="phlo-workflow-input"
                onChange={(event) => setWorkflowName(event.target.value)}
                value={workflowName}
              />
            </label>
            <label>
              <span>Domain</span>
              <input
                className="phlo-workflow-input"
                onChange={(event) => setDomain(event.target.value)}
                value={domain}
              />
            </label>
          </div>
          <div className="phlo-workflow-step-actions">
            <Button
              className="phlo-workflow-action"
              onClick={() => setActiveStep('graph')}
              type="button"
              variant="primary"
            >
              Continue to graph
            </Button>
          </div>
        </section>
      )}

      {activeStep === 'graph' && (
        <section className="phlo-workflow-graph-step">
          <div
            className="phlo-workflow-canvas-main"
            data-inspector-open={Boolean(
              inspectorOpen && selectedNode && selectedContribution,
            )}
          >
            <div className="phlo-workflow-canvas-toolbar">
              <Button
                className="phlo-workflow-action"
                disabled={proposalLoading}
                leadingVisual={FileCodeIcon}
                onClick={generateProposal}
                type="button"
                variant="primary"
              >
                {proposalLoading ? 'Generating...' : 'Generate proposal'}
              </Button>
            </div>
            <PipelineLane
              addMenuOpen={addMenuOpen}
              contributions={contributions}
              insertIndex={insertIndex ?? nodes.length}
              nodes={nodes}
              onAddContribution={addContribution}
              onCloseAddMenu={() => setAddMenuOpen(false)}
              onMoveNode={moveNode}
              onRemoveNode={removeNode}
              onSelectInsert={(index) => {
                setInsertIndex(index)
                setAddMenuOpen(true)
              }}
              onSelectNode={(nodeId) => {
                setSelectedNodeId(nodeId)
                setInspectorOpen(true)
              }}
              selectedNodeId={selectedNodeId}
            />
            {inspectorOpen && selectedNode && selectedContribution ? (
              <aside className="phlo-workflow-inspector">
                <Button
                  className="phlo-workflow-inspector-close"
                  onClick={() => setInspectorOpen(false)}
                  size="small"
                  type="button"
                >
                  Close
                </Button>
                <Inspector
                  contribution={selectedContribution}
                  node={selectedNode}
                  onChange={updateNodeField}
                  values={selectedNode ? (values[selectedNode.id] ?? {}) : {}}
                />
              </aside>
            ) : null}
          </div>
        </section>
      )}

      {activeStep === 'proposal' && (
        <section className="phlo-workflow-proposal-step">
          <ReviewPanel
            actionMessage={actionMessage}
            loading={proposalLoading}
            onGenerate={generateProposal}
            onRunAction={runAction}
            proposal={proposal}
          />
        </section>
      )}
    </V2Page>
  )
}

function PipelineLane({
  nodes,
  contributions,
  insertIndex,
  addMenuOpen,
  selectedNodeId,
  onAddContribution,
  onCloseAddMenu,
  onMoveNode,
  onRemoveNode,
  onSelectInsert,
  onSelectNode,
}: {
  nodes: Array<WorkflowNode>
  contributions: Array<V2WorkflowWizardContribution>
  insertIndex: number
  addMenuOpen: boolean
  selectedNodeId: string | null
  onAddContribution: (contribution: V2WorkflowWizardContribution) => void
  onCloseAddMenu: () => void
  onMoveNode: (nodeId: string, direction: -1 | 1) => void
  onRemoveNode: (nodeId: string) => void
  onSelectInsert: (index: number) => void
  onSelectNode: (nodeId: string) => void
}) {
  const groupedContributions = useMemo(
    () =>
      (['source', 'transform', 'quality', 'publish'] as const).map((stage) => ({
        stage,
        items: contributions.filter((item) => item.stage === stage),
      })),
    [contributions],
  )

  return (
    <div className="phlo-workflow-canvas">
      <div className="phlo-workflow-lane" aria-label="Workflow pipeline">
        <InsertPoint
          active={insertIndex === 0}
          index={0}
          onOpenChange={(open) => {
            if (!open) onCloseAddMenu()
          }}
          onSelect={onSelectInsert}
        >
          {addMenuOpen && insertIndex === 0 ? (
            <AddStepMenu
              groupedContributions={groupedContributions}
              insertIndex={insertIndex}
              onAddContribution={onAddContribution}
              onCloseAddMenu={onCloseAddMenu}
            />
          ) : null}
        </InsertPoint>
        {nodes.map((node, index) => (
          <div className="phlo-workflow-lane-item" key={node.id}>
            <PipelineNode
              isFirst={index === 0}
              isLast={index === nodes.length - 1}
              node={node}
              onMoveNode={onMoveNode}
              onRemoveNode={onRemoveNode}
              onSelectNode={onSelectNode}
              selected={selectedNodeId === node.id}
            />
            <InsertPoint
              active={insertIndex === index + 1}
              index={index + 1}
              onOpenChange={(open) => {
                if (!open) onCloseAddMenu()
              }}
              onSelect={onSelectInsert}
            >
              {addMenuOpen && insertIndex === index + 1 ? (
                <AddStepMenu
                  groupedContributions={groupedContributions}
                  insertIndex={insertIndex}
                  onAddContribution={onAddContribution}
                  onCloseAddMenu={onCloseAddMenu}
                />
              ) : null}
            </InsertPoint>
          </div>
        ))}
      </div>
    </div>
  )
}

function AddStepMenu({
  groupedContributions,
  insertIndex,
  onAddContribution,
  onCloseAddMenu,
}: {
  groupedContributions: Array<{
    stage: 'source' | 'transform' | 'quality' | 'publish'
    items: Array<V2WorkflowWizardContribution>
  }>
  insertIndex: number
  onAddContribution: (contribution: V2WorkflowWizardContribution) => void
  onCloseAddMenu: () => void
}) {
  return (
    <div className="phlo-workflow-add-menu-surface">
      <div className="phlo-workflow-add-menu-header">
        <div>
          <h2>Add workflow step</h2>
          <p>Step will be inserted at position {insertIndex + 1}.</p>
        </div>
        <Button onClick={onCloseAddMenu} size="small" type="button">
          Close
        </Button>
      </div>
      <div className="phlo-workflow-add-menu-list">
        {groupedContributions.map((group) =>
          group.items.length ? (
            <section key={group.stage}>
              <h3>{STAGE_LABELS[group.stage]}</h3>
              {group.items.map((contribution) => (
                <Button
                  className="phlo-workflow-add-option"
                  key={contribution.id}
                  onClick={() => onAddContribution(contribution)}
                  type="button"
                >
                  <PlusIcon size={16} />
                  <span>
                    <strong>{contribution.label}</strong>
                    <em>{contribution.package}</em>
                  </span>
                </Button>
              ))}
            </section>
          ) : null,
        )}
      </div>
    </div>
  )
}

function InsertPoint({
  active,
  children,
  index,
  onOpenChange,
  onSelect,
}: {
  active: boolean
  children?: ReactNode
  index: number
  onOpenChange: (open: boolean) => void
  onSelect: (index: number) => void
}) {
  return (
    <Popover
      modal={false}
      onOpenChange={(nextOpen) => {
        if (!nextOpen) onOpenChange(false)
      }}
    >
      <div className="phlo-workflow-insert-point" data-active={active}>
        <PopoverTrigger
          aria-label={`Add workflow step at position ${index + 1}`}
          onClick={() => onSelect(index)}
          type="button"
        >
          <span />
          <em>+</em>
          <span />
        </PopoverTrigger>
        {active && children ? (
          <PopoverContent
            align="center"
            className="phlo-workflow-add-menu"
            side="right"
            sideOffset={18}
          >
            {children}
          </PopoverContent>
        ) : null}
      </div>
    </Popover>
  )
}

function PipelineNode({
  node,
  selected,
  isFirst,
  isLast,
  onMoveNode,
  onRemoveNode,
  onSelectNode,
}: {
  node: WorkflowNode
  selected: boolean
  isFirst: boolean
  isLast: boolean
  onMoveNode: (nodeId: string, direction: -1 | 1) => void
  onRemoveNode: (nodeId: string) => void
  onSelectNode: (nodeId: string) => void
}) {
  return (
    <article className="phlo-workflow-canvas-node" data-selected={selected}>
      <button
        className="phlo-workflow-node-select"
        onClick={() => onSelectNode(node.id)}
        type="button"
      >
        <span>{STAGE_LABELS[node.data.stage]}</span>
        <strong>{node.data.label}</strong>
        <p>{node.data.description}</p>
      </button>
      <div className="phlo-workflow-node-footer">
        <em>{node.data.packageName}</em>
        <div className="phlo-workflow-node-actions">
          <IconButton
            aria-label="Move node up"
            className="phlo-workflow-node-action"
            disabled={isFirst}
            icon={ArrowUpIcon}
            onClick={() => onMoveNode(node.id, -1)}
            size="small"
            title="Move up"
            type="button"
            variant="invisible"
          />
          <IconButton
            aria-label="Move node down"
            className="phlo-workflow-node-action"
            disabled={isLast}
            icon={ArrowDownIcon}
            onClick={() => onMoveNode(node.id, 1)}
            size="small"
            title="Move down"
            type="button"
            variant="invisible"
          />
          <IconButton
            aria-label="Remove node"
            className="phlo-workflow-node-action"
            icon={TrashIcon}
            onClick={() => onRemoveNode(node.id)}
            size="small"
            title="Remove"
            type="button"
            variant="invisible"
          />
        </div>
      </div>
    </article>
  )
}

function Inspector({
  node,
  contribution,
  values,
  onChange,
}: {
  node: WorkflowNode | null
  contribution: V2WorkflowWizardContribution | null | undefined
  values: Record<string, string>
  onChange: (nodeId: string, field: string, value: string) => void
}) {
  if (!node || !contribution) {
    return (
      <div className="phlo-v2-panel phlo-workflow-inspector-card">
        <div className="phlo-workflow-pane-header">
          <h2>Inspector</h2>
        </div>
        <p>Select a node to configure it.</p>
      </div>
    )
  }

  return (
    <div className="phlo-v2-panel phlo-workflow-inspector-card">
      <div className="phlo-workflow-pane-header">
        <div>
          <h2>{contribution.label}</h2>
          <p>{contribution.description}</p>
        </div>
        <span className="phlo-v2-pill">{contribution.package}</span>
      </div>
      <div className="phlo-workflow-inspector-fields">
        {contribution.fields.map((field) => (
          <DynamicField
            field={field}
            key={field.name}
            nodeId={node.id}
            onChange={onChange}
            value={values[field.name] ?? ''}
          />
        ))}
      </div>
    </div>
  )
}

function DynamicField({
  nodeId,
  field,
  value,
  onChange,
}: {
  nodeId: string
  field: V2WorkflowWizardField
  value: string
  onChange: (nodeId: string, field: string, value: string) => void
}) {
  const common = {
    onChange: (
      event: ChangeEvent<
        HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
      >,
    ) => onChange(nodeId, field.name, event.target.value),
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
        <textarea className="phlo-workflow-input" rows={4} {...common} />
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
        <Button
          className="phlo-workflow-action phlo-workflow-apply"
          disabled={loading}
          leadingVisual={FileCodeIcon}
          onClick={onGenerate}
          type="button"
          variant="primary"
        >
          {loading ? 'Generating proposal...' : 'Try again'}
        </Button>
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
          <FileCodeIcon aria-hidden size={16} />
        </div>
        <div className="phlo-workflow-empty-review">
          {loading
            ? 'Generating a proposal from the graph...'
            : 'Generate a proposal to preview graph-generated files.'}
        </div>
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
            {proposal.data.planned_models.length} models
          </p>
        </div>
        <span className="phlo-v2-pill">{proposal.data.files.length} files</span>
      </div>
      <div className="phlo-workflow-file-list">
        {proposal.data.files.map((file) => (
          <details className="phlo-workflow-file" key={file.path}>
            <summary>
              <FileCodeIcon size={16} />
              <span>{file.path}</span>
              <em>{file.mode}</em>
            </summary>
            <pre>{file.content}</pre>
          </details>
        ))}
      </div>
      {proposal.data.actions.map((action) => (
        <Button
          className="phlo-workflow-action phlo-workflow-apply"
          disabled={loading || !action.enabled}
          key={action.id}
          leadingVisual={CheckCircleIcon}
          onClick={() => onRunAction(action)}
          type="button"
          variant="primary"
        >
          {action.label}
        </Button>
      ))}
      <Button
        className="phlo-workflow-secondary-action"
        disabled={loading}
        onClick={onGenerate}
        type="button"
      >
        {loading ? 'Refreshing proposal...' : 'Refresh proposal'}
      </Button>
      {actionMessage && (
        <div className="phlo-v2-panel-footer">{actionMessage}</div>
      )}
    </div>
  )
}

function starterGraph(contributions: Array<V2WorkflowWizardContribution>) {
  const ids = [
    'dlt.rest-api-source',
    'dbt.transform',
    'pandera.quality-checks',
    'dagster.orchestration',
    'openmetadata.catalog',
  ]
  const selected = ids
    .map((id) => contributions.find((contribution) => contribution.id === id))
    .filter((item): item is V2WorkflowWizardContribution => Boolean(item))
  const nodes = selected.map((contribution, index) =>
    toCanvasNode(contribution, `node-${index + 1}`),
  )
  return { nodes }
}

function toCanvasNode(
  contribution: V2WorkflowWizardContribution,
  id: string,
): WorkflowNode {
  return {
    id,
    data: {
      contributionId: contribution.id,
      description: contribution.description,
      label: contribution.label,
      packageName: contribution.package,
      stage: contribution.stage,
    },
  }
}

function starterValues(
  contributions: Array<V2WorkflowWizardContribution>,
  nodes: Array<WorkflowNode>,
) {
  return nodes.reduce<FormValues>((current, node) => {
    const contribution = contributions.find(
      (item) => item.id === node.data.contributionId,
    )
    current[node.id] = contribution ? defaultsForContribution(contribution) : {}
    return current
  }, {})
}

function defaultsForContribution(contribution: V2WorkflowWizardContribution) {
  return contribution.fields.reduce<Record<string, string>>(
    (current, field) => {
      current[field.name] =
        field.default === undefined || field.default === null
          ? defaultFieldValue(contribution.id, field)
          : String(field.default)
      return current
    },
    {},
  )
}

function defaultFieldValue(
  contributionId: string,
  field: V2WorkflowWizardField,
) {
  if (field.name === 'domain') return 'recipes'
  if (field.name === 'table_name') return 'recipes'
  if (field.name === 'unique_key') return 'id'
  if (field.name === 'api_base_url') return 'https://dummyjson.com/recipes'
  if (field.name === 'response_path') return 'recipes'
  if (field.name === 'pagination') return 'none'
  if (field.name === 'auth') return 'none'
  if (field.name === 'cron') return '0 2 * * *'
  if (field.name === 'schedule') return '0 2 * * *'
  if (field.name === 'fields') {
    return 'name:str\ningredients:str\ninstructions:str\nprepTimeMinutes:int\ncookTimeMinutes:int\nservings:int\ndifficulty:str\ncuisine:str\ncaloriesPerServing:int\ntags:str\nrating:float\nreviewCount:int\nmealType:str'
  }
  if (field.name === 'source_name') return 'raw'
  if (field.name === 'source_stream') return 'public.recipes'
  if (field.name === 'target_table') return 'recipes'
  if (field.name === 'primary_key') return 'id'
  if (field.name === 'replication_mode') return 'incremental'
  if (field.name === 'update_key') return 'updated_at'
  if (field.name === 'project_name') return 'recipe_catalog'
  if (field.name === 'source_table') return 'recipes'
  if (field.name === 'staging_model_name') return 'stg_recipes'
  if (field.name === 'staging_source_relation') return 'raw.recipes'
  if (field.name === 'enable_rename') return 'no'
  if (field.name === 'enable_cast') return 'no'
  if (field.name === 'enable_aggregate') return 'no'
  if (contributionId === 'dbt.basic-model' && field.name === 'model_name')
    return 'stg_recipes'
  if (contributionId === 'dbt.basic-model' && field.name === 'source_relation')
    return 'raw.recipes'
  if (contributionId === 'dbt.source-yml' && field.name === 'source_name')
    return 'raw'
  if (contributionId === 'dbt.schema-tests' && field.name === 'model_name')
    return 'clean_recipes'
  if (contributionId === 'dbt.filter-rows' && field.name === 'model_name')
    return 'filtered_recipes'
  if (contributionId === 'dbt.filter-rows' && field.name === 'source_relation')
    return "ref('stg_recipes')"
  if (contributionId === 'dbt.filter-rows' && field.name === 'where')
    return 'rating >= 4.5'
  if (contributionId === 'dbt.transform' && field.name === 'where')
    return 'rating >= 4.5'
  if (field.name === 'filter_model_name') return 'filtered_recipes'
  if (field.name === 'dedupe_model_name') return 'clean_recipes'
  if (field.name === 'test_model_name') return 'clean_recipes'
  if (contributionId === 'dbt.deduplicate' && field.name === 'model_name')
    return 'clean_recipes'
  if (contributionId === 'dbt.deduplicate' && field.name === 'source_relation')
    return "ref('filtered_recipes')"
  if (field.name === 'partition_by') return 'id'
  if (field.name === 'order_by') return 'reviewCount'
  if (field.name === 'renames')
    return 'name:recipe_name\ncaloriesPerServing:calories_per_serving'
  if (field.name === 'casts') return 'rating:double\nreviewCount:integer'
  if (field.name === 'group_by') return 'cuisine'
  if (field.name === 'metrics')
    return 'recipe_count:count(*)\navg_rating:avg(rating)'
  if (field.name === 'check_name') return 'clean_recipes_quality'
  if (field.name === 'not_null_columns') return 'id\nname\ncuisine'
  if (field.name === 'range_checks') return 'rating:0:5\nreviewCount:0:100000'
  if (field.name === 'freshness_column') return 'updated_at'
  if (field.name === 'freshness_hours') return '24'
  if (field.name === 'min_rows') return '1'
  if (field.name === 'job_name') return 'recipe_catalog_job'
  if (field.name === 'asset_group') return 'recipes'
  if (field.name === 'include_sensor') return 'no'
  if (field.name === 'service_name') return 'phlo'
  if (field.name === 'database') return 'warehouse'
  if (field.name === 'schema') return 'recipes'
  if (field.name === 'owner') return 'data-platform'
  if (field.name === 'tags') return 'domain.recipes\nsource.dummyjson'
  if (field.name === 'description')
    return 'Catalog metadata for the recipe workflow generated from DummyJSON recipes.'
  if (field.name === 'source_relation') return "ref('clean_recipes')"
  if (field.name === 'model_name') return 'recipe_model'
  return ''
}
