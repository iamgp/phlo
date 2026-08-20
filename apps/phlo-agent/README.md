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
Eve: Functions, Workflows, and Sandbox. Configure spend alerts before enabling
GitHub webhooks or unattended schedules.

Current prices and eligibility can change. Check the
[AI Gateway pricing page](https://vercel.com/docs/ai-gateway/pricing) and the
DeepSeek V4 Flash model page in the Vercel dashboard before setting a budget.

## Deferred automation

Evi's unattended issue triage, repository-health sweep, upstream dependency
sync, Linear reporting, memory, telemetry, and automatic pull requests are not
enabled in this first deployment. They require explicit trust policy,
destinations, schedules, and spend limits. Add them after the GitHub identity
and approval flow have been exercised interactively.
