#!/usr/bin/env python3
"""
Simple wrapper to run cargo-buckal with correct Python library paths.
Fixes: libpython3.x.so.1.0: cannot open shared object file
"""

import os
import sys
import sysconfig
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CARGO_BUCKAL_MANIFEST = SCRIPT_DIR / ".." / "cargo-buckal" / "Cargo.toml"


def main() -> int:
    env = os.environ.copy()

    # Set PYO3_PYTHON to current interpreter
    env["PYO3_PYTHON"] = sys.executable

    # Use separate target dir to avoid mixing binaries linked against different Python versions
    env.setdefault(
        "CARGO_TARGET_DIR",
        str(SCRIPT_DIR / "target" / "buckal-py"),
    )

    # Collect Python library directories
    lib_dirs: list[str] = []
    for key in ("LIBDIR", "LIBPL"):
        value = sysconfig.get_config_var(key)
        if value:
            lib_dirs.append(value)

    # Add Python's lib directory relative to executable
    exe_dir = Path(sys.executable).parent
    lib_dirs.append(str(exe_dir.parent / "lib"))

    # Set LD_LIBRARY_PATH (or DYLD_LIBRARY_PATH on macOS)
    ld_var = "DYLD_LIBRARY_PATH" if sys.platform == "darwin" else "LD_LIBRARY_PATH"
    existing = env.get(ld_var, "")
    combined = ":".join([d for d in lib_dirs if d] + ([existing] if existing else []))
    if combined:
        env[ld_var] = combined

    # Build the command: cargo run ... -- buckal <user_args>
    cmd = [
        "cargo", "run", "--quiet",
        "--manifest-path", str(CARGO_BUCKAL_MANIFEST),
        "--", "buckal",
    ] + sys.argv[1:]

    print(f"+ {' '.join(cmd)}")
    return subprocess.run(cmd, env=env).returncode


if __name__ == "__main__":
    sys.exit(main())
