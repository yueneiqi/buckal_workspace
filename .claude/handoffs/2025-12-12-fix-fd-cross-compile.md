# Fix FD Cross‑Compile / Multi‑Platform Support

<analysis>
Chronological recap:

1. User provided OpenSpec AGENTS rules + environment, then asked to review current implementation and update the OpenSpec change `openspec/changes/add-multi-platform-support`.
2. I opened `openspec/AGENTS.md` (per repo policy), listed changes, and inspected `openspec/changes/add-multi-platform-support/{proposal.md,design.md,tasks.md,specs/platform-compatibility/spec.md}`.
3. Searched codebase for multi‑platform hooks (`os_deps`, `compatible_with`, `prelude//os:*`, cfg parsing). Found that most of the change was already implemented:
   - `buckal-bundles/wrapper.bzl` merges `os_deps`/`os_named_deps` into `select()`.
   - `cargo-buckal/src/buck.rs` rule structs already carry `os_deps` + `compatible_with`.
   - `cargo-buckal/src/buckify.rs` buckets target‑guarded deps into `os_deps`/`os_named_deps` using `oses_from_platform`.
   - `cargo-buckal/src/platform.rs` defines Tier1 triples, caches `rustc --print=cfg`, and evaluates `cargo_platform::Platform` matches.
   - `compatible_with` is still allowlist‑based (`PACKAGE_PLATFORMS`), not cfg‑derived.
   - `cargo-buckal/src/cache.rs` fingerprints don’t include platform‑model version.
   - Sample CI repo lives under `test/3rd/fd` with platforms/toolchains.
4. Updated OpenSpec change docs to reflect reality:
   - Marked implemented tasks completed, added explicit follow‑ups (tests, cache revision, docs).
   - Updated proposal/design/spec wording to include `os_named_deps` and clarify allowlist‑based `compatible_with`.
   - Ran `openspec validate add-multi-platform-support --strict` → valid.
5. User then asked to update proposal based on `doc/buck2/buck2_cross_build.md` and a failing CI log.
6. I read `log/2025-12-12_08-01/b2_aarch64-unknown-linux-gnu_..._57844872940.log`; failure was at link time:
   - `rust-lld: error: symbols.o is incompatible with elf64-x86-64` while building with `--target-platforms //platforms:aarch64-unknown-linux-gnu`.
   - Diagnosis: Buckal emitted OS labels `prelude//os:linux|macos|windows`, but sample repo’s platform constraints are canonical `prelude//os/constraints:*` (see `test/3rd/fd/platforms/BUCK`).
   - Because labels didn’t match, `select()` branches from `os_deps` never activated under cross‑platform builds, leaving some deps/actions built in exec (host) configuration, causing mixed‑arch artifacts.
7. Implemented fix:
   - `cargo-buckal/src/platform.rs` changed `Os::buck_label()` to return `prelude//os/constraints:*`.
   - `buckal-bundles/wrapper.bzl` `_platform_label()` mapping updated to `prelude//os/constraints:*`.
   - `test/3rd/fd/buckal/wrapper.bzl` updated similarly for the sample.
   - Updated OpenSpec proposal “Why/What Changes” to mention CI failure and canonical label emission; added task 1.6b; validate still passes.
8. Couldn’t run Rust tests from repo root (`Cargo.toml` absent at root). No new unit tests added.

Current purpose for next session (user‑stated): the `test/3rd/fd` sample still needs an extra manual step (from commit `4146ca64bf4f17a8676319`) to make BOTH:
- `buck2 build //:fd --target-platforms //platforms:x86_64-unknown-linux-gnu`
- `buck2 build //:fd --target-platforms //platforms:aarch64-unknown-linux-gnu`
work. Remove that extra step by fixing generator/bundles/sample config.
</analysis>

<plan>
# Session Handoff Plan

## 1. Primary Request and Intent
- Align OpenSpec change `add-multi-platform-support` with the actual implemented multi‑platform support.
- Diagnose and fix cross‑compile failure in CI/sample repo, informed by `doc/buck2/buck2_cross_build.md` and CI logs.
- **Next-session explicit purpose**: eliminate any remaining manual “extra step” required in `test/3rd/fd` (commit `4146ca64bf4f17a8676319`) so cross‑builds for x86_64‑linux and aarch64‑linux succeed out of the box.

## 2. Key Technical Concepts
- Buck2 platforms, constraints, and cross‑build selection via `--target-platforms`.
- Rust Tier1 host triples model.
- Cargo cfg/target‑specific dependencies parsed with `cargo_platform::Platform`.
- `os_deps` / `os_named_deps` for per‑OS dependency graphs.
- Buck2 `select()` expansion in Starlark wrappers.
- `compatible_with` filtering (currently allowlist‑based).
- Cache diffing/fingerprinting in Buckal.
- OpenSpec change/proposal/task/delta‑spec workflow.

## 3. Files and Code Sections

