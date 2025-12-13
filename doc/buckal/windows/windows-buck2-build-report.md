# Buck2 Windows build fix report (`fd`)

## Summary

`buck2 build //:fd --target-platforms //platforms:x86_64-pc-windows-msvc` was failing on Windows during Rust linking.

Two separate Windows/MSVC issues were involved:

1. **MAX_PATH-style path length failures** (with Windows long paths disabled) caused `link.exe` to fail to open Rust object files emitted under long `buck-out` paths.
2. **MSVC `link.exe` does not support nested response files**, and the Buck + `rustc` invocation ended up producing nested `@response` usage (an `@file` that itself contains another `@file`), which `link.exe` treats as a literal input and errors with `LNK1181`.

The build now succeeds by:

- Shortening Buck rule names for Rust build scripts to reduce `buck-out` path lengths.
- Using Rust’s bundled `lld-link` for linking (it supports nested response files).
- Ensuring `lld-link` can find the `windows.0.52.0.lib` import libraries by adding the appropriate `-Lnative` search path via an existing buildscript output.

## Repro command

```powershell
buck2 build //:fd --target-platforms //platforms:x86_64-pc-windows-msvc
```

## Observed failures

### 1) Rust build-script link failures (path length)

Example:

- `proc-macro2-build-script-build (rustc link)`
- `LINK : fatal error LNK1181: cannot open input file '...rcgu.o'`

The failing `*.rcgu.o` paths were longer than ~260 characters.

### 2) Proc-macro link failure (`clap_derive`) due to nested response files

Example:

- `clap_derive (rustc proc-macro)`
- `LINK : fatal error LNK1181: cannot open input file '@...__clap_derive-link_linker_args.txt'`

The `@...__clap_derive-link_linker_args.txt` file existed, but `link.exe` still failed because it was being used as a nested response file.

## Root cause details

### MAX_PATH-style linking failures

When Windows long paths are not enabled, tools like MSVC `link.exe` can fail to open inputs under long paths. Buck places Rust outputs under deep `buck-out/v2/...` directories, and build-script object paths can exceed legacy length limits.

### Nested response files on MSVC

MSVC `link.exe` supports response files (`@args.rsp`), but **does not support a response file that references another response file** (nested `@...`).

In this build, rustc/Buck passed an `@...__*-link_linker_args.txt` argument to the linker, and rustc also uses response files internally when the link command is long. The result is a nested response structure that triggers `LNK1181`.

## Changes applied

### 1) Shorten Rust build-script rule names to reduce path lengths

Updated generated BUCK targets so build-script rules use short names:

- `rust_binary(name = "...-build-script-build")` → `rust_binary(name = "bsb")`
- `buildscript_run(name = "...-build-script-run")` → `buildscript_run(name = "bsr")`

and updated all references accordingly.

This was applied to `BUCK` and to multiple `third-party/rust/crates/**/BUCK` files for crates that have build scripts.

### 2) Use `lld-link` for linking on Windows (nested response file support)

Added a repo-local `link` shim:

- `link.bat`

This script resolves Rust’s sysroot and executes:

- `%SYSROOT%\lib\rustlib\x86_64-pc-windows-msvc\bin\gcc-ld\lld-link.exe`

Because Buck’s Windows toolchain invokes `link` by name, `link.bat` in the repo root shadows MSVC’s `link.exe` and allows linking to proceed when nested response files are present.

### 3) Add the `windows.0.52.0.lib` search path required by `lld-link`

After switching to `lld-link`, the final link step failed with:

- `rust-lld: error: could not open 'windows.0.52.0.lib': no such file or directory`

The import libraries are provided by the `windows_*_msvc` crates. Their build script outputs a `rustc_flags` file containing the required `-Lnative=...` path.

To make that available for the `fd` binary link, `BUCK` was updated to add, on Windows:

- `@$(location //third-party/rust/crates/windows_x86_64_msvc/0.52.6:bsr[rustc_flags])`

## Verification

The following build succeeded after the changes:

```powershell
buck2 build //:fd --target-platforms //platforms:x86_64-pc-windows-msvc
```

(Most recent successful build output showed `BUILD SUCCEEDED`.)

## Notes / follow-ups

- `link.bat` affects any Buck/Rust action that invokes `link` from the repo context. If you need to restore MSVC `link.exe`, rename/remove `link.bat`.
- A longer-term fix would be to:
  - Enable Windows long paths (or place the repo under a shorter base path), and/or
  - Improve propagation of build-script link-search flags so crates like `windows_x86_64_msvc` automatically contribute their required `-Lnative` paths to final link steps without manually editing the top-level `BUCK`.

