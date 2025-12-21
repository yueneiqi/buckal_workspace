## Context
cargo-buckal evaluates Cargo platform predicates (`cfg(...)`) by querying `rustc --print=cfg --target <triple>` for a fixed set of targets and collapsing results to `{linux,macos,windows}`. The current `SUPPORTED_TARGETS` list is hand-maintained and limited to Rust Tier-1 hosts. cross-rs/cross maintains `3rd/cross/targets.toml` with 50+ targets including Android, *BSD, Solaris, Illumos, Emscripten, and embedded platforms, providing a comprehensive upstream data source.

## Goals / Non-Goals
- Goals: expand target coverage for cfg evaluation, reduce manual target list maintenance, preserve existing OS three-way classification, maintain or improve startup performance.
- Non-Goals: adding new OS categories beyond linux/macos/windows, modifying Buck constraint model, implementing container-based builds (deferred to follow-up change), auto-generating Buck platform definitions.

## Decisions
- **Data source**: `3rd/cross/targets.toml` is parsed at build time (or via build script / proc macro if needed, but likely direct runtime parse is simplest). Filter `disabled=true`; decide per-target whether to include `special=true` entries (x86_64-apple-darwin, x86_64-pc-windows-msvc are marked special in cross but must remain; likely keep all non-disabled).
- **Os mapping heuristic**: derive Os from Rust target triple structure (split on `-`, inspect components). Known patterns:
  - `*-linux-*` or `*-unknown-linux-*` → Linux
  - `*-apple-darwin` → Macos
  - `*-pc-windows-*` or `*-windows-*` → Windows
  - `*-android*` → Linux (Android targets are Linux-based for cfg purposes)
  - `*-freebsd`, `*-netbsd`, `*-dragonfly`, `*-illumos`, `*-solaris` → Linux (treat Unix-like OSes as Linux for os_deps bucketing; alternative is to skip them, but treating as Linux improves fallback behavior)
  - Embedded/bare-metal (`thumbv*`, `riscv*-none-*`, `wasm32-unknown-emscripten`) → skip or map to Linux (decide based on whether cfg evaluation makes sense; likely skip `*-none-*` targets as they lack std and won't match typical cfg predicates)
- **Performance**: current implementation spawns one thread per target for cfg snapshot. With 50+ targets, this is acceptable (threads are I/O-bound waiting on rustc). If profiling shows degradation, limit concurrency or cache results to disk.
- **Fallback**: if `3rd/cross/targets.toml` is missing or parse fails, fall back to a hardcoded minimal Tier-1 list to ensure cargo-buckal remains usable.

## Risks / Trade-offs
- **Mapping ambiguity**: some cross targets (e.g., `sparcv9-sun-solaris`, `x86_64-unknown-dragonfly`) don't cleanly fit linux/macos/windows. Treating them as "linux" is pragmatic but may misapply linux-specific deps; skipping them loses coverage. Recommend: map Unix-like to Linux, document the behavior, allow refinement in follow-up.
- **Performance regression**: expanding target count increases rustc invocations. Mitigate with profiling and caching.
- **Cross version coupling**: if cross changes targets.toml schema or removes targets, cargo-buckal behavior changes. Mitigate with schema validation and fallback.
- **Test coverage**: need tests that exercise new targets (Android, FreeBSD, musl variants) to ensure mapping works.

## Migration Plan
- Land parser and Os mapping with feature flag or behind existing multi-platform logic (no user-facing change required).
- Update SUPPORTED_TARGETS to use cross-derived list.
- Validate with existing tests plus new tests for exotic targets.
- Document in multi-platform.md.

## Open Questions
- Should embedded/bare-metal targets (thumbv*, riscv*-none-*) be included in SUPPORTED_TARGETS, or filtered out?
- Should we expose a CLI flag or config to override the cross targets.toml path or disable cross integration?