set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

default := "build"
root := justfile_directory()

build:
	cd "{{root}}/cargo-buckal" && cargo build --locked

release:
	cd "{{root}}/cargo-buckal" && cargo build --locked --release

clean:
	cd "{{root}}/cargo-buckal" && cargo clean

test-fd:
	cd "{{root}}" && uv run test/buckal_fd_build.py --test

actions-latest repo="yueneiqi/fd-test" branch="":
	cd "{{root}}" && \
	  if [ -n "{{branch}}" ]; then \
	    uv run test/github_actions_latest.py --repo "{{repo}}" --branch "{{branch}}"; \
	  else \
	    uv run test/github_actions_latest.py --repo "{{repo}}"; \
	  fi

dump-log:
	cd "{{root}}" && uv run test/github_actions_latest.py --dump-log
