# Change: Migrate test CI to cargo-buckal repository

## Why
The current test CI workflow is split across two repositories and involves a complex multi-stage process:
1. `buckal_c/.github/workflows/fd-gen-push.yml` generates Buck2 files on 3 platforms and pushes to separate branches in the external `fd-test` repo
2. `fd-test` repo's CICD.yml then runs multi-platform Buck2 builds triggered by those branch pushes

This architecture has several drawbacks:
- Requires maintaining CI in two separate repositories
- Needs SSH deploy keys and cross-repo secrets management
- Introduces latency between generation and testing (two separate CI runs)
- Makes debugging harder as logs are split across repos
- The fd-test repo is essentially a mirror that only exists for CI purposes

Consolidating into `cargo-buckal/.github/` simplifies maintenance, reduces CI latency, and keeps all buckal-related CI in one place.

## What Changes
- Create a new unified workflow in `cargo-buckal/.github/workflows/` that:
  - Generates Buck2 files for fd on each platform (linux/macos/windows)
  - Immediately runs Buck2 build and test on the same runner
  - Supports cross-compilation targets from each host platform
- Remove dependency on external fd-test repository for CI
- Consolidate the Buck2 build matrix from CICD.yml into the new workflow
- Retain the existing `check-build-and-test.yml` for cargo-buckal's own Rust checks

## Impact
- Affected specs: ci-testing (new capability)
- Affected code: `cargo-buckal/.github/workflows/`
- External dependencies removed: fd-test repo SSH keys, cross-repo push workflow
- Breaking changes: none (existing workflows in buckal_c remain unchanged; this adds to cargo-buckal)
