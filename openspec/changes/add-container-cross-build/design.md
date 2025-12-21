## Context
Cross-compilation requires target-specific toolchains (cross-compilers, linkers, sysroots) that are difficult to set up manually. cross-rs/cross provides pre-built Docker images with complete toolchain environments for 50+ targets. Users run `cross build --target <triple>` instead of `cargo build --target <triple>`, and cross transparently executes the build inside a container. cargo-buckal can adopt this pattern to enable zero-setup Buck2 cross-builds.

## Goals / Non-Goals
- Goals: enable container-based Buck2 cross-compilation, support Docker and Podman, align with cross conventions (image naming, Cross.toml configuration), maintain good UX (streaming output, error messages), preserve Buck2 caching across container runs.
- Non-Goals: replacing native Buck2 builds (container execution is opt-in), supporting Windows/macOS container hosts for all targets (limited by cross image availability), implementing custom image building (users can provide pre-built images).

## Decisions
- **Container engine selection**: check `CROSS_CONTAINER_ENGINE` env var; if unset, probe `docker` then `podman` binaries and use first available.
- **Image naming**: follow cross convention `ghcr.io/cross-rs/<target>:main` (or user-specified via Cross.toml `[target.<triple>].image`).
- **Volume mounts**: mount workspace root read-only at `/workspace`, mount `buck-out` read-write at `/workspace/buck-out`, mount Cargo cache/registry at `/cargo` (or cross's default paths), mount Buck2 cache at appropriate location.
- **User mapping**: run container as current user (pass `--user $(id -u):$(id -g)`) to avoid permission issues with generated artifacts; handle rootless podman scenarios.
- **Buck2 invocation**: exec `buck2 build <args>` inside container with `--target-platforms` matching the cross target.
- **Cross.toml support**: parse `Cross.toml` or `[workspace.metadata.cross]` in `Cargo.toml` to allow custom images, pre-build scripts, environment variables, and additional volumes (align with cross's config schema).
- **Error handling**: detect missing container engine at startup, surface image pull progress/errors, propagate Buck2 exit codes, provide actionable error messages.

## Risks / Trade-offs
- **Container availability**: requires Docker/Podman installed; fails gracefully if unavailable but adds installation burden.
- **Image availability**: cross does not provide images for all targets (e.g., Windows/macOS); must document limitations and allow custom images.
- **Performance overhead**: container startup adds latency (mitigated by keeping containers running or using fast startup images); volume mount overhead (mitigated by selective mounts).
- **Cache invalidation**: Buck2 cache keyed by host paths may not work correctly inside containers; may need remapping or cache isolation.
- **Hermiticity**: containers improve reproducibility but introduce new variables (base image, network access during pre-build); document behavior and provide `--offline` or pinned-image options.
- **Windows/macOS host support**: Docker Desktop on Windows/macOS has volume mount performance issues and path translation quirks; may need platform-specific handling.

## Migration Plan
- Land container backend abstraction with feature flag or as opt-in subcommand (`cargo buckal cross-build`).
- Validate on Linux host with common targets (aarch64-unknown-linux-gnu, arm-unknown-linux-gnueabihf).
- Document usage and limitations.
- Gather feedback and iterate on UX, caching, and error handling.

## Open Questions
- Should cross-build be a subcommand (`cargo buckal cross-build`) or a flag (`cargo buckal build --cross`)?
- How to handle Buck2 cache isolation across different target containers (separate cache dirs, shared cache with target prefix)?
- Should we support running Buck2 itself inside the container, or only the compiler/linker invocations (cross runs full cargo inside container; Buck2's execution model is different)?
- Do we need custom cross image variants with Buck2 pre-installed, or can we mount Buck2 binary from host?