# Phlo 0.1.0-alpha.3 Release Plan

## Overview

This document outlines the work required to release version 0.1.0-alpha.3, following the 0.1.0-alpha.2 release on December 26, 2025.

**Target Version:** 0.1.0-alpha.3
**Timeline:** No fixed deadline; quality over speed
**Package Versioning:** Fully independent (each package manages its own version)

---

## 1. Release Infrastructure

### 1.1 Fix release-please Prerelease Versioning

**Priority:** Critical (blocking release)
**Status:** Needs investigation and fix

The release-please workflow is not correctly incrementing alpha versions (e.g., alpha.2 -> alpha.3). The current configuration uses:

```yaml
release-type: python
prerelease: true
prerelease-type: alpha
```

**Tasks:**

- [ ] Investigate release-please v4 prerelease behavior with Python release type
- [ ] Consider switching to manifest-based configuration (`.release-please-manifest.json`) for finer control
- [ ] Test the fix locally before merging
- [ ] Document the working configuration

**Files:**

- `.github/workflows/release-please.yml`
- Potentially add: `.release-please-manifest.json`, `release-please-config.json`

### 1.2 Selective Package Publishing

**Priority:** High
**Status:** Needs implementation

The current `publish.yml` only builds the main `phlo` package. With 23+ workspace packages that version independently, we need selective publishing.

**Tasks:**

- [ ] Modify publish workflow to detect which packages have changes
- [ ] Build and publish only changed packages
- [ ] Handle package dependency ordering (if phlo-core changes, dependents may need rebuild)
- [ ] Add dry-run mode for testing

**Files:**

- `.github/workflows/publish.yml`

---

## 2. Testing and Quality

### 2.1 Fix Test Warnings

**Priority:** High
**Status:** Ready to implement

**Task A: Remove pytest asyncio config warning**

- [ ] Remove or update `asyncio_default_fixture_loop_scope` in `pyproject.toml`

**Task B: Suppress pyiceberg Pydantic deprecation warnings**

- [ ] Add pytest warning filter for pyiceberg's Pydantic V2.12 deprecations
- [ ] Document that this is an upstream issue to track

**Files:**

- `pyproject.toml` (pytest.ini_options section)

### 2.2 Auto-Configure Testing

**Priority:** High
**Status:** Needs testing

The auto-configure feature (#119) needs validation across all core services.

**Tasks:**

- [ ] Manual smoke test: Fresh install, run through quickstart
- [ ] Add automated integration tests for service configuration
- [ ] Docker Compose full-stack test
- [ ] Document any discovered edge cases

**Services to test:**

- Dagster
- Postgres
- MinIO
- Nessie
- Trino

---

## 3. Observability

### 3.1 Iceberg Table Maintenance Monitoring

**Priority:** Medium
**Status:** Needs implementation

Add comprehensive observability for Iceberg table maintenance operations.

**Tasks:**

- [ ] Add structured logging for maintenance operations (start/end/duration)
- [ ] Export Prometheus metrics for maintenance operations
- [ ] Surface maintenance status in Observatory UI
- [ ] Add error alerting for failed maintenance

**Files:**

- `packages/phlo-iceberg/`
- `packages/phlo-metrics/`
- `packages/phlo-observatory/`

---

## 4. Documentation

### 4.1 Full Documentation Audit

**Priority:** High
**Status:** Needs review

The README and other docs reference outdated patterns (basedpyright instead of ty, removed examples directory, etc.).

**Tasks:**

- [ ] Update README.md: Replace `basedpyright src/` with `ty check src/phlo`
- [ ] Remove references to examples/ directory (moved to separate repo)
- [ ] Verify all doc links are valid
- [ ] Update developer guide with current tooling
- [ ] Review and update CLI reference for any changed commands
- [ ] Update configuration reference for new features (auto-configure, hooks, security)

**Files to audit:**

- `README.md`
- `docs/getting-started/installation.md`
- `docs/getting-started/quickstart.md`
- `docs/guides/developer-guide.md`
- `docs/reference/cli-reference.md`
- `docs/reference/configuration-reference.md`

### 4.2 Blog Series Rewrite

**Priority:** Medium
**Status:** Needs full rewrite

The 13-part blog series references deprecated patterns (DuckLake, old contracts module, etc.).

**Tasks:**

- [ ] Audit all blog posts for outdated content
- [ ] Rewrite posts to match current architecture
- [ ] Update code examples to use current APIs
- [ ] Consider consolidating posts if content overlaps

**Files:**

- `docs/blog/*.md`

### 4.3 Testing Guide Documentation

**Priority:** Medium
**Status:** Needs creation

The phlo-testing package references a `docs/TESTING_GUIDE.md` that needs to be created.

**Tasks:**

- [ ] Create `docs/TESTING_GUIDE.md` with comprehensive testing patterns
- [ ] Reference phlo-testing package in main documentation
- [ ] Add examples for common testing scenarios
- [ ] Document local test mode usage

**Files:**

- Create: `docs/TESTING_GUIDE.md`
- Update: `docs/guides/developer-guide.md` (add testing section)

### 4.4 Security Documentation

**Priority:** Low
**Status:** Needs creation

The enterprise security configuration feature (#117) should be documented as experimental.

**Tasks:**

- [ ] Create security configuration documentation
- [ ] Mark features as experimental with appropriate warnings
- [ ] Document available security options

**Files:**

- Create: `docs/reference/security-configuration.md`

---

## 5. Observatory

### 5.1 Observatory Installation Experience

**Priority:** High
**Status:** Needs verification

Users should be able to start Observatory with:

1. `phlo observatory start` - dedicated command
2. `phlo services start` - included in services stack

**Tasks:**

- [ ] Verify `phlo observatory start` command works
- [ ] Verify Observatory is included in `phlo services start`
- [ ] Document the installation experience
- [ ] Test with fresh install

---

## 6. Quality Checks

### 6.1 Reconciliation Checks Review

**Priority:** Low
**Status:** Needs evaluation

Review the reconciliation checks in phlo-quality for edge cases or missing check types.

**Tasks:**

- [ ] Audit existing check types
- [ ] Identify any missing common use cases
- [ ] Document available check types

---

## Work Item Summary

### Critical (Blocking Release)

1. Fix release-please prerelease versioning

### High Priority

2. Fix pytest warnings (asyncio config, pyiceberg suppression)
3. Test auto-configure across all services
4. Full documentation audit
5. Observatory installation verification
6. Selective package publishing

### Medium Priority

7. Iceberg maintenance monitoring (logging, metrics, UI)
8. Blog series rewrite
9. Testing guide documentation

### Low Priority

10. Security documentation (mark as experimental)
11. Reconciliation checks review

---

## Verification Checklist

Before tagging alpha.3:

- [ ] All unit tests passing (583+ tests)
- [ ] No pytest warnings in output
- [ ] `ty check src/phlo` passes
- [ ] `ruff check src/` passes
- [ ] Fresh install smoke test succeeds
- [ ] `phlo services start` brings up all services
- [ ] `phlo observatory start` opens Observatory UI
- [ ] Documentation links are valid
- [ ] Release-please creates correct version bump
- [ ] PyPI publish workflow succeeds (dry run)

---

## Post-Release

After alpha.3 is released:

1. Monitor PyPI download metrics
2. Track any user-reported issues
3. Begin planning for beta.1 (feature freeze criteria)
