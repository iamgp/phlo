# Container image security operations

Pull requests run only cheap checks: waiver/report validation, Hadolint for
affected Dockerfiles, and generated Compose/Dockerfile validation. They do not
build or scan images; documentation-only changes do not trigger container work.
Build, exact-digest vulnerability scanning, SBOM/provenance, and publication
run only after a merge to `main`.

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

## Base-image refresh

Renovate is configured for dependency updates. Review digest updates as normal
pull requests, including the container security workflow. For an upstream that
Renovate cannot update, a maintainer should resolve the upstream digest, update
the relevant `FROM` line in a branch, run `python scripts/container_security.py
affected-images --base main --head HEAD`, and open a pull request. Do not update
base images directly on the default branch.
