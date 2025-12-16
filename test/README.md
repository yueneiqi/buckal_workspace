# cargo-buckal Test Suite

This directory contains comprehensive test scripts and sample projects for validating cargo-buckal functionality.

## Test Infrastructure

### `buckal_fd_build.py`

The main test script that generates Buck2 build files and validates cargo-buckal functionality.

#### Test Targets

The script supports two test targets:

1. **fd** (default) - Original test using the fd project
   - **Source**: `test/3rd/fd/`
   - **Default Buck2 target**: `//:fd`
   - **Purpose**: Basic cargo-buckal functionality validation

2. **rust_test_workspace** - Comprehensive test workspace
   - **Source**: `test/rust_test_workspace/`
   - **Default Buck2 target**: `//apps/demo:demo`
   - **Purpose**: Advanced cargo-buckal features testing

#### Usage Examples

##### Test fd project (original functionality)
```bash
# Basic test with temp workspace
uv run test/buckal_fd_build.py

# In-place test (modifies fd repo)
uv run test/buckal_fd_build.py --target=fd --inplace

# Multi-platform build test
uv run test/buckal_fd_build.py --target=fd --multi-platform

# Test with build and run
uv run test/buckal_fd_build.py --target=fd --test
```

##### Test rust_test_workspace (comprehensive)
```bash
# Basic test with temp workspace
uv run test/buckal_fd_build.py --target=rust_test_workspace

# In-place test (modifies test workspace)
uv run test/buckal_fd_build.py --target=rust_test_workspace --inplace

# Build server application
uv run test/buckal_fd_build.py --target=rust_test_workspace --buck2-target="//apps/server:server"

# Run all tests
uv run test/buckal_fd_build.py --target=rust_test_workspace --test --buck2-test-target="//..."

# Multi-platform test
uv run test/buckal_fd_build.py --target=rust_test_workspace --multi-platform
```

#### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--target {fd,rust_test_workspace}` | Test target to use | `fd` |
| `--inplace` | Run directly in sample directory | False |
| `--keep-temp` | Keep temporary workspace | False |
| `--buck2-target TARGET` | Buck2 target to build | Depends on `--target` |
| `--skip-build` | Only generate Buck2 files | False |
| `--multi-platform` | Build for additional platforms | False |
| `--test` | Run buck2 test after build | False |
| `--buck2-test-target TARGET` | Test target | `//...` |
| `--no-patch-num-jobs` | Skip NUM_JOBS=1 injection | False |
| `--keep-rust-test` | Keep rust_test in load statements | False |
| `--no-fetch` | Skip fetching buckal bundles | False |
| `--supported-platform-only` | Only generate for supported platforms | False |
| `--inplace-branch NAME` | Custom branch name for inplace mode | Auto-generated |
| `--no-push` | Skip committing/pushing changes | False |

## Test Workspaces

### 1. fd Project (`test/3rd/fd/`)

**Purpose**: Original test case for basic cargo-buckal functionality

**Features**:
- Real-world Rust project (fd file finder)
- Complex dependency graph
- Build scripts
- Platform-specific dependencies

### 2. rust_test_workspace (`test/rust_test_workspace/`)

**Purpose**: Comprehensive test workspace for advanced cargo-buckal features

**Structure**:
```
rust_test_workspace/
├── Cargo.toml                 # Workspace manifest
├── .buckconfig                # Buck2 configuration
├── crates/                    # Library crates
│   ├── core/                 # Core business logic
│   ├── utils/                # Utility functions with build script
│   ├── cli/                  # CLI application
│   ├── api/                  # API library
│   ├── db/                   # Database abstraction
│   └── shared/               # Shared types and utilities
└── apps/                     # Executable applications
    ├── demo/                 # Demo CLI application
    └── server/               # Server application
```

**Test Features**:
- ✅ **First-party dependencies** - Workspace member relationships
- ✅ **Build scripts** - Complex build script with generated code
- ✅ **Platform-specific code** - Conditional compilation
- ✅ **Feature flags** - Optional features and conditional deps
- ✅ **Multiple binaries** - CLI tools, examples, apps
- ✅ **Integration tests** - Full workspace testing
- ✅ **Complex dependency graph** - Async, serialization, HTTP

## Testing cargo-buckal Features

### 1. Basic Functionality (fd)
```bash
# Test basic cargo-buckal workflow
uv run test/buckal_fd_build.py --target=fd

# Expected output:
# 1. Copies fd to temp directory
# 2. Runs cargo-buckal migrate
# 3. Builds fd with Buck2
# 4. Validates successful build
```

### 2. Build Script Handling (rust_test_workspace)
```bash
# Test build script integration
uv run test/buckal_fd_build.py --target=rust_test_workspace --inplace

# Validates:
# - Build scripts are properly configured
# - Generated code is included
# - Environment variables are passed
```

### 3. First-Party Dependencies
```bash
# Test workspace dependency resolution
uv run test/buckal_fd_build.py --target=rust_test_workspace

# Validates:
# - resolve_first_party_label() function
# - Cross-crate dependency resolution
# - Proper Buck2 target generation
```

### 4. Multi-Platform Support
```bash
# Test platform-specific dependency generation
uv run test/buckal_fd_build.py --target=rust_test_workspace --multi-platform

# Validates:
# - os_deps and os_named_deps generation
# - Platform-specific build rules
# - Cross-compilation support
```

### 5. Feature Flags
```bash
# Test feature flag resolution
uv run test/buckal_fd_build.py --target=rust_test_workspace --supported-platform-only

# Validates:
# - Conditional dependency resolution
# - Feature-based compilation
# - Platform filtering
```

## Expected Validation Results

After running the test script, validate:

### 1. Buck2 Files Generated
- BUCK files in each crate directory
- Proper rule generation (rust_library, rust_binary, buildscript_run)
- Correct dependency resolution

### 2. Build Success
- Buck2 can build the project: `buck2 build <target>`
- All dependencies resolved correctly
- Build scripts execute properly

### 3. Test Execution
- Integration tests pass: `buck2 test //...`
- First-party dependency tests work
- Build script generated code is available

### 4. Platform Support
- Multi-platform builds succeed
- Platform-specific dependencies are correct
- os_deps/os_named_deps are properly generated

## Troubleshooting

### Common Issues

1. **Build script failures**
   ```bash
   # Check build script output
   uv run test/buckal_fd_build.py --target=rust_test_workspace --verbose
   ```

2. **Dependency resolution errors**
   ```bash
   # Verify first-party label resolution
   cargo buckal --verbose
   ```

3. **Platform-specific issues**
   ```bash
   # Test on different platforms
   uv run test/buckal_fd_build.py --target=rust_test_workspace --multi-platform
   ```

### Debug Mode

Use `--verbose` flag with cargo-buckal for detailed output:
```bash
cargo buckal --verbose
```

Check generated Buck2 files:
- Verify dependency paths are correct
- Ensure all required rules are present
- Validate feature flag handling

## Continuous Integration

The test script is designed to be used in CI pipelines:

```yaml
# Example GitHub Actions workflow
- name: Test cargo-buckal with rust_test_workspace
  run: |
    uv run test/buckal_fd_build.py --target=rust_test_workspace --test
```

## Maintenance

- **fd project**: Update periodically to test against latest Rust/cargo versions
- **rust_test_workspace**: Add new test cases as cargo-buckal features are developed
- **Test script**: Update as new cargo-buckal functionality is added
