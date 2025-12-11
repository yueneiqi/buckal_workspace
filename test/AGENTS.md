# Test Utilities

- `buckal_fd_build.py`: End-to-end helper that copies `test/3rd/fd` to a temp dir (or `--inplace`), runs `buck2 init`, generates Buck2 files via local `cargo-buckal`, vendors local `buckal-bundles`, patches buildscript NUM_JOBS, then builds (and optionally tests) with Buck2.
  - Default: `uv run test/buckal_fd_build.py`
  - In-place: `uv run test/buckal_fd_build.py --inplace`
  - Skip bundle fetch: `--no-fetch`
  - Run tests: `--test [--buck2-test-target //...]`
  - Keep workspace for inspection: `--keep-temp`
