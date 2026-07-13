import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const apiGet = vi.fn()
const apiPost = vi.fn()

vi.mock('@/server/phlo-api', () => ({
  apiGet,
  apiPost,
}))

describe('observatory dataset resources', () => {
  beforeEach(() => {
    apiGet.mockReset()
    apiPost.mockReset()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('fetches Dataset records from phlo-api', async () => {
    apiGet.mockResolvedValue({
      items: [
        {
          id: 'gold.orders',
          name: 'gold.orders',
          classifications: ['internal'],
          publication_state: 'published',
          readiness_state: 'ok',
          candidate: false,
          kinds: ['table'],
          source_refs: [],
          metadata: {},
        },
      ],
    })

    const { getObservatoryDatasetRecords } = await import('./resources')
    const result = await getObservatoryDatasetRecords()

    expect(result.error).toBeNull()
    expect(result.data).toEqual([
      expect.objectContaining({
        id: 'gold.orders',
        publication_state: 'published',
      }),
    ])
    expect(apiGet).toHaveBeenCalledWith(
      '/api/observatory/datasets',
      undefined,
      8000,
    )
  })

  it('creates workflow proposals through the server API during SSR', async () => {
    const proposal = workflowProposal()
    apiPost.mockResolvedValue(proposal)

    const { createObservatoryWorkflowProposal } = await import('./resources')
    const request = workflowProposalRequest()
    const result = await createObservatoryWorkflowProposal({ data: request })

    expect(result).toEqual({ data: proposal, error: null })
    expect(apiPost).toHaveBeenCalledWith(
      '/api/observatory/workflow-wizard/proposals',
      request,
      12000,
    )
  })

  it('creates workflow proposals through the browser API in the client', async () => {
    const proposal = workflowProposal()
    const fetchMock = stubBrowserPost(proposal)

    const { createObservatoryWorkflowProposal } = await import('./resources')
    const request = workflowProposalRequest()
    const result = await createObservatoryWorkflowProposal({ data: request })

    expect(result).toEqual({ data: proposal, error: null })
    expect(fetchMock).toHaveBeenCalledWith(
      'https://api.example.test/api/observatory/workflow-wizard/proposals',
      expect.objectContaining({
        body: JSON.stringify(request),
        method: 'POST',
      }),
    )
  })

  it('runs workflow actions through the server API during SSR', async () => {
    const proposal = workflowProposal()
    const actionResult = workflowActionResult()
    apiPost.mockResolvedValue(actionResult)

    const { runObservatoryWorkflowAction } = await import('./resources')
    const result = await runObservatoryWorkflowAction({
      data: { actionId: 'apply', proposal },
    })

    expect(result).toEqual({ data: actionResult, error: null })
    expect(apiPost).toHaveBeenCalledWith(
      '/api/observatory/workflow-wizard/actions',
      { action_id: 'apply', proposal_id: proposal.proposal_id },
      12000,
    )
  })

  it('runs workflow actions through the browser API in the client', async () => {
    const proposal = workflowProposal()
    const actionResult = workflowActionResult()
    const fetchMock = stubBrowserPost(actionResult)

    const { runObservatoryWorkflowAction } = await import('./resources')
    const result = await runObservatoryWorkflowAction({
      data: { actionId: 'apply', proposal },
    })

    expect(result).toEqual({ data: actionResult, error: null })
    expect(fetchMock).toHaveBeenCalledWith(
      'https://api.example.test/api/observatory/workflow-wizard/actions',
      expect.objectContaining({
        body: JSON.stringify({
          action_id: 'apply',
          proposal_id: proposal.proposal_id,
        }),
        method: 'POST',
      }),
    )
  })
})

function workflowProposalRequest() {
  return {
    domain: 'finance',
    graph: { edges: [], nodes: [] },
    workflow_name: 'Revenue refresh',
  }
}

function workflowProposal() {
  return {
    actions: [],
    disabled_stages: {},
    domain: 'finance',
    files: [],
    missing_capabilities: [],
    planned_assets: [],
    planned_models: [],
    planned_tables: [],
    selected_contributions: [],
    warnings: [],
    workflow_name: 'Revenue refresh',
    proposal_id: 'proposal_1234567890',
  }
}

function workflowActionResult() {
  return {
    action_id: 'apply',
    files: [],
    message: 'Applied',
    status: 'succeeded' as const,
  }
}

function stubBrowserPost(payload: unknown) {
  vi.stubGlobal('window', {
    __PHLO_API_BROWSER_URL__: 'https://api.example.test',
    clearTimeout: globalThis.clearTimeout,
    setTimeout: globalThis.setTimeout,
  })
  const fetchMock = vi.fn().mockResolvedValue({
    json: vi.fn().mockResolvedValue(payload),
    ok: true,
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}
