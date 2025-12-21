## MODIFIED Requirements
### Requirement: Tier1 platform model
The system SHALL map Rust target triples (including Tier-1 hosts and additional targets from cross-rs/cross) to Buck platform constraints `prelude//os/constraints:{linux,macos,windows}` and expose the mapping for rule generation.

#### Scenario: Linux triple mapping
- **WHEN** the target triple belongs to the linux-gnu family or other Linux-based targets (including Android, musl variants)
- **THEN** the generated platform constraints include `prelude//os/constraints:linux`.

#### Scenario: Apple Silicon macOS triple mapping
- **WHEN** the target triple is `aarch64-apple-darwin`
- **THEN** the generated platform constraints include `prelude//os/constraints:macos`.

#### Scenario: Unix-like OS mapping
- **WHEN** the target triple is FreeBSD, NetBSD, DragonFly, Illumos, or Solaris
- **THEN** the system maps it to `prelude//os/constraints:linux` for os_deps bucketing.

#### Scenario: Android target mapping
- **WHEN** the target triple contains `android` (e.g., `aarch64-linux-android`)
- **THEN** the system maps it to `prelude//os/constraints:linux`.

#### Scenario: Embedded/bare-metal target handling
- **WHEN** the target triple is bare-metal (e.g., `thumbv7em-none-eabi`, `riscv64gc-unknown-none-elf`)
- **THEN** the system either skips it or maps it to a default OS based on configuration.

#### Scenario: Unknown triple fallback
- **WHEN** a target triple is not recognized in the mapping
- **THEN** generation proceeds without applying any platform constraint.

## ADDED Requirements
### Requirement: Cross target matrix integration
The system SHALL parse `3rd/cross/targets.toml` to derive the set of supported target triples, filtering disabled entries and applying Os classification heuristics.

#### Scenario: Cross targets.toml parsing
- **WHEN** cargo-buckal initializes the platform model
- **THEN** it reads `3rd/cross/targets.toml`, filters `disabled=true` entries, and extracts target triple strings.

#### Scenario: Fallback when cross unavailable
- **WHEN** `3rd/cross/targets.toml` is missing or parse fails
- **THEN** the system falls back to a minimal hardcoded Tier-1 target list.

#### Scenario: Performance optimization
- **WHEN** cfg snapshots are collected for 50+ targets
- **THEN** the system completes initialization without significant startup delay (target: <5s added overhead).