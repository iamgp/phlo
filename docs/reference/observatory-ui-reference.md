# Observatory UI Reference

Use this reference with `$impeccable` whenever Observatory pages, workflows, or visual details are changed.

## Product Standard

Observatory is a lakehouse control plane. It should feel like GitHub and DiffKit: dense, calm, precise, and built for repeated operational use. It is not a marketing dashboard and should not use decorative cards, soft SaaS hero language, or ornamental color.

Every page should answer:

- what is wrong
- why it matters
- who owns it
- what evidence exists
- what action is next

## Canonical Vocabulary

- Dataset: governed or publishable data offering.
- Table: physical or queryable table.
- Lineage: dependency and impact graph.
- Quality check: executable evidence about trust.
- Operation: recoverable runtime action or failure.
- Run: orchestrator execution history.
- Publishing: internal release/readiness state.
- Governance: owners, classifications, approvals, and controls.
- Change Review: branch and proposed lakehouse change review.

## UI Rules

- Use Primer components for menus, labels, buttons, dialogs, forms, tabs, tooltips, and layout primitives where they fit.
- Keep custom Observatory components for dense tables, lineage graphs, logs, and operational matrices.
- Use one compact UI type scale. Prefer 12px to 15px for rows, labels, metadata, and tables.
- Keep status readable without relying only on color.
- Avoid mixed list styles on the same page.
- Avoid double borders, detached headers, nested cards, oversized empty states, and sparse dashboard filler.
- Prefer row-driven workflows over card grids.
- Light and dark mode must both be checked for menus, popovers, dialogs, tables, and selected rows.

## Acceptance

Before calling a UI change complete, verify the changed route in the in-app browser against live hydrated data from the Docker lakehouse. Fixture-only or shell-only verification is not enough.
