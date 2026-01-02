## 1. Implementation
- [x] 1.1 Add a `cross` constraint_setting/value + config_setting to the platforms template.
- [x] 1.2 Add `*-cross` platform variants for all existing targets, including the `cross` marker.
- [x] 1.3 Update BUCK generation to emit `rust_test` rules with `target_compatible_with` select using `:cross`.
- [x] 1.4 Update docs to explain `*-cross` platforms and cross test gating (if required by existing docs).

## 2. Validation
- [x] 2.1 Regenerate a sample workspace and confirm `*-cross` platforms are emitted.
- [x] 2.2 Verify `rust_test` rules include the `target_compatible_with` select for cross platforms.
