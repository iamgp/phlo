---
cron: "0 8 * * 2,4"
---

Run Phlo's scheduled maintenance pass. Load and execute both the upstream-sync
and repo-health skills against current main. Search existing issues and pull
requests before proposing anything. Across both procedures, create at most two
artifacts total, and only grounded GitHub issues or verified draft pull
requests. Create nothing when no action is warranted.
