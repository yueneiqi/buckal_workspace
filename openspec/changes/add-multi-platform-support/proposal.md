# Change: Add multi-platform Buckal support

## Why
Generated BUCK rules today are tied to the host platform that ran `cargo buckal migrate`, forcing macOS/Windows users to regenerate on their own machines and breaking cross-platform builds. Workspaces need once-generated BUCK files that honor Cargo's platform-conditional dependencies across Tier1 targets.

## What Changes
- Introduce a Tier1 host OS model mapping Rust triples to Buck prelude OS constraints (explicitly covering `x86_64-apple-darwin`) for cfg evaluation and rule generation.
- Parse Cargo target-specific dependency clauses and emit `os_deps` / `os_named_deps` on generated `rust_*` rules.
- Apply `compatible_with` to OS‑only crates via a package allowlist now, with follow‑up work to derive compatibility directly from cfg expressions.
- Extend `buckal-bundles` rust rules to consume `os_deps` / `os_named_deps` and translate them into Buck `select()` filters, preserving behavior when empty.
- Provide sample workspace and docs to validate cross-platform builds without regeneration.

## Impact
- Affected specs: platform-compatibility
- Affected code: cargo-buckal platform/cfg handling, buckify emit path, buckal-bundles rust rules, docs and sample workspace
- Breaking changes: none (adds optional platform metadata with backward-compatible fallbacks)
