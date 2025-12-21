# Change: Integrate cross-rs target matrix

## Why
cargo-buckal's `SUPPORTED_TARGETS` currently covers only 13 Tier-1 host targets (x86_64/aarch64/i686 for linux-gnu/linux-musl/windows-msvc/windows-gnu and aarch64-apple-darwin). This limits cfg evaluation and platform mapping for workspaces that depend on crates with more exotic target predicates (e.g., Android, FreeBSD, embedded, or musl variants). The cross-rs/cross project maintains a comprehensive `targets.toml` with 50+ target definitions including metadata for android, freebsd, netbsd, dragonfly, illumos, solaris, emscripten, and embedded (thumbv*/riscv/etc.) targets. Leveraging this existing target matrix as a data source will improve platform-conditional dependency mapping and reduce manual maintenance.

## What Changes
- Parse `3rd/cross/targets.toml` to extract target triples (filtering `disabled=true` entries) and map them to the existing `Os::{Linux,Macos,Windows}` enum based on Rust target naming conventions.
- Expand `SUPPORTED_TARGETS` in `cargo-buckal/src/platform.rs` to include cross targets while preserving the current three-OS classification model.
- Optimize cfg snapshot collection to handle the expanded target set without degrading startup performance (consider caching, parallel execution limits, or lazy evaluation).
- Update documentation to describe the expanded target coverage and relationship to cross.
- No changes to Buck rules, bundles, or os_deps logic (those remain linux/macos/windows-keyed).

## Impact
- Affected specs: platform-compatibility (extends existing requirements for target mapping and cfg evaluation)
- Affected code: `cargo-buckal/src/platform.rs` (SUPPORTED_TARGETS definition, possibly cfg_cache initialization), potentially `cargo-buckal/Cargo.toml` (add toml parsing dep if not present)
- Affected docs: multi-platform.md or a new platform-coverage doc
- Breaking changes: none (additive; existing behavior preserved for current targets)