### `openspec/changes/add-multi-platform-support/proposal.md`
- **Why important**: Authoritative change proposal; now includes cross‑compile failure context and canonical label requirement.
- **Changes made**: Clarified current state, added CI root‑cause paragraph, added canonical label bullet.

### `openspec/changes/add-multi-platform-support/tasks.md`
- **Why important**: Implementation checklist for the change.
- **Changes made**: Marked completed tasks, added follow‑ups 1.2b/1.3b/1.4b/1.6b.

### `openspec/changes/add-multi-platform-support/design.md`
- **Why important**: Records actual design/decisions.
- **Changes made**: Updated decisions to match implemented cfg matching + os_deps flow; noted cache revision gap.

### `openspec/changes/add-multi-platform-support/specs/platform-compatibility/spec.md`
- **Why important**: Delta requirements.
- **Changes made**: Loosened `compatible_with` requirement to allow allowlist or cfg‑derived sources.

### `cargo-buckal/src/platform.rs`
- **Why important**: Core platform model and label emission.
- **Changes made**: `Os::buck_label()` switched to canonical constraint labels.
- **Snippet**:
```rust
impl Os {
    pub fn buck_label(self) -> &'static str {
        match self {
            Os::Windows => "prelude//os/constraints:windows",
            Os::Macos => "prelude//os/constraints:macos",
            Os::Linux => "prelude//os/constraints:linux",
        }
    }
}
```

### `cargo-buckal/src/buckify.rs`
- **Why important**: Emits `os_deps`/`os_named_deps` based on cfg matching and allowlist `compatible_with`.
- **Notable logic**: `set_deps()` computes `matching_platforms` from `dep.dep_kinds[*].target` and calls `insert_dep()` with optional OS set.

### `buckal-bundles/wrapper.bzl`
- **Why important**: Starlark wrapper expands `os_deps` to `select()`.
- **Changes made**: `_platform_label()` now maps OS keys to `prelude//os/constraints:*`.
- **Snippet**:
```python
def _platform_label(os_key):
    mapping = {
        "linux": "prelude//os/constraints:linux",
        "macos": "prelude//os/constraints:macos",
        "windows": "prelude//os/constraints:windows",
    }
    return mapping.get(os_key, os_key)
```

### `buckal-bundles/cargo_buildscript.bzl`
- **Why important**: Handles host/target buildscript transitions via `buildscript_for_platform=` + `transition_alias` and uses target‑platform rustc_cfg.
- **No changes made**.

### `test/3rd/fd/*`
- **Why important**: Sample/CI workspace to validate cross‑platform/cross‑arch builds.
- **Files touched**: `test/3rd/fd/buckal/wrapper.bzl` mapping update.
- **Key context**: `platforms/BUCK` defines platforms using `prelude//os/constraints:*` and `prelude//cpu/constraints:*`.

### `doc/buck2/buck2_cross_build.md`
- **Why important**: Reference for Buck2 cross‑build semantics; explains compatibility filtering and platform selection order.

### `log/2025-12-12_08-01/b2_aarch64-unknown-linux-gnu_..._57844872940.log`
- **Why important**: Concrete CI evidence of mixed host/target artifacts.
- **Key error**: linker expects x86_64, receives aarch64 objects.

## 4. Problem Solving
- Reconciled OpenSpec change with existing implementation.
- Diagnosed CI cross‑arch build failure as OS label mismatch between Buckal output and Buck prelude constraints.
- Implemented canonical label fix across generator and bundles.

## 5. Pending Tasks
- **User‑explicit for next session**: locate what “extra step” commit `4146ca64bf4f17a8676319` added in `test/3rd/fd`, and remove the need for it by updating Buckal generator/bundles/sample config.
- Add unit tests for Tier1 triple mapping + cfg matching (`tasks.md` 1.2b, 1.3b).
- Include platform model revision in cache fingerprinting or bump `CACHE_VERSION` when platform dictionaries change (1.4b).
- Update docs (buckal intro + platform guide) to mention canonical labels + known limitations (1.7).
- Regenerate sample BUCK/snapshots in `test/3rd/fd` with new generator if required.

## 6. Current Work
- Last code edits were the canonical OS label mapping changes and proposal/task updates.
- No further runtime validation was performed in this repo.

## 7. Optional Next Step
- Regenerate BUCK files in `test/3rd/fd` using current `cargo-buckal` + bundled rules.
- Re‑run:
  - `buck2 build //:fd --target-platforms //platforms:x86_64-unknown-linux-gnu`
  - `buck2 build //:fd --target-platforms //platforms:aarch64-unknown-linux-gnu`
  without any manual edits.
- If still failing, inspect which targets/actions remain in exec config (likely build scripts/proc‑macros) and adjust:
  - emission of `target_compatible_with` vs `compatible_with` where appropriate,
  - cfg→compatibility derivation (reduce allowlist reliance),
  - possibly extend platform model to include CPU/arch constraints for cross‑arch correctness.
</plan>
