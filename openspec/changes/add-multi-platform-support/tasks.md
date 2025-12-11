## 1. Implementation
- [ ] 1.1 Review current platform handling in cargo-buckal and buckal-bundles; capture gaps versus desired multi-platform behavior.
- [ ] 1.2 Implement Tier1 platform model (including `x86_64-apple-darwin`) and mapping helpers in Rust with unit tests.
- [ ] 1.3 Parse cfg/target-specific dependencies using cargo_platform to derive platform sets; log and fallback to universal when parsing fails; add tests.
- [ ] 1.4 Emit `compatible_with` and `os_deps` in buckify generation and ensure snapshot/cache keys account for platform model inputs.
- [ ] 1.5 Extend buckal-bundles rust_* rules to accept `os_deps` and render select/platform filters with backward-compatible defaults; add rule-level tests if available.
- [ ] 1.6 Add sample workspace covering windows-only and unix-only deps; document build steps for cross-platform/`buck2 --target-platform` validation.
- [ ] 1.7 Update docs (e.g., doc/buckal_intro.md and a platform guide) and run formatting plus `openspec validate add-multi-platform-support --strict`.
