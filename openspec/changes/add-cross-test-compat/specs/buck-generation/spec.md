## ADDED Requirements
### Requirement: Cross-Compilation Test Compatibility
The system SHALL generate platform definitions and test rules that disable test execution on cross-compilation target platforms.

#### Scenario: Cross platforms are defined
- **WHEN** generating `platforms/BUCK`
- **THEN** the file SHALL define a `cross` constraint marker and `config_setting` usable in `select()`s
- **AND** `*-cross` platform variants SHALL be generated for every existing target, carrying the `cross` marker

#### Scenario: Tests are gated on cross platforms
- **WHEN** generating a BUCK file that contains `rust_test` rules
- **THEN** each `rust_test` rule SHALL include `target_compatible_with = select({":cross": ["config//:none"], "DEFAULT": []})`
