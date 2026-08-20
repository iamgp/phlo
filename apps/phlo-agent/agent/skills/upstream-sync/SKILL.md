---
name: upstream-sync
description: Check the Phlo agent's Eve ecosystem dependencies for relevant updates and open a bounded draft PR or issue. Load when the upstream-sync schedule fires.
---

# Upstream sync

Compare installed and current releases of `eve`, `@agent-browser/eve`,
`@github-tools/eve-extension`, `@vercel/connect`, the Vercel AI SDK, and
`@vercel/before-and-after`. Read release notes and installed documentation for
behavior changes that affect `apps/phlo-agent`.

Search existing issues and pull requests first. Ignore version churn with no
effect on this agent.

- If an update is compatible and its required adaptation is mechanical, create
  one feature branch, update the dependency and code, run `npm ci`, typecheck,
  and build, commit, call `git__push`, and open a **draft** pull request.
- If an update requires a product or security decision, create one focused
  GitHub issue explaining the release, affected files, risk, and decision.
- If nothing warrants action, create nothing.

Never merge, publish, release, or open more than one artifact per run.
