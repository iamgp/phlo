---
cron: "0 8 * * 2,4"
---

Run Phlo's scheduled maintenance pass. Load and execute both the upstream-sync
and repo-health skills against current main. The upstream pass covers Phlo's
lakehouse ecosystem dependencies and runtime images, with the agent's own Eve
dependencies as a secondary area. Search existing issues, Renovate work, and
pull requests before proposing anything. Across both procedures, create at most
two artifacts total, and only grounded GitHub issues or verified draft pull
requests. If autonomous writes are disabled, complete the audit without trying
to deliver an artifact. Create nothing when no action is warranted.
