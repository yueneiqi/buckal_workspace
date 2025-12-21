## 1. Implementation
- [ ] 1.1 Add toml parsing dependency if needed (check Cargo.toml for existing toml/serde support).
- [ ] 1.2 Implement cross targets.toml parser in new module `cargo-buckal/src/cross_targets.rs` (deserialize `[[target]]` entries, filter `disabled=true`, handle `special`/`sub` metadata).
- [ ] 1.3 Implement target triple → Os mapping heuristic (pattern match on `target_os` component or triple structure; e.g., `-linux-` → Linux, `-apple-` → Macos, `-windows-` → Windows, `-android` → Linux, `-freebsd`/`-netbsd`/etc. → treat as Linux for OS-level os_deps).
- [ ] 1.4 Replace static SUPPORTED_TARGETS with cross-derived list (maintain backward compat by ensuring Tier-1 targets remain present even if cross omits them).
- [ ] 1.5 Measure and optimize cfg_cache initialization (profile thread count, consider limiting parallel rustc calls or caching to disk if startup time degrades).
- [ ] 1.6 Add unit tests for cross parser, Os mapping, and verify cfg_cache handles expanded target set.
- [ ] 1.7 Update docs (doc/multi-platform.md or new doc/platform-coverage.md) to explain cross integration, target coverage, and OS classification behavior.
- [ ] 1.8 Run `cargo fmt && cargo clippy` and `openspec validate integrate-cross-targets --strict`.

## 2. Validation
- [ ] 2.1 Verify SUPPORTED_TARGETS contains expected cross targets (spot-check Android, FreeBSD, musl variants).
- [ ] 2.2 Build cargo-buckal and run existing multi-platform tests to ensure no regressions.
- [ ] 2.3 Test a workspace with Android-specific or FreeBSD-specific conditional deps and confirm os_deps mapping improves (previously unmapped → now mapped to linux).