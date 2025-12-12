# Buck2 arm64 link fix

## Problem

Building `fd` with Buck2 failed during the Rust link step.

Two related failures were observed:

1. **Host builds on Linux** failed because the bundled demo C/C++ toolchain
   wraps the linker with `clang++ -fuse-ld=lld`, but this environment does not
   have `lld` installed (or the shipped clang does not recognize it). The error
   looked like:

   ```
   clang++: error: invalid linker name in argument '-fuse-ld=lld'
   ```

2. **Cross builds for `aarch64-unknown-linux-gnu`** failed even after removing
   the `lld` flag, because Rust produced AArch64 object files (ELF machine id
   `EM: 183`) but the host `ld/g++` was used to link them:

   ```
   Relocations in generic ELF (EM: 183)
   error adding symbols: file in wrong format
   ```

## Root cause

`toolchains/BUCK` originally called `system_demo_toolchains()`. The demo C++
toolchain uses clang on Linux and injects `-fuse-ld=lld` when the linker is
`g++`/`clang++`. This broke host linking.

When an explicit target platform was passed via
`--target-platforms //platforms:aarch64-unknown-linux-gnu`, Buck correctly
compiled Rust for AArch64, but the C/C++ toolchain still pointed at host tools,
so linking used host `ld`.

## Fix

1. **Replace demo toolchains with explicit system toolchains** in
   `toolchains/BUCK`.

   - Use GCC/G++ for normal Linux host builds to avoid the hard‑coded
     `-fuse-ld=lld` behavior from the demo toolchain.
   - Add a CPU‑based `select()` so that when the platform sets
     `prelude//cpu/constraints:arm64`, the toolchain uses the cross compiler and
     linker:

     - `compiler = aarch64-linux-gnu-gcc`
     - `linker   = aarch64-linux-gnu-g++`

   - Keep `cxx_compiler = "g++"` even for arm64 so the prelude does **not**
     re‑introduce the `lld` flag (there is no AArch64 `g++` in this environment).

2. **Commit platform definitions** in `platforms/BUCK` so `--target-platforms`
   can be used consistently:

   - `//platforms:x86_64-unknown-linux-gnu`
   - `//platforms:aarch64-unknown-linux-gnu`

## How to verify

Host build:

```bash
buck2 build //:fd
```

Cross build:

```bash
buck2 build //:fd --target-platforms //platforms:aarch64-unknown-linux-gnu
```

Both should now complete successfully.

## Notes / limitations

- This fix assumes `aarch64-linux-gnu-gcc` and `aarch64-linux-gnu-ld` are
  available on `$PATH`.

