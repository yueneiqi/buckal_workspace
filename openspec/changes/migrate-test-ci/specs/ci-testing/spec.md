## ADDED Requirements

### Requirement: fd Integration Test Workflow
The cargo-buckal repository SHALL provide a GitHub Actions workflow that generates Buck2 files from the fd project and validates they build correctly across multiple platforms.

#### Scenario: Workflow triggers on every PR
- **WHEN** a pull request is opened or updated
- **THEN** the fd integration test workflow SHALL be triggered

#### Scenario: Multi-platform generation
- **WHEN** the workflow runs
- **THEN** Buck2 files SHALL be generated on Linux, macOS, and Windows runners
- **AND** each platform SHALL use its native toolchain for generation
- **AND** the workflow SHALL use fd version v10.3.0

#### Scenario: Buck2 build validation
- **WHEN** Buck2 files have been generated on a platform
- **THEN** the workflow SHALL execute `buck2 build` for all supported targets on that platform
- **AND** the build SHALL complete without errors

#### Scenario: Buck2 test validation
- **WHEN** Buck2 build succeeds for a target
- **THEN** the workflow SHALL execute `buck2 test` for that target
- **AND** tests SHALL pass

### Requirement: Cross-Compilation Target Support
The workflow SHALL support building fd for cross-compilation targets appropriate to each host platform.

#### Scenario: Linux cross-compilation targets
- **WHEN** running on Ubuntu
- **THEN** the workflow SHALL support building for:
  - x86_64-unknown-linux-gnu (native)
  - x86_64-unknown-linux-musl
  - aarch64-unknown-linux-gnu
  - aarch64-unknown-linux-musl
  - arm-unknown-linux-gnueabihf
  - arm-unknown-linux-musleabihf
  - i686-unknown-linux-gnu
  - i686-unknown-linux-musl

#### Scenario: macOS targets
- **WHEN** running on macOS (ARM64)
- **THEN** the workflow SHALL support building for:
  - aarch64-apple-darwin (native)

#### Scenario: Windows targets
- **WHEN** running on Windows x64
- **THEN** the workflow SHALL support building for:
  - x86_64-pc-windows-msvc (native)
  - x86_64-pc-windows-gnu
  - i686-pc-windows-msvc

#### Scenario: Windows ARM64 targets
- **WHEN** running on Windows ARM64
- **THEN** the workflow SHALL support building for:
  - aarch64-pc-windows-msvc (native)

### Requirement: Platform-Specific Environment Setup
The workflow SHALL configure platform-specific prerequisites required for cross-compilation.

#### Scenario: Windows long path support
- **WHEN** running on Windows
- **THEN** the workflow SHALL enable long path support via registry
- **AND** configure git for LF line endings

#### Scenario: Linux cross-compiler installation
- **WHEN** building for ARM or i686 targets on Linux
- **THEN** the workflow SHALL install appropriate GCC cross-compilers
- **AND** the compilers SHALL be available in PATH

#### Scenario: Windows GNU toolchain
- **WHEN** building for x86_64-pc-windows-gnu
- **THEN** the workflow SHALL install MSYS2 with MinGW64 toolchain

### Requirement: Buck2 Installation
The workflow SHALL install Buck2 from source using a pinned revision.

#### Scenario: Buck2 installation from source
- **WHEN** the workflow needs Buck2
- **THEN** it SHALL install Buck2 using `cargo +nightly install` from the facebook/buck2 repository
- **AND** the revision SHALL be pinned for reproducibility

#### Scenario: Buck2 caching
- **WHEN** Buck2 has been installed in a previous run
- **THEN** the workflow SHOULD restore Buck2 from cache to reduce CI time

### Requirement: Concurrency Control
The workflow SHALL prevent redundant CI runs.

#### Scenario: Superseded runs cancelled
- **WHEN** a new commit is pushed to a PR that has a running workflow
- **THEN** the previous workflow run SHALL be cancelled
