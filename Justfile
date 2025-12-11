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
