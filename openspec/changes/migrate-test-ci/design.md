## Context
The cargo-buckal project needs end-to-end CI validation that generates Buck2 files from a real Cargo project (fd) and verifies they build correctly across multiple platforms and cross-compilation targets.

Currently this is achieved through a two-repo workflow:
1. **buckal_c repo** (`fd-gen-push.yml`): Generates Buck2 files on linux/macos/windows, uploads artifacts, then pushes to platform-specific branches in fd-test
2. **fd-test repo** (`CICD.yml`): Triggered by branch pushes, runs Buck2 builds across 12+ target platforms

This design was necessary when cargo-buckal didn't have its own CI infrastructure, but now that `cargo-buckal/.github/` exists, consolidation is possible.

## Goals / Non-Goals

### Goals
- Single workflow that generates and tests Buck2 files in one CI run
- Support all current target platforms from CICD.yml's buck2 job matrix
- Maintain platform-specific generation (some Buck2 files may differ per host OS)
- Keep CI times reasonable through parallelization
- Self-contained in cargo-buckal repo (no external repo dependencies)

### Non-Goals
- Replacing the existing `check-build-and-test.yml` (that handles cargo-buckal's own Rust code)
- Supporting release artifact publishing (fd releases are handled upstream)
- Maintaining backward compatibility with fd-test repo workflow (it becomes obsolete)

## Decisions

### Decision 1: Single workflow with matrix strategy
Use a single workflow file with GitHub Actions matrix to parallelize:
- **Generation phase**: Run on linux/macos/windows to generate platform-specific Buck2 files
- **Build/test phase**: Each generator immediately builds and tests on its platform

**Rationale**: Simpler than separate workflows, GitHub Actions handles parallelization natively.

### Decision 2: In-workflow Buck2 testing (no artifact handoff)
Each platform generates Buck2 files and immediately runs Buck2 build/test on the same runner, rather than uploading artifacts for a separate job.

**Rationale**:
- Eliminates artifact upload/download latency
- Simpler workflow structure
- Each platform tests its own generated files (matches real-world usage)

**Trade-off**: Cannot test cross-platform file compatibility (e.g., files generated on macOS tested on Linux). This is acceptable because:
- Platform-specific files are expected to work on their generation platform
- Cross-platform compatibility is a separate concern handled by the multi-platform-support spec

### Decision 3: Subset of cross-compilation targets per host
Not all 12+ targets from CICD.yml can be built on every host. Map targets to appropriate hosts:

| Host | Native Target | Cross Targets |
|------|---------------|---------------|
| ubuntu-24.04 | x86_64-unknown-linux-gnu | aarch64-unknown-linux-gnu, aarch64-unknown-linux-musl, arm-unknown-linux-gnueabihf, arm-unknown-linux-musleabihf, i686-unknown-linux-gnu, i686-unknown-linux-musl, x86_64-unknown-linux-musl |
| macos-14 | aarch64-apple-darwin | (none currently) |
| windows-2022 | x86_64-pc-windows-msvc | i686-pc-windows-msvc, x86_64-pc-windows-gnu |
| windows-11-arm | aarch64-pc-windows-msvc | (none currently) |

**Rationale**: Matches CICD.yml's existing matrix, uses native runners where available.

### Decision 4: Reuse existing tooling
Leverage `test/buckal_fd_build.py` for generation logic rather than duplicating shell scripts in the workflow.

**Rationale**: Single source of truth for generation process, easier to test locally.

## Risks / Trade-offs

### Risk: Longer CI times
**Mitigation**: Matrix parallelization means total wall-clock time is bounded by the slowest platform, not sum of all platforms.

### Risk: Buck2 installation overhead
**Mitigation**: Use Swatinem/rust-cache for cargo install caching; Buck2 binary caching similar to existing workflow.

### Risk: Windows path length issues
**Mitigation**: Carry over the existing Windows-specific setup (LongPathsEnabled, short CARGO_HOME paths) from CICD.yml.

## Migration Plan

1. Create new workflow in `cargo-buckal/.github/workflows/fd-integration-test.yml`
2. Test on a feature branch to validate all platforms pass
3. Once stable, the old `fd-gen-push.yml` in buckal_c can be deprecated
4. fd-test repo becomes archive-only (no active CI)

## Resolved Questions

1. **Trigger conditions**: Run on every PR (no path filtering)
   - Rationale: Ensures all changes are validated against real-world Buck2 generation

2. **fd source**: Clone fd fresh from upstream repository at tag v10.3.0
   - Rationale: Avoids submodule complexity, pinned version ensures reproducible CI
