set shell := ["bash", "-eu", "-o", "pipefail", "-c"]
set windows-shell := ["powershell", "-NoProfile", "-Command"]

default := "build"
root := justfile_directory()

build:
	cargo build --locked --manifest-path "{{root}}/cargo-buckal/Cargo.toml"

release:
	cargo build --locked --release --manifest-path "{{root}}/cargo-buckal/Cargo.toml"

clean:
	cargo clean --manifest-path "{{root}}/cargo-buckal/Cargo.toml"

check:
	cargo fmt --manifest-path "{{root}}/cargo-buckal/Cargo.toml"
	cargo clippy --locked --manifest-path "{{root}}/cargo-buckal/Cargo.toml"
	cargo check --locked --manifest-path "{{root}}/cargo-buckal/Cargo.toml"
	cargo test --locked --manifest-path "{{root}}/cargo-buckal/Cargo.toml"

test-fd:
	cd "{{root}}"
	uv run test/buckal_fd_build.py --test

test-fd-quick:
	cd "{{root}}"
	uv run test/buckal_fd_build.py

test-fd-release:
	cd "{{root}}"
	uv run test/buckal_fd_build.py --test --inplace

test-full:
	cd "{{root}}"
	uv run test/buckal_fd_build.py --test --multi-platform
	uv run test/buckal_fd_build.py --test --multi-platform --supported-platform-only 

actions-latest repo="yueneiqi/fd-test" branch="":
	uv run "{{root}}/test/github_actions_latest.py" --repo "{{repo}}"{{ if branch != "" { " --branch " + branch } else { "" } }}

dump-log:
	uv run "{{root}}/test/github_actions_latest.py" --dump-log
