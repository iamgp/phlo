# Container image security operations

Pull requests run Hadolint and build/scan only images affected by changes under
their service package. Documentation-only changes therefore do not trigger
container builds. The CI workflow stores Hadolint and Trivy JSON reports as
artifacts and applies the policy in [the security policy](../../SECURITY.md).

Published image digests are collected as workflow artifacts. The nightly
container scan downloads that manifest from the most recent successful image
publication run and rescans immutable `image@digest` references with current
Trivy data; it does not rebuild images. This repository has no safely
configured issue token or issue-routing convention, so nightly failures are
intentionally surfaced through workflow summaries and retained artifacts rather
than creating issues automatically.

## Base-image refresh

Renovate is configured for dependency updates. Review digest updates as normal
pull requests, including the container security workflow. For an upstream that
Renovate cannot update, a maintainer should resolve the upstream digest, update
the relevant `FROM` line in a branch, run `python scripts/container_security.py
affected-images --base main --head HEAD`, and open a pull request. Do not update
base images directly on the default branch.
