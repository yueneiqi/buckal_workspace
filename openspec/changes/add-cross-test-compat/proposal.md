# Change: Add cross-test compatibility gating

## Why
Cross-compiling Buck2 targets produces test binaries for non-host platforms that cannot be executed on the host. This causes CI failures when running `buck2 test` with `--target-platforms` set to cross targets. We need a consistent, platform-driven way to mark tests incompatible for cross targets so cross builds can proceed without attempting to run target binaries.

## What Changes
- Add a `cross` platform marker (constraint setting/value + config_setting) in generated `platforms/BUCK`.
- Add `*-cross` platform variants for all existing targets that include the `cross` marker.
- When migrating Buck2 files, emit `rust_test` rules with `target_compatible_with = select({":cross": ["config//:none"], "DEFAULT": []})` to disable tests on cross platforms.

## Impact
- Affected specs: buck-generation (adds cross-test compatibility requirement)
- Affected code: `cargo-buckal` BUCK generation logic and bundled `platforms/BUCK` template
- Breaking changes: none (host platforms remain unchanged; cross platforms are additive)
