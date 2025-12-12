#!/usr/bin/env python3
"""
Generate Buck2 build files for the sample fd project with cargo-buckal and
build the fd binary using Buck2.

By default the script copies `test/3rd/fd` to a temporary directory to avoid
dirtying the repo. Use `--inplace` to run directly in the sample directory.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import sysconfig
import tempfile
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = REPO_ROOT / "test" / "3rd" / "fd"
CARGO_BUCKAL_MANIFEST = REPO_ROOT / "cargo-buckal" / "Cargo.toml"


def run(cmd: list[str], cwd: Path, env: dict[str, str]) -> None:
    print(f"+ {' '.join(cmd)} (cwd={cwd})")
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def ensure_tool(tool: str) -> None:
    if shutil.which(tool):
        return
    sys.exit(f"Required tool not found on PATH: {tool}")


def git_run(cmd: list[str], cwd: Path, env: dict[str, str], capture: bool = False) -> str | None:
    full_cmd = ["git", *cmd]
    print(f"+ {' '.join(full_cmd)} (cwd={cwd})")
    if capture:
        result = subprocess.run(
            full_cmd,
            cwd=cwd,
            env=env,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        )
        return result.stdout.strip()
    subprocess.run(full_cmd, cwd=cwd, env=env, check=True)
    return None


def ensure_fd_on_base_and_branch(
    args: argparse.Namespace, env: dict[str, str]
) -> tuple[str | None, str | None]:
    """Ensure fd sample repo is on base branch.

    For --inplace runs, create and switch to a fresh branch from base.
    Returns (original_branch, inplace_branch).
    """
    try:
        git_run(["rev-parse", "--is-inside-work-tree"], cwd=SAMPLE_DIR, env=env)
    except subprocess.CalledProcessError:
        print(f"Warning: {SAMPLE_DIR} is not a git repository; skipping base checkout.")
        return None, None

    status = git_run(["status", "--porcelain"], cwd=SAMPLE_DIR, env=env, capture=True) or ""
    if status.strip():
        sys.exit(
            f"fd repo at {SAMPLE_DIR} has uncommitted changes; please commit/stash before running."
        )

    original_branch = git_run(
        ["rev-parse", "--abbrev-ref", "HEAD"], cwd=SAMPLE_DIR, env=env, capture=True
    )
    if original_branch != "base":
        git_run(["checkout", "base"], cwd=SAMPLE_DIR, env=env)

    inplace_branch = None
    if args.inplace:
        if args.inplace_branch:
            inplace_branch = args.inplace_branch
            exists_rc = subprocess.run(
                ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{inplace_branch}"],
                cwd=SAMPLE_DIR,
                env=env,
            ).returncode
            if exists_rc == 0:
                sys.exit(
                    f"In-place branch '{inplace_branch}' already exists in fd repo; choose another name."
                )
        else:
            base_name = f"buckal-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            inplace_branch = base_name
            suffix = 1
            while (
                subprocess.run(
                    ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{inplace_branch}"],
                    cwd=SAMPLE_DIR,
                    env=env,
                ).returncode
                == 0
            ):
                inplace_branch = f"{base_name}-{suffix}"
                suffix += 1

        git_run(["checkout", "-b", inplace_branch], cwd=SAMPLE_DIR, env=env)
        print(f"Created and switched to fd branch {inplace_branch}")

    return original_branch, inplace_branch


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inplace",
        action="store_true",
        help="run directly in test/3rd/fd instead of copying to a temp dir",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="keep the temporary workspace when not running inplace",
    )
    parser.add_argument(
        "--buck2-target",
        default="//:fd",
        help="Buck2 target to build (default: //:fd)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="after a successful build, run buck2 test",
    )
    parser.add_argument(
        "--buck2-test-target",
        default="//...",
        help="buck2 test target to run when --test is set (default: //...)",
    )
    parser.add_argument(
        "--no-patch-num-jobs",
        action="store_true",
        help="skip injecting NUM_JOBS=1 into the copied cargo_buildscript.bzl",
    )
    parser.add_argument(
        "--keep-rust-test",
        action="store_true",
        help="do not strip rust_test from the generated BUCK load statement",
    )
    parser.add_argument(
        "--no-fetch",
        action="store_true",
        help="skip fetching latest buckal bundles (defaults to fetching)",
    )
    parser.add_argument(
        "--inplace-branch",
        help="branch name to create when running --inplace (defaults to buckal-test-<timestamp>)",
    )
    args = parser.parse_args()

    if not CARGO_BUCKAL_MANIFEST.exists():
        sys.exit(f"Missing cargo-buckal manifest at {CARGO_BUCKAL_MANIFEST}")
    if not SAMPLE_DIR.exists():
        sys.exit(f"Missing sample workspace at {SAMPLE_DIR}")

    ensure_tool("cargo")
    ensure_tool("buck2")
    ensure_tool("python3")
    ensure_tool("git")

    # Propagate Python ABI/library path for pyo3 so cargo-buckal can link & run.
    env = os.environ.copy()
    env["PYO3_PYTHON"] = sys.executable
    # Fresh target dir prevents reusing a binary linked against another Python.
    env.setdefault(
        "CARGO_TARGET_DIR",
        str(REPO_ROOT / "target" / "buckal-py"),
    )

    lib_dirs: list[str] = []
    for key in ("LIBDIR", "LIBPL"):
        value = sysconfig.get_config_var(key)
        if value:
            lib_dirs.append(value)
    exe_dir = Path(sys.executable).parent
    lib_dirs.append(str(exe_dir.parent / "lib"))
    ld_var = "DYLD_LIBRARY_PATH" if sys.platform == "darwin" else "LD_LIBRARY_PATH"
    existing = env.get(ld_var, "")
    combined = ":".join([d for d in lib_dirs if d] + ([existing] if existing else []))
    if combined:
        env[ld_var] = combined

    original_fd_branch, _ = ensure_fd_on_base_and_branch(args, env)

    workspace: Path
    temp_dir: Path | None = None
    if args.inplace:
        workspace = SAMPLE_DIR
        print(f"Running in-place in {workspace}")
    else:
        temp_dir = Path(tempfile.mkdtemp(prefix="buckal-fd-"))
        workspace = temp_dir / "fd"
        shutil.copytree(SAMPLE_DIR, workspace)
        print(f"Copied sample workspace to {workspace}")
        if original_fd_branch and original_fd_branch != "base":
            git_run(["checkout", original_fd_branch], cwd=SAMPLE_DIR, env=env)

    try:
        buckconfig_path = workspace / ".buckconfig"
        if not buckconfig_path.exists():
            run(["buck2", "init"], cwd=workspace, env=env)

        # Step 1: generate Buck2 files via cargo-buckal (initializes Buck2 if needed).
        migrate_cmd = [
            "cargo",
            "run",
            "--quiet",
            "--manifest-path",
            str(CARGO_BUCKAL_MANIFEST),
            "--",
            "buckal",
            "migrate",
            "--buck2",
        ]
        run(migrate_cmd, cwd=workspace, env=env)

        if not args.no_fetch:
            run(
                [
                    "cargo",
                    "run",
                    "--quiet",
                    "--manifest-path",
                    str(CARGO_BUCKAL_MANIFEST),
                    "--",
                    "buckal",
                    "migrate",
                    "--fetch",
                ],
                cwd=workspace,
                env=env,
            )

        # Point the buckal cell to local bundled rules (vendored into the workspace)
        # to ensure os_deps/rust_test support.
        bundle_src = (REPO_ROOT / "buckal-bundles").resolve()
        bundle_dst = workspace / "buckal"
        if bundle_dst.exists():
            shutil.rmtree(bundle_dst)
        shutil.copytree(bundle_src, bundle_dst)
        buildscript_bzl = bundle_dst / "cargo_buildscript.bzl"
        if buildscript_bzl.exists() and not args.no_patch_num_jobs:
            content = buildscript_bzl.read_text()
            marker = 'env["RUST_BACKTRACE"] = "1"\n'
            if marker in content and "NUM_JOBS" not in content:
                content = content.replace(marker, marker + '    env["NUM_JOBS"] = "1"\n')
                buildscript_bzl.write_text(content)
        bundle_cell_path = "buckal"
        if buckconfig_path.exists():
            sections: dict[str, list[str]] = {}
            current = None
            for line in buckconfig_path.read_text().splitlines():
                if line.strip().startswith("[") and line.strip().endswith("]"):
                    current = line.strip()[1:-1]
                    sections.setdefault(current, [])
                elif current:
                    sections[current].append(line)

            out_lines: list[str] = []
            out_lines += [
                "[cells]",
                "  root = .",
                "  prelude = prelude",
                "  toolchains = toolchains",
                "  none = none",
                f"  buckal = {bundle_cell_path}",
                "",
            ]

            if "cell_aliases" in sections:
                out_lines.append("[cell_aliases]")
                out_lines += sections["cell_aliases"]
                out_lines.append("")

            out_lines += [
                "[external_cells]",
                "  prelude = bundled",
                "",
            ]

            for key in ("parser", "build", "project"):
                if key in sections:
                    out_lines.append(f"[{key}]")
                    out_lines += sections[key]
                    out_lines.append("")

            buckconfig_path.write_text("\n".join(out_lines).rstrip() + "\n")

        # The pinned buckal bundle may not export rust_test; drop it from the load
        # statement in the generated BUCK file to avoid parse errors.
        buck_file = workspace / "BUCK"
        if buck_file.exists() and not args.keep_rust_test:
            lines = buck_file.read_text().splitlines()
            new_lines = []
            modified = False
            for line in lines:
                if "wrapper.bzl" in line and "rust_test" in line:
                    new_lines.append(
                        'load("@buckal//:wrapper.bzl", "buildscript_run", "rust_binary", "rust_library")'
                    )
                    modified = True
                else:
                    new_lines.append(line)
            if modified:
                buck_file.write_text("\n".join(new_lines) + "\n")

        # Step 2: build fd with Buck2.
        run(["buck2", "build", args.buck2_target], cwd=workspace, env=env)
        print("✅ Buck2 build finished")

        # Optional: run the test suite.
        if args.test:
            run(["buck2", "test", args.buck2_test_target], cwd=workspace, env=env)
            print("✅ Buck2 tests finished")
    finally:
        if temp_dir and not args.keep_temp:
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"Removed temporary workspace {temp_dir}")


if __name__ == "__main__":
    main()
