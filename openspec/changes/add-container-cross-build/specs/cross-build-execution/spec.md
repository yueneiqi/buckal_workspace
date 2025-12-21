## ADDED Requirements
### Requirement: Container backend abstraction
The system SHALL provide a container backend abstraction supporting Docker and Podman, with automatic detection and graceful fallback.

#### Scenario: Docker detection
- **WHEN** Docker is available on the host
- **THEN** the system uses Docker as the container backend.

#### Scenario: Podman fallback
- **WHEN** Docker is unavailable and Podman is available
- **THEN** the system uses Podman as the container backend.

#### Scenario: No container engine
- **WHEN** neither Docker nor Podman is available
- **THEN** the system reports a clear error and suggests installation.

#### Scenario: Explicit engine selection
- **WHEN** `CROSS_CONTAINER_ENGINE` is set to `docker` or `podman`
- **THEN** the system uses the specified engine regardless of auto-detection.

### Requirement: Cross-build command
The system SHALL provide a `cross-build` subcommand (or `build --cross` flag) that executes Buck2 builds inside cross-rs Docker containers.

#### Scenario: Basic cross-build invocation
- **WHEN** user runs `cargo buckal cross-build --target aarch64-unknown-linux-gnu`
- **THEN** the system resolves the cross image, pulls it if missing, mounts the workspace, and executes `buck2 build` inside the container.

#### Scenario: Build arguments forwarding
- **WHEN** user runs `cargo buckal cross-build --target <triple> -- <buck2-args>`
- **THEN** additional Buck2 arguments are forwarded to the containerized build command.

#### Scenario: Output streaming
- **WHEN** a cross-build is running
- **THEN** container output (stdout/stderr) is streamed to the user in real-time.

### Requirement: Target to image mapping
The system SHALL resolve Rust target triples to cross Docker image names following cross-rs conventions, with user overrides.

#### Scenario: Default image naming
- **WHEN** no custom image is specified for a target
- **THEN** the system uses `ghcr.io/cross-rs/<target>:main` as the image name.

#### Scenario: Custom image via Cross.toml
- **WHEN** `Cross.toml` or `Cargo.toml` specifies `[target.<triple>].image = "custom/image:tag"`
- **THEN** the system uses the custom image instead of the default.

### Requirement: Workspace and cache mounting
The system SHALL mount the workspace and Buck2 cache directories into containers with appropriate permissions and path mappings.

#### Scenario: Workspace mount
- **WHEN** a container is created
- **THEN** the workspace root is mounted at `/workspace` with appropriate read/write permissions.

#### Scenario: Buck cache persistence
- **WHEN** multiple cross-builds run for the same target
- **THEN** the Buck2 cache is persisted and reused across container runs.

#### Scenario: User permission mapping
- **WHEN** running on Linux
- **THEN** the container runs as the current user to avoid permission issues with generated artifacts.

### Requirement: Cross.toml configuration support
The system SHALL parse `Cross.toml` or `[workspace.metadata.cross]` in `Cargo.toml` to support custom images, environment variables, and build hooks.

#### Scenario: Pre-build commands
- **WHEN** `Cross.toml` specifies `[target.<triple>].pre-build` commands
- **THEN** those commands are executed inside the container before the Buck2 build.

#### Scenario: Environment variable injection
- **WHEN** `Cross.toml` specifies `[build].env.passthrough` or `[build].env.volumes`
- **THEN** the specified environment variables are set or volumes are mounted in the container.

### Requirement: Error handling and diagnostics
The system SHALL provide clear error messages and diagnostics for common failure modes.

#### Scenario: Missing container engine
- **WHEN** no container engine is detected
- **THEN** the error message includes installation instructions for Docker/Podman.

#### Scenario: Image pull failure
- **WHEN** pulling a cross image fails (network error, image not found)
- **THEN** the error message includes the image name and suggests checking network connectivity or image availability.

#### Scenario: Build failure propagation
- **WHEN** Buck2 build inside the container fails
- **THEN** the exit code is propagated to the user and container logs are preserved for debugging.