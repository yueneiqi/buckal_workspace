#!/usr/bin/env python3
"""
Generate Buck2 build files for Rust test projects with cargo-buckal and
build the binaries using Buck2.

Supports three test targets:
1. fd project (original functionality) - use --target=fd
2. rust_test_workspace (comprehensive test) - use --target=rust_test_workspace
3. first_party_demo (first-party demo project) - use --target=first_party_demo

By default the script copies the sample project to a temporary directory to avoid
dirtying the repo. Use `--inplace` to run directly in the sample directory.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import sysconfig
import tempfile
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FD_SAMPLE_DIR = REPO_ROOT / "test" / "3rd" / "fd"
RUST_TEST_WORKSPACE_DIR = REPO_ROOT / "test" / "rust_test_workspace"
FIRST_PARTY_DEMO_DIR = REPO_ROOT / "test" / "first-party-demo"
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


def ensure_on_base_and_branch(
    args: argparse.Namespace, env: dict[str, str], sample_dir: Path
) -> tuple[str | None, str | None]:
    """Ensure sample repo is on base branch.
    
    For --inplace runs, create and switch to a fresh branch from base.
    Returns (original_branch, inplace_branch).
    """
    # Only perform git operations for fd project (which is a git repo)
    if args.target != "fd":
        print(f"Skipping git operations for {args.target} (not a git repository)")
        return None, None
        
    try:
        git_run(["rev-parse", "--is-inside-work-tree"], cwd=sample_dir, env=env)
    except subprocess.CalledProcessError:
        print(f"Warning: {sample_dir} is not a git repository; skipping base checkout.")
        return None, None

    status = git_run(["status", "--porcelain"], cwd=sample_dir, env=env, capture=True) or ""
    if status.strip():
        sys.exit(
            f"Repo at {sample_dir} has uncommitted changes; please commit/stash before running."
        )

    original_branch = git_run(
        ["rev-parse", "--abbrev-ref", "HEAD"], cwd=sample_dir, env=env, capture=True
    )
    if original_branch != "base":
        git_run(["checkout", "base"], cwd=sample_dir, env=env)

    inplace_branch = None
    if args.inplace:
        if args.inplace_branch:
            inplace_branch = args.inplace_branch
            exists_rc = subprocess.run(
                ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{inplace_branch}"],
                cwd=sample_dir,
                env=env,
            ).returncode
            if exists_rc == 0:
                sys.exit(
                    f"In-place branch '{inplace_branch}' already exists in repo; choose another name."
                )
        else:
            base_name = f"buckal-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            inplace_branch = base_name
            suffix = 1
            while (
                subprocess.run(
                    ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{inplace_branch}"],
                    cwd=sample_dir,
                    env=env,
                ).returncode
                == 0
            ):
                inplace_branch = f"{base_name}-{suffix}"
                suffix += 1

        git_run(["checkout", "-b", inplace_branch], cwd=sample_dir, env=env)
        print(f"Created and switched to branch {inplace_branch}")

    return original_branch, inplace_branch


def detect_host_os_group() -> str:
    system = platform.system().lower()
    if system == "linux":
        return "linux"
    if system == "darwin":
        return "macos"
    if system == "windows":
        return "windows"
    if system.startswith(("cygwin", "msys", "mingw")):
        return "windows"

    sys_platform = sys.platform.lower()
    if sys_platform.startswith("linux"):
        return "linux"
    if sys_platform == "darwin":
        return "macos"
    if sys_platform in {"win32", "cygwin", "msys"}:
        return "windows"

    raise RuntimeError(
        "Unable to detect host OS group. "
        f"platform.system()={platform.system()!r}, sys.platform={sys.platform!r}"
    )


def multi_platform_targets(host: str) -> tuple[str, ...]:
    if host == "linux":
        return (
            "buckal//platforms:x86_64-unknown-linux-gnu",
            "buckal//platforms:i686-unknown-linux-gnu",
            "buckal//platforms:aarch64-unknown-linux-gnu",
        )
    if host == "windows":
        return (
            "buckal//platforms:x86_64-pc-windows-msvc",
            "buckal//platforms:i686-pc-windows-msvc",
            "buckal//platforms:aarch64-pc-windows-msvc",
            "buckal//platforms:x86_64-pc-windows-gnu",
        )
    if host == "macos":
        return ("buckal//platforms:aarch64-apple-darwin",)
    raise ValueError(f"Unexpected host: {host!r}")


def ensure_valid_buck2_daemon(cwd: Path, env: dict[str, str]) -> None:
    result = subprocess.run(
        ["buck2", "status"],
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        return
    try:
        status = json.loads(result.stdout)
    except json.JSONDecodeError:
        return
    if status.get("valid_working_directory") is False or status.get("valid_buck_out_mount") is False:
        print("Buck2 daemon reports stale working directory; restarting buckd.")
        subprocess.run(["buck2", "kill"], cwd=cwd, env=env, check=False)


def commit_and_push_inplace(
    args: argparse.Namespace, env: dict[str, str], sample_dir: Path, inplace_branch: str | None
) -> None:
    # Only perform git operations for fd project
    if args.target != "fd":
        return
        
    if not args.inplace or args.no_push:
        return
    if not inplace_branch:
        print(f"Warning: repo not on a created inplace branch; skipping commit/push.")
        return
    status = git_run(["status", "--porcelain"], cwd=sample_dir, env=env, capture=True) or ""
    if not status.strip():
        print("No changes in repo to commit; skipping push.")
        return
    git_run(["add", "-A"], cwd=sample_dir, env=env)
    msg = f"buckal migrate update {datetime.now().strftime('%Y%m%d-%H%M%S')}"
    git_run(["commit", "-m", msg], cwd=sample_dir, env=env)
    print("Committed changes, pushing to origin/main...")
    git_run(["push", "--force-with-lease", "origin", "HEAD:main"], cwd=sample_dir, env=env)
    print("[ok] Pushed changes to origin/main")


def get_sample_dir(args: argparse.Namespace) -> Path:
    """Get the sample directory based on the target argument."""
    if args.target == "fd":
        return FD_SAMPLE_DIR
    elif args.target == "rust_test_workspace":
        return RUST_TEST_WORKSPACE_DIR
    elif args.target == "first_party_demo":
        return FIRST_PARTY_DEMO_DIR
    else:
        sys.exit(f"Unknown target: {args.target}. Use 'fd', 'rust_test_workspace', or 'first_party_demo'.")


def get_default_buck2_target(args: argparse.Namespace) -> str:
    """Get the default Buck2 target based on the test target."""
    if args.target == "fd":
        return "//:fd"
    elif args.target == "rust_test_workspace":
        return "//apps/demo:demo"
    elif args.target == "first_party_demo":
        return "//:demo-root"
    else:
        return "//..."  # Fallback


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        choices=["fd", "rust_test_workspace", "first_party_demo"],
        default="fd",
        help="Test target to use (default: fd)",
    )
    parser.add_argument(
        "--inplace",
        action="store_true",
        help="run directly in the sample directory instead of copying to a temp dir",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="keep the temporary workspace when not running inplace",
    )
    parser.add_argument(
        "--buck2-target",
        help="Buck2 target to build (default: depends on target)",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="only generate Buck2 files; skip buck2 build/test steps",
    )
    parser.add_argument(
        "--multi-platform",
        action="store_true",
        help="also build for additional target platforms",
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
        "--no-fetch",
        action="store_true",
        help="skip fetching latest buckal bundles (defaults to fetching)",
    )
    parser.add_argument(
        "--supported-platform-only",
        action="store_true",
        help="only generate BUCK files for supported platforms",
    )
    parser.add_argument(
        "--inplace-branch",
        help="branch name to create when running --inplace (defaults to buckal-test-<timestamp>)",
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="when running --inplace, skip committing/pushing changes",
    )
    parser.add_argument(
        "--origin",
        action="store_true",
        help="use installed cargo-buckal instead of local dev version and skip local bundle copy",
    )
    args = parser.parse_args()

    # Set default buck2 target based on test target if not specified
    if args.buck2_target is None:
        args.buck2_target = get_default_buck2_target(args)

    sample_dir = get_sample_dir(args)
    
    if not CARGO_BUCKAL_MANIFEST.exists():
        sys.exit(f"Missing cargo-buckal manifest at {CARGO_BUCKAL_MANIFEST}")
    if not sample_dir.exists():
        sys.exit(f"Missing sample workspace at {sample_dir}")

    if args.skip_build and (args.multi_platform or args.test):
        sys.exit("--skip-build is incompatible with --multi-platform/--test")

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

    original_branch, inplace_branch = ensure_on_base_and_branch(args, env, sample_dir)

    workspace: Path
    temp_dir: Path | None = None
    if args.inplace:
        workspace = sample_dir
        print(f"Running in-place in {workspace}")
    else:
        temp_dir = Path(tempfile.mkdtemp(prefix=f"buckal-{args.target}-"))
        workspace = temp_dir / args.target
        shutil.copytree(sample_dir, workspace)
        print(f"Copied sample workspace to {workspace}")
        if original_branch and original_branch != "base":
            git_run(["checkout", original_branch], cwd=sample_dir, env=env)

    try:
        buckconfig_path = workspace / ".buckconfig"
        if not buckconfig_path.exists():
            run(["buck2", "init"], cwd=workspace, env=env)

        # Step 1: generate Buck2 files via cargo-buckal (initializes Buck2 if needed).
        if args.origin:
            migrate_cmd = ["cargo", "buckal", "migrate", "--buck2"]
        else:
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
        if args.supported_platform_only:
            migrate_cmd.append("--supported-platform-only")
        run(migrate_cmd, cwd=workspace, env=env)

        if not args.no_fetch:
            if args.origin:
                fetch_cmd = ["cargo", "buckal", "migrate", "--fetch"]
            else:
                fetch_cmd = [
                    "cargo",
                    "run",
                    "--quiet",
                    "--manifest-path",
                    str(CARGO_BUCKAL_MANIFEST),
                    "--",
                    "buckal",
                    "migrate",
                    "--fetch",
                ]
            run(fetch_cmd, cwd=workspace, env=env)

        # # Point the buckal cell to local bundled rules (vendored into the workspace)
        # # to ensure os_deps/rust_test support.
        # # Skip when --origin is set (use fetched bundles instead).
        # if not args.origin:
        #     bundle_src = (REPO_ROOT / "buckal-bundles").resolve()
        #     bundle_dst = workspace / "buckal"
        #     if bundle_dst.exists():
        #         shutil.rmtree(bundle_dst)
        #     shutil.copytree(bundle_src, bundle_dst)
        # bundle_cell_path = "buckal"
        # if buckconfig_path.exists():
        #     sections: dict[str, list[str]] = {}
        #     current = None
        #     for line in buckconfig_path.read_text().splitlines():
        #         if line.strip().startswith("[") and line.strip().endswith("]"):
        #             current = line.strip()[1:-1]
        #             sections.setdefault(current, [])
        #         elif current:
        #             sections[current].append(line)

        #     out_lines: list[str] = []
        #     out_lines += [
        #         "[cells]",
        #         "  root = .",
        #         "  prelude = prelude",
        #         f"  toolchains = {bundle_cell_path}/config/toolchains",
        #         "  none = none",
        #         f"  buckal = {bundle_cell_path}",
        #         "",
        #     ]

        #     if "cell_aliases" in sections:
        #         out_lines.append("[cell_aliases]")
        #         out_lines += sections["cell_aliases"]
        #         out_lines.append("")

        #     out_lines += [
        #         "[external_cells]",
        #         "  prelude = bundled",
        #         "",
        #     ]

        #     for key in ("parser", "build", "project", "buckal"):
        #         if key in sections:
        #             out_lines.append(f"[{key}]")
        #             out_lines += sections[key]
        #             out_lines.append("")

        #     buckconfig_path.write_text("\n".join(out_lines).rstrip() + "\n")

        # # We use the bundled toolchains/platforms under `buckal/config/*`, so
        # # remove any `buck2 init` scaffolding to avoid confusion.
        # for dirname in ("toolchains", "platforms"):
        #     path = workspace / dirname
        #     if path.exists():
        #         shutil.rmtree(path, ignore_errors=True)

        if not args.skip_build:
            # Step 2: build with Buck2.
            ensure_valid_buck2_daemon(workspace, env)
            run(["buck2", "build", args.buck2_target], cwd=workspace, env=env)
            print("[ok] Buck2 build finished")

            # Step 2b: optionally build for additional target platforms.
            if args.multi_platform:
                host = detect_host_os_group()
                print(f"[info] Detected host OS group: {host}")
                ensure_valid_buck2_daemon(workspace, env)
                for platform in multi_platform_targets(host):
                    run(
                        ["buck2", "build", args.buck2_target, "--target-platforms", platform],
                        cwd=workspace,
                        env=env,
                    )
                print("[ok] Buck2 multi-platform builds finished")

            # Optional: run the test suite.
            if args.test:
                ensure_valid_buck2_daemon(workspace, env)
                run(["buck2", "test", args.buck2_test_target], cwd=workspace, env=env)
                print("[ok] Buck2 tests finished")

        commit_and_push_inplace(args, env, sample_dir, inplace_branch)
    finally:
        if temp_dir and not args.keep_temp:
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"Removed temporary workspace {temp_dir}")


if __name__ == "__main__":
    main()
