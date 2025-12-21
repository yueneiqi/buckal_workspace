## 1. Design
- [ ] 1.1 Define container backend trait (methods: check availability, pull image, create container, exec command, cleanup).
- [ ] 1.2 Research cross container invocation patterns (mount paths, env vars, user mapping, cache handling).
- [ ] 1.3 Determine target triple → image name mapping (use cross conventions or allow user override).
- [ ] 1.4 Plan Buck2 workspace mount strategy (read-only source, read-write buck-out, handling symlinks/permissions).
- [ ] 1.5 Identify limitations and document (Windows/macOS host images, MSVC targets, container-in-container scenarios).

## 2. Implementation
- [ ] 2.1 Add container runtime detection (probe `docker`/`podman` binaries, respect `CROSS_CONTAINER_ENGINE`).
- [ ] 2.2 Implement Docker backend (image pull, container create/run, volume mounts, output streaming).
- [ ] 2.3 Implement Podman backend (similar to Docker but handle podman-specific flags/behavior).
- [ ] 2.4 Add `cross-build` CLI subcommand (parse target, resolve image, invoke container backend, forward buck2 args).
- [ ] 2.5 Support Cross.toml parsing (custom images, pre-build scripts, environment variables, volumes).
- [ ] 2.6 Handle errors gracefully (missing container engine, image pull failures, build failures).
- [ ] 2.7 Add unit tests for container backend abstraction and integration tests for cross-build workflow.

## 3. Documentation
- [ ] 3.1 Write doc/cross-build.md (setup, usage examples, supported targets, troubleshooting).
- [ ] 3.2 Update README with cross-build feature summary.
- [ ] 3.3 Add FAQ entries for common issues (permissions, cache invalidation, image updates).

## 4. Validation
- [ ] 4.1 Test cross-build on Linux host targeting aarch64-unknown-linux-gnu, arm-unknown-linux-gnueabihf.
- [ ] 4.2 Test with custom Cross.toml configuration (custom image, pre-build commands).
- [ ] 4.3 Verify cache directory persistence across container runs.
- [ ] 4.4 Test error handling (missing docker, invalid target, network failures).
- [ ] 4.5 Run `cargo fmt && cargo clippy` and `openspec validate add-container-cross-build --strict`.