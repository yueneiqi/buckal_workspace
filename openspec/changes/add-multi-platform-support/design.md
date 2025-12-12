## Context
Buckal currently emits BUCK rules tied to the host platform. Platform-conditional Cargo dependencies (e.g., `winapi`, `nix`) are lost, requiring regeneration on each OS. We need a once-generated, multi-platform rule set covering Rust Tier1 hosts (linux-gnu, apple-darwin, pc-windows-msvc).

## Goals / Non-Goals
- Goals: model Tier1 platforms, propagate platform constraints (`compatible_with`), encode platform-guarded deps via `os_deps`, keep CLI zero-config, stay backward-compatible when no platform data exists.
- Non-Goals: cross-arch optimization, fine-grained `target_env`/`target_vendor` matrices, auto-creating Buck platform definitions.

## Decisions
- Platform dictionary: Tier1 triples captured in `SUPPORTED_TARGETS` with OS mapping; package allowlist overrides (`PACKAGE_PLATFORMS`) remain for OS‑only crates (e.g., `hyper-named-pipe`).
- Cfg parsing: `cargo_platform::Platform` is matched against cached `rustc --print=cfg --target <triple>` output for supported triples. If parsing/matching yields no OS, treat dependency as universal.
- Emission: edges carry `os_deps`/`os_named_deps` keyed by OS; unconditional deps stay in `deps`/`named_deps`. Nodes currently set `compatible_with` only from the allowlist; deriving it from cfg is a follow‑up.
- Bundles: rust_* wrapper rules accept `os_deps` and `os_named_deps`, expanding into `select({platform: deps, "DEFAULT": base})`. Empty maps keep today’s deps.
- Caching: cache fingerprints do **not** yet include platform model revision; needs follow‑up (or cache version bump) when platform dictionary changes.

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
