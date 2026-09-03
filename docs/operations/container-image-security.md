# Container image security operations

Ordinary pull requests run only cheap checks: waiver/report validation, Hadolint
for affected Dockerfiles, and generated Compose/Dockerfile validation. They do
not build or scan images; documentation-only changes do not trigger container
work. The narrow Renovate upstream-image exception performs paired exact-image
scans before merge, as described below. Build, first-party exact-digest
vulnerability scanning, SBOM/provenance, and publication run only after a merge
to `main`.

Publication runs collect the digests changed by that run as workflow artifacts.
Those artifacts are publication evidence and may intentionally describe only a
subset of the fleet; they are not the nightly rescan inventory.

The nightly container scan derives the complete three-image fleet from the
current service definitions, including the shared image used by `dagster` and
`dagster-daemon`. It resolves every current versioned GHCR tag from the registry
to an immutable digest, rejects an incomplete, duplicate, conflicting, or
unexpected fleet, writes a deterministic `generated-service-images.json`, and
rescans every `image@digest` with current Trivy data. The scan does not rebuild
or republish images. The generated full-fleet manifest and scan reports are
retained together as the nightly workflow artifact.

This repository has no safely configured issue token or issue-routing
convention, so nightly failures are intentionally surfaced through workflow
summaries and retained artifacts rather than creating issues automatically.

Vendor runtime images have a separate, non-blocking visibility lane. The
scheduled **Upstream Image Visibility** workflow derives every unique vendor
image from root `image` fields under `packages/*/src/**/*.yaml`, requires an
immutable tag and digest, and scans the exact references sequentially. HIGH and
CRITICAL findings are reported rather than waived or treated as Phlo build
failures: upstream vendors own those images. Inventory mistakes, registry or
scanner failures, missing reports, and malformed results still fail the run so
a green run means the visibility report is complete.

For Renovate-created vendor-image pull requests, the same workflow adds a
blocking candidate comparison. Its trigger requires a GitHub bot account, the
`renovate/` branch convention, and the `dependencies` label; this avoids
granting secrets or write permissions to pull-request code. It derives exact
base and head references from Git source, downloads one pinned Trivy database
snapshot, and scans both references against that snapshot. The candidate must
not increase raw CRITICAL or HIGH occurrences and must strictly decrease at
least one. The report retains raw occurrence counts, unique vulnerability IDs,
fixable and unfixed counts, and added, removed, and unchanged IDs for each
deduplicated image pair. A passing comparison does not replace the affected
package's runtime acceptance checks or human review. The workflow updates one
sticky pull-request comment with the exact comparison Markdown and an explicit
pass/fail result, including when the comparison gate fails.

The workflow summary shows aggregate and per-image severity and fixability,
along with every package-source location and environment override. Its retained
artifact contains the deterministic inventory, rendered Markdown summary, and
raw Trivy JSON. Maintainers can run it on demand from **Actions > Upstream Image
Visibility > Run workflow**. It scans 24 current images sequentially with a
shared cache, so a complete run is intentionally relatively expensive and may
take close to an hour.

## Base-image refresh

Renovate's Docker regex manager discovers immutable vendor runtime defaults in
package source YAML, including strict `${NAME:-image}` defaults. It updates the
tag and digest together and opens review-required pull requests; automerge is
disabled. Phlo-owned `ghcr.io/phlohouse/phlo-*` images are explicitly disabled
for this manager because the first-party publication pipeline owns them.

Review each update as a normal dependency pull request and check the container
security comparison and the affected package's runtime acceptance checks. For
an upstream that Renovate cannot update, resolve the
new tag and digest in a branch, run `python scripts/container_security.py
upstream-runtime-images`, and open a pull request. Never update image defaults
directly on the default branch.
