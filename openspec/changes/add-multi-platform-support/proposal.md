# Change: Add multi-platform Buckal support

## Why
Generated BUCK rules today are tied to the host platform that ran `cargo buckal migrate`, forcing macOS/Windows users to regenerate on their own machines and breaking cross-platform builds. Workspaces need once-generated BUCK files that honor Cargo's platform-conditional dependencies across Tier1 targets.

## What Changes
- Introduce a Tier1 platform model mapping Rust targets to Buck prelude OS constraints and apply it to rule compatibility.
- Parse Cargo cfg/target-specific dependencies and emit `os_deps` plus `compatible_with` on generated `rust_*` rules.
- Extend `buckal-bundles` rust rules to consume `os_deps` and translate them into Buck `select`/platform filters with safe fallbacks.
- Provide sample workspace and docs to validate cross-platform builds without regeneration.

## Impact
- Affected specs: platform-compatibility
- Affected code: cargo-buckal platform/cfg handling, buckify emit path, buckal-bundles rust rules, docs and sample workspace
- Breaking changes: none (adds optional platform metadata with backward-compatible fallbacks)
