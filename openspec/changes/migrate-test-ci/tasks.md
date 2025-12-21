## 1. Workflow Setup
- [ ] 1.1 Create `cargo-buckal/.github/workflows/fd-integration-test.yml` with basic structure
- [ ] 1.2 Define trigger conditions (push to main, PRs touching cargo-buckal/buckal-bundles)
- [ ] 1.3 Add concurrency group to cancel superseded runs

## 2. Environment Setup Jobs
- [ ] 2.1 Add Windows long-path and CRLF handling (from fd-gen-push.yml)
- [ ] 2.2 Add Rust toolchain setup with required targets
- [ ] 2.3 Add Buck2 installation step (cargo install from source with nightly)
- [ ] 2.4 Add Python/uv setup for buckal_fd_build.py
- [ ] 2.5 Add cross-compilation prerequisites (gcc-aarch64-linux-gnu, etc.)

## 3. Generation Matrix
- [ ] 3.1 Define matrix for generation platforms (ubuntu-latest, macos-14, windows-2022)
- [ ] 3.2 Clone fd repository at tag v10.3.0 from upstream (sharkdp/fd)
- [ ] 3.3 Integrate buckal_fd_build.py invocation for Buck2 file generation
- [ ] 3.4 Checkout fd base branch for generation

## 4. Build/Test Matrix
- [ ] 4.1 Define target matrix per host platform (from CICD.yml buck2 job)
- [ ] 4.2 Add Buck2 build step with --target-platforms
- [ ] 4.3 Add Buck2 test step with --target-platforms
- [ ] 4.4 Handle Windows ARM64 execution platform override

## 5. Platform-Specific Handling
- [ ] 5.1 Add MSYS2/MinGW setup for windows-gnu targets
- [ ] 5.2 Add Linux cross-compiler package installation
- [ ] 5.3 Add macOS universal binary support (if needed)

## 6. Caching
- [ ] 6.1 Add Swatinem/rust-cache for cargo dependencies
- [ ] 6.2 Add Buck2 binary caching
- [ ] 6.3 Add uv cache for Python dependencies

## 7. Validation
- [ ] 7.1 Test workflow on feature branch
- [ ] 7.2 Verify all target platforms build successfully
- [ ] 7.3 Verify test execution passes
- [ ] 7.4 Compare CI times with old two-repo workflow

## 8. Documentation
- [ ] 8.1 Update test/CLAUDE.md with new workflow information
- [ ] 8.2 Add workflow documentation comments
