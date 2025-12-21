# Change: Add container-based cross-compilation execution

## Why
Buck2 cross-platform builds currently assume host-native toolchains are available for the target platform (e.g., cross-compilers, target sysroots, linkers). This works for some targets but breaks down for MSVC (requires Windows), macOS toolchains (requires macOS SDK/Xcode), and many exotic targets. cross-rs/cross solves this by running builds inside pre-configured Docker/Podman images with complete cross-toolchains and target sysroots. Integrating cross-style container execution will enable zero-setup cross-compilation for 50+ targets without requiring users to install complex toolchain dependencies.

## What Changes
- Add a new `cargo buckal cross-build` (or `cargo buckal build --cross`) subcommand that wraps Buck2 execution in a cross container.
- Implement container backend abstraction supporting Docker and Podman (detect via `CROSS_CONTAINER_ENGINE` env var or auto-detect availability).
- Map Buck2 workspace and cache directories into containers with appropriate volume mounts.
- Resolve target triple → cross Docker image name (use cross's image naming conventions; e.g., `ghcr.io/cross-rs/<target>:main`).
- Handle container lifecycle (pull image if missing, create/start/stop container, stream build output).
- Support cross configuration via `Cross.toml` or `[workspace.metadata.cross]` in `Cargo.toml` (for custom images, pre-build scripts, env vars).
- Document setup requirements (Docker/Podman installation), usage, limitations (MSVC/macOS targets still constrained by cross's image availability).

## Impact
- Affected specs: new capability `cross-build-execution` (does not modify existing platform-compatibility spec)
- Affected code: new module `cargo-buckal/src/commands/cross_build.rs`, potentially new `cargo-buckal/src/container.rs` for backend abstraction, CLI definition in main.rs
- Affected docs: new doc/cross-build.md, updates to README and intro docs
- Breaking changes: none (new opt-in feature; existing `cargo buckal build` unaffected)