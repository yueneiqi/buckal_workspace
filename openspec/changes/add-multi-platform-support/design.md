## Context
Buckal currently emits BUCK rules tied to the host platform. Platform-conditional Cargo dependencies (e.g., `winapi`, `nix`) are lost, requiring regeneration on each OS. We need a once-generated, multi-platform rule set covering Rust Tier1 hosts (linux-gnu, apple-darwin, pc-windows-msvc).

## Goals / Non-Goals
- Goals: model Tier1 platforms, propagate platform constraints (`compatible_with`), encode platform-guarded deps via `os_deps`, keep CLI zero-config, stay backward-compatible when no platform data exists.
- Non-Goals: cross-arch optimization, fine-grained `target_env`/`target_vendor` matrices, auto-creating Buck platform definitions.

## Decisions
- Platform dictionary: table-driven mapping from Rust triple to `prelude//os:{linux,macos,windows}`; retain package-specific overrides (e.g., `hyper-named-pipe`).
- Cfg parsing: use `cargo_platform` to evaluate `target_os`/`target_family` with `any/all/not`; on parse failure, treat dependency as universal and log at debug.
- Emission: nodes set `compatible_with` from platform set; edges carry `os_deps` keyed by OS plus a default branch for unconditional deps.
- Bundles: extend rust_* rules to accept `os_deps`, expand into Buck `select` or platform filtering; when `os_deps` empty, behavior matches current deps to avoid churn.
- Caching: snapshot/signature should include platform model version so stale caches regenerate when model changes.

## Risks / Trade-offs
- Missing Buck platform definitions in host repo could break select resolution; fallback will collapse `os_deps` into normal deps when no platforms are configured.
- Complex cfg expressions may still be under-modeled; fallback-to-universal prioritizes build success over strictness.
- Build script platform vs target differences need validation to ensure `compatible_with` does not block required host execution.

## Migration Plan
- Land platform model + cfg parsing behind default-on logic.
- Regenerate BUCK via `cargo buckal migrate` once; confirm cross-platform builds (or via `buck2 --target-platform`).
- Update docs and sample workspace to guide validation.

## Open Questions
- Do we need host/target differentiation for build scripts, or is target_os sufficient for initial rollout?
- Should we expose a flag to force strict cfg parsing (fail on unknown), or is permissive default sufficient?
