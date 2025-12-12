# Cross‑Building (Cross‑Compiling) in Buck2

Buck2 doesn’t have a single “cross build on/off” switch. Cross‑compilation happens by building your targets in a *different configuration*—i.e., selecting a different **target platform** (or adding platform/arch constraints). Buck2 then resolves `select()`s and toolchains for that platform.

## 1. Cross‑build when platforms already exist

### Pick a target platform on the CLI

Use the `--target-platforms` flag to configure top‑level targets (this has the highest priority in platform selection):

```sh
buck2 build //app:bin --target-platforms //platforms:linux-arm64
```

Buck2 chooses the final target platform in this order:

1. `--target-platforms` command‑line flag
2. `default_target_platform` attribute on the target
3. Cell default platform from `.buckconfig`

### Or add configuration modifiers (constraints)

If your repo uses configuration modifiers, you can cross‑build by adding constraint values:

```sh
buck2 build //app:bin -m //constraints:linux -m //constraints:arm64
```

Some commands also support the `?modifier` syntax:

```sh
buck2 build //app:bin?linux+arm64
```

## 2. Setting up cross‑build support in your repo

If you don’t have platforms/toolchains defined yet, you need to add them.

### Step A: Define constraints and platforms

1. Create `constraint_setting` / `constraint_value` targets for things like OS and CPU.
2. Create a `platform()` target that groups those constraints.

Example (names vary by repo):

```python
# platforms/BUCK

constraint_setting(name = "os")
constraint_value(name = "linux", constraint_setting = ":os")
constraint_value(name = "macos", constraint_setting = ":os")

constraint_setting(name = "cpu")
constraint_value(name = "x86_64", constraint_setting = ":cpu")
constraint_value(name = "arm64", constraint_setting = ":cpu")

platform(
    name = "linux-arm64",
    constraint_values = [
        ":linux",
        ":arm64",
    ],
)
```

### Step B: Make toolchains platform‑aware

Your language toolchains (C++, Rust, Go, etc.) must `select()` the right compiler/flags based on constraints/platform.

High‑level pattern:

```python
toolchain(
    name = "cxx",
    compiler = select({
        "//platforms:linux-arm64": "//toolchains:clang-linux-arm64",
        "DEFAULT": "//toolchains:clang-host",
    }),
    # ... other fields with select() as needed
)
```

Rules that depend on toolchains will automatically cross‑compile once the toolchains respond to the chosen target platform.

### Step C (open‑source Buck2 only): Enable modifiers

If you want `-m` / `?modifier` support in an open‑source repo, call `set_cfg_constructor(...)` in your root `PACKAGE` file. Internal Buck2 repos already have this enabled.

### Step D: Optionally set defaults

Per‑target default platform:

```python
cxx_binary(
    name = "bin",
    srcs = ["main.cpp"],
    default_target_platform = "//platforms:linux-arm64",
)
```

Repo‑wide default platform can be set in `.buckconfig` (cell default platform), so you don’t need to pass `--target-platforms` every time.

## 3. Helpful related knobs

### Compatibility filtering

To mark targets as only buildable on certain platforms, use:

- `target_compatible_with = [...]` (ALL semantics)
- `compatible_with = [...]` (ANY semantics)

Buck2 will skip or error on incompatible targets depending on flags like `--skip-incompatible-targets`.

