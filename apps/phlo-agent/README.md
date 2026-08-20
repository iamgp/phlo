# Phlo agent

An [Eve](https://eve.dev)-based engineering agent for the Phlo ecosystem,
inspired by [Evi](https://github.com/hugorcd/evlog/tree/main/apps/evi).

The initial setup includes:

- DeepSeek V4 Flash for text and Qwen 3.7 Flash for turns containing images
- Vercel AI Gateway routing with caching, zero-data-retention, and usage tags
- a GitHub channel and GitHub tools scoped to `phlohouse/phlo`
- Agent Browser and the `before-and-after` CLI for visual verification
- an isolated Vercel Sandbox containing a shallow Phlo checkout
- approval-gated GitHub writes through the GitHub Tools extension
- autonomous repository-health and Eve dependency maintenance schedules
- guarded feature-branch pushes and draft pull requests from scheduled runs

## Autonomous maintenance

The agent runs two proactive workflows after deployment:

| Workflow | UTC schedule | Outcome |
| --- | --- | --- |
| Repository health | Tuesday and Friday, 08:00 | Grounded documentation, example, test, CI, and convention findings |
| Eve upstream sync | Monday and Thursday, 07:00 | Relevant agent dependency updates and migration findings |

Each run searches existing issues and pull requests first. A mechanical,
low-risk fix may become a verified **draft** pull request. A finding that needs
product judgment may become a focused issue. Runs create nothing when there is
no grounded work, and each skill limits how many artifacts one run can produce.

The schedule identity can push feature branches, create issues, and open draft
pull requests. It cannot push `main` or `master`, open a non-draft PR without
approval, merge, publish, release, or modify secrets. Git credentials are
injected by the sandbox network broker and are never exposed to its processes.

## Local setup

Requires Node.js 24 or newer.

```bash
cd apps/phlo-agent
npm ci
cp .env.example .env.local
# Add AI_GATEWAY_API_KEY to .env.local.
npm run dev
```

Installing and type-checking do not call a model. `npm run dev` starts using AI
Gateway credit when you send the first prompt.

`PHLO_AGENT_MODEL` and `PHLO_AGENT_VISION_MODEL` can override the defaults
without changing source.

## Connect GitHub and deploy

The checked-in connector name is `github/phlo-agent`. Provision that connector
and its GitHub App interactively, then install the app on `phlohouse/phlo`:

```bash
cd apps/phlo-agent
npx eve add channel/github
npx eve link
npx eve deploy
```

The generated/provisioned channel must keep the connector name
`github/phlo-agent`. If the available GitHub App name is not `phlo-agent`, set
`PHLO_AGENT_GITHUB_BOT` to the selected app slug in the Vercel project.

The GitHub App installation needs repository contents, issues, and pull request
write access so scheduled runs can push feature branches and deliver proposals.

Deployment and connector provisioning change shared Vercel and GitHub state,
so they are intentionally not performed by repository setup.

## Billing

No billing setup is required to install, build, or type-check the agent. A
model credential is required before the first interactive prompt.

Vercel AI Gateway provides a monthly free-credit tier for eligible models.
DeepSeek V4 Flash is billed per token at the provider's list price with no
Gateway markup. Add paid AI Gateway credits when either:

1. the model is not eligible for the free tier on the team at execution time,
2. free-tier rate limits block the workload, or
3. the free balance is exhausted.

Buying credits moves the team to AI Gateway's paid tier and ends its monthly
free-credit allocation. Production also consumes the Vercel resources used by
Eve: Functions, Workflows, and Sandbox. Configure spend alerts before deploying:
the four weekly scheduled runs begin automatically once Vercel enables the cron
jobs.

Current prices and eligibility can change. Check the
[AI Gateway pricing page](https://vercel.com/docs/ai-gateway/pricing) and the
DeepSeek V4 Flash model page in the Vercel dashboard before setting a budget.

## Deferred capabilities

Automatic first-response triage on every new community issue, Linear reporting,
long-term memory, telemetry, automatic merging, and releases are not enabled.
