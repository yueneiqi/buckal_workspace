## ADDED Requirements

### Requirement: Conditional Load Statement Generation
The system SHALL generate load statements that only include symbols actually used by the Buck rules in the file.

#### Scenario: BUCK file with only library targets
- **WHEN** generating a BUCK file that contains only `rust_library` rules
- **THEN** the load statement from `@buckal//:wrapper.bzl` SHALL include only `rust_library`
- **AND** the load statement SHALL NOT include `rust_test`, `rust_binary`, or `buildscript_run`

#### Scenario: BUCK file with library and binary targets
- **WHEN** generating a BUCK file that contains `rust_library` and `rust_binary` rules
- **THEN** the load statement SHALL include `rust_library` and `rust_binary`
- **AND** the load statement SHALL NOT include `rust_test` or `buildscript_run`

#### Scenario: BUCK file with test targets
- **WHEN** generating a BUCK file that contains `rust_test` rules
- **THEN** the load statement SHALL include `rust_test`

#### Scenario: BUCK file with build script support
- **WHEN** generating a BUCK file that contains `buildscript_run` rules
- **THEN** the load statement SHALL include `buildscript_run`

#### Scenario: Complete BUCK file with all rule types
- **WHEN** generating a BUCK file that contains `rust_library`, `rust_binary`, `rust_test`, and `buildscript_run` rules
- **THEN** the load statement SHALL include all four symbols: `rust_library`, `rust_binary`, `rust_test`, `buildscript_run`

### Requirement: Cross-Platform Load Compatibility
The system SHALL generate BUCK files that are valid across all supported platforms without requiring post-processing.

#### Scenario: BUCK file generated on one platform used on another
- **WHEN** a BUCK file is generated on Linux without test targets
- **AND** the same BUCK file is used on macOS or Windows
- **THEN** Buck2 SHALL successfully parse the file without "Module has no symbol" errors

#### Scenario: Tests disabled via ignore_tests configuration
- **WHEN** `ignore_tests = true` is set in the repository configuration
- **THEN** generated BUCK files SHALL NOT include `rust_test` in load statements
- **AND** generated BUCK files SHALL NOT contain any `rust_test` rules
