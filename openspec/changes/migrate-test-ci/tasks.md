## 1. Workflow Setup
- [x] 1.1 Create `cargo-buckal/.github/workflows/fd-integration-test.yml` with basic structure
- [x] 1.2 Define trigger conditions (every PR, workflow_dispatch)
- [x] 1.3 Add concurrency group to cancel superseded runs

## 2. Environment Setup Jobs
- [x] 2.1 Add Windows long-path and CRLF handling (from fd-gen-push.yml)
- [x] 2.2 Add Rust toolchain setup with required targets
- [x] 2.3 Add Buck2 installation step (cargo install from source with nightly)
- [x] 2.4 Add Python/uv setup for buckal_fd_build.py
- [x] 2.5 Add cross-compilation prerequisites (gcc-aarch64-linux-gnu, etc.)

## 3. Generation Matrix
- [x] 3.1 Define matrix for generation platforms (ubuntu-24.04, macos-14, windows-2022, windows-11-arm)
- [x] 3.2 Clone fd repository at tag v10.3.0 from upstream (sharkdp/fd)
- [x] 3.3 Build cargo-buckal and run `cargo buckal migrate` for Buck2 file generation
- [x] 3.4 Initialize Buck2 in fd directory

## 4. Build/Test Matrix
- [x] 4.1 Define target matrix per host platform (from CICD.yml buck2 job)
- [x] 4.2 Add Buck2 build step with --target-platforms
- [x] 4.3 Add Buck2 test step with --target-platforms
- [x] 4.4 Handle Windows ARM64 execution platform override

## 5. Platform-Specific Handling
- [x] 5.1 Add MSYS2/MinGW setup for windows-gnu targets
- [x] 5.2 Add Linux cross-compiler package installation
- [x] 5.3 Add macOS universal binary support (if needed) - N/A, not needed

## 6. Caching
- [x] 6.1 Add Swatinem/rust-cache for cargo dependencies
- [x] 6.2 Add uv cache for Python dependencies
- [ ] 6.3 Add Buck2 binary caching (deferred - rust-cache handles cargo install)

## 7. Validation
- [ ] 7.1 Test workflow on feature branch
- [ ] 7.2 Verify all target platforms build successfully
- [ ] 7.3 Verify test execution passes
- [ ] 7.4 Compare CI times with old two-repo workflow

## 8. Documentation
- [x] 8.1 Add workflow documentation comments
- [ ] 8.2 Update test/CLAUDE.md with new workflow information
