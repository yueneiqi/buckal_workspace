## 1. Implementation

- [ ] 1.1 Modify `gen_buck_content()` in `cargo-buckal/src/buckify/rules.rs` to analyze the rules slice and determine which symbols are actually used
- [ ] 1.2 Build the `wrapper.bzl` load statement dynamically based on detected rule types:
  - Include `rust_binary` only when `Rule::RustBinary` is present
  - Include `rust_library` only when `Rule::RustLibrary` is present
  - Include `rust_test` only when `Rule::RustTest` is present
  - Include `buildscript_run` only when `Rule::BuildscriptRun` is present
- [ ] 1.3 Skip generating the `wrapper.bzl` load statement entirely if no matching rules are present

## 2. Cleanup

- [ ] 2.1 Remove the `--keep-rust-test` argument from `test/buckal_fd_build.py`
- [ ] 2.2 Remove the `rust_test` stripping logic (lines 469-485) from `test/buckal_fd_build.py`
- [ ] 2.3 Update `test/README.md` to remove `--keep-rust-test` documentation
- [ ] 2.4 Update CI workflows in `.github/workflows/` to remove `--keep-rust-test` flags
- [ ] 2.5 Update `Justfile` to remove `--keep-rust-test` flags

## 3. Validation

- [ ] 3.1 Run `uv run test/buckal_fd_build.py --target=fd --test` to verify fd project builds
- [ ] 3.2 Run `uv run test/buckal_fd_build.py --target=rust_test_workspace --test` to verify workspace builds
- [ ] 3.3 Verify BUCK files generated without tests only load needed symbols (no `rust_test`)
- [ ] 3.4 Verify BUCK files generated with tests include `rust_test` in load statement
