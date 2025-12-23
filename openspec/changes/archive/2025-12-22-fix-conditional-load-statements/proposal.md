# Change: Fix conditional load statements for cross-platform compatibility

## Why
When cross-compiling or using Buck2 files generated on another platform, builds fail with:
```
error: Module has no symbol `rust_test`
 --> BUCK:4:81
  |
4 | load("@buckal//:wrapper.bzl", "buildscript_run", "rust_binary", "rust_library", "rust_test")
  |                                                                                 ^^^^^^^^^^^
```

The root cause is that `cargo-buckal` always includes `rust_test` (and other symbols) in the load statement, regardless of whether any `rust_test` rules are actually generated. This causes failures when:
1. The project has no test targets (common when `ignore_tests = true`)
2. The pinned bundle version doesn't export `rust_test`
3. Cross-platform builds use BUCK files generated on a different platform

Currently, `test/buckal_fd_build.py` has a workaround that strips `rust_test` from load statements, but this should be fixed at the source in `cargo-buckal`.

## What Changes
- Modify `gen_buck_content()` in `cargo-buckal/src/buckify/rules.rs` to dynamically build the load statement based on which rule types are actually present in the generated rules
- Only include `rust_test` in the load when `RustTest` rules are present
- Only include `rust_binary` when `RustBinary` rules are present
- Only include `rust_library` when `RustLibrary` rules are present
- Only include `buildscript_run` when `BuildscriptRun` rules are present
- Remove the workaround in `test/buckal_fd_build.py` (the `--keep-rust-test` flag and associated logic)

## Impact
- Affected specs: buck-generation (new capability)
- Affected code:
  - `cargo-buckal/src/buckify/rules.rs` - `gen_buck_content()` function
  - `test/buckal_fd_build.py` - remove workaround logic
- Breaking changes: none - the generated BUCK files remain valid; they just omit unused load symbols
