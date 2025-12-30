# Test Utilities

- `buckal_fd_build.py`: End-to-end helper for testing cargo-buckal with multiple targets. Supports `--target={fd,libra,rust_test_workspace,first_party_demo}`. For git-enabled targets (fd, libra), it checks out the base branch and optionally forks a fresh branch from it. Then copies the project to a temp dir (or `--inplace`), runs `buck2 init`, generates Buck2 files via local `cargo-buckal`, then builds (and optionally tests) with Buck2.
  - Default (fd): `uv run test/buckal_fd_build.py`
  - Libra: `uv run test/buckal_fd_build.py --target=libra`
  - Clean existing Buck2 files (for libra): `--clean-buck2`
  - In-place: `--inplace`
  - Skip bundle fetch: `--no-fetch`
  - Run tests: `--test [--buck2-test-target //...]`
  - Keep workspace for inspection: `--keep-temp`
- `github_actions_latest.py`: Fetches the newest GitHub Actions workflow run for a repository (defaults to `yueneiqi/fd-test`). Auth is optional via `GITHUB_TOKEN` or `GITHUB_ACCESS_TOKEN`; log download requires a token. JSON output: `uv run test/github_actions_latest.py --json`. Dump logs for jobs prefixed `b2`: `uv run test/github_actions_latest.py --dump-log` (successful jobs print success; failed jobs write logs under `log/<created_at>`).

## Test Workflow (CI verification)
- Finish the buckal change and commit code in `buckal-bundles/` and `cargo-buckal/`.
- Build buckal: `just build` (or the equivalent cargo build in `cargo-buckal/`).
- Run buckal in `test/3rd/fd/` to regenerate Buck2 files.
- Commit the generated Buck2 files in `test/3rd/fd/`.
- Push all commits to GitHub; this triggers the multi-platform CI.
- Inspect CI results and failed job logs with `uv run test/github_actions_latest.py --dump-log`.
