## ADDED Requirements
### Requirement: Tier1 platform model
The system SHALL map Rust Tier1 target triples to Buck platform constraints `prelude//os/constraints:{linux,macos,windows}` and expose the mapping for rule generation.

#### Scenario: Linux triple mapping
- **WHEN** the target triple belongs to the linux-gnu family
- **THEN** the generated platform constraints include `prelude//os/constraints:linux`.

#### Scenario: Apple Silicon macOS triple mapping
- **WHEN** the target triple is `aarch64-apple-darwin`
- **THEN** the generated platform constraints include `prelude//os/constraints:macos`.

#### Scenario: Unknown triple fallback
- **WHEN** a target triple is not recognized in the mapping
- **THEN** generation proceeds without applying any platform constraint.

### Requirement: Platform compatibility on rules
The system SHALL set `compatible_with` on generated Buck rules for crates constrained to specific OS values.

#### Scenario: Windows-only crate
- **WHEN** a crate is known to be Windows‑only (via allowlist)
- **THEN** its Buck rule has `compatible_with = ["prelude//os/constraints:windows"]`.

### Requirement: Conditional dependencies via os_deps
The system SHALL emit `os_deps` entries mapping platform keys to dependency targets when dependencies are guarded by cfg/target clauses, while keeping unconditional dependencies in the default branch.

#### Scenario: Windows-only dependency
- **WHEN** a dependency is guarded by `cfg(target_os = "windows")`
- **THEN** the generated rule lists that dependency under `os_deps = { "windows": [":dep_windows"] }` and it is absent from other platforms.

#### Scenario: Unmapped condition fallback
- **WHEN** a target-specific dependency condition cannot be mapped to `linux`/`macos`/`windows`
- **THEN** the dependency is treated as universal and emitted in the default deps to preserve build success.

#### Scenario: Unsupported platforms omitted in supported-platform-only mode
- **WHEN** `--supported-platform-only` is enabled and a dependency targets only unsupported platforms
- **THEN** that dependency is omitted from the generated rule.

### Requirement: Bundle rules support os_deps
Buckal bundle rust_* rules SHALL accept `os_deps` and translate them into Buck select/platform filtering while remaining behaviorally identical when `os_deps` is empty.

#### Scenario: os_deps select rendered
- **WHEN** `os_deps` contains entries for linux, macos, and windows
- **THEN** the bundle expands them so each platform receives its dependencies and a default branch covers shared deps.

#### Scenario: No os_deps path
- **WHEN** `os_deps` is omitted
- **THEN** the bundle emits dependencies exactly as today with no select inserted.

### Requirement: Cross-platform validation assets
The project SHALL provide a sample workspace or test target containing platform-guarded dependencies with documented steps to build the generated BUCK on at least one non-origin platform or via `buck2 --target-platforms`.

#### Scenario: Sample build succeeds
- **WHEN** BUCK files generated on Linux are built on macOS/Windows (or via `buck2 --target-platforms`)
- **THEN** the sample workspace builds successfully without regenerating BUCK on that platform.
