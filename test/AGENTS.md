# Test Utilities

- `buckal_fd_build.py`: End-to-end helper that copies `test/3rd/fd` to a temp dir (or `--inplace`), runs `buck2 init`, generates Buck2 files via local `cargo-buckal`, vendors local `buckal-bundles`, patches buildscript NUM_JOBS, then builds (and optionally tests) with Buck2.
  - Default: `uv run test/buckal_fd_build.py`
  - In-place: `uv run test/buckal_fd_build.py --inplace`
  - Skip bundle fetch: `--no-fetch`
  - Run tests: `--test [--buck2-test-target //...]`
  - Keep workspace for inspection: `--keep-temp`
- `github_actions_latest.py`: Fetches the newest GitHub Actions workflow run for a repository (defaults to `yueneiqi/fd-test`). Auth is optional via `GITHUB_TOKEN` or `GITHUB_ACCESS_TOKEN`; log download requires a token. JSON output: `uv run test/github_actions_latest.py --json`. Dump logs for jobs prefixed `b2`: `uv run test/github_actions_latest.py --dump-log` (successful jobs print success; failed jobs write logs under `log/<created_at>`).
