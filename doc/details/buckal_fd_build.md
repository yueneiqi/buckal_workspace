# test/buckal_fd_build.py 使用说明

一个端到端脚本，用本地 `cargo-buckal` + 本地 `buckal-bundles` 为 sample 工程 `test/3rd/fd` 生成 BUCK2 规则并用 Buck2 编译（可选跑测试）。方便本地验证 Buckal 产物是否可直接构建。

## 工作流程
- 复制 `test/3rd/fd` 到临时目录（默认）或在原目录执行（`--inplace`）。
- `buck2 init`：如果临时目录内没有 `.buckconfig` 则初始化。
- 生成 BUCK：`cargo run --manifest-path cargo-buckal/Cargo.toml -- buckal migrate --buck2`，可选再 `--fetch` 更新 bundle。
- 绑定本地规则：将仓库内的 `buckal-bundles` 拷贝到工作区 `buckal/`，并把 `.buckconfig` 的 buckal cell 指向该本地路径。
- 兼容补丁：在拷贝的 `cargo_buildscript.bzl` 里注入 `NUM_JOBS=1`，避免部分 build.rs 期望 Cargo 环境时 panic。
- 清理加载项：如果生成的 BUCK 中包含 `rust_test` 但当前 bundle 不提供，则移除该 load 以防解析报错。
- 构建：`buck2 build <buck2-target>`（默认 `//:fd`）。
- 可选测试：加 `--test` 时执行 `buck2 test <buck2-test-target>`（默认 `//...`）。

## 主要参数
- `--inplace`：在 `test/3rd/fd` 直接生成 / 构建（会写 BUCK 文件）。
- `--keep-temp`：保留临时工作区，便于调试生成结果。
- `--no-fetch`：跳过 `cargo buckal migrate --fetch`，使用现有 bundle。
- `--buck2-target`：构建目标，默认 `//:fd`。
- `--test`：构建成功后再跑 `buck2 test`。
- `--buck2-test-target`：测试目标，默认 `//...`。

## 环境细节
- 设置 `PYO3_PYTHON` 为当前 `python3`，并补齐 `LD_LIBRARY_PATH`（或 macOS 下 `DYLD_LIBRARY_PATH`）以保证 `cargo-buckal` 动态链接到正确的 libpython。
- 使用独立的 `CARGO_TARGET_DIR=target/buckal-py`，防止重用旧的二进制导致 Python ABI 不匹配。

### Q: 为什么在拷贝的 `cargo_buildscript.bzl` 里注入 `NUM_JOBS=1`？
- Buck2 的 buildscript 运行环境默认没有 Cargo 的变量，而不少 `build.rs`（如 `tikv-jemalloc-sys`）会 `expect_env("NUM_JOBS")`，缺失就 panic。
- 注入 `env["NUM_JOBS"] = "1"` 是最小仿真 Cargo 行为的补丁：有值即可通过检查，且默认 1 避免误导并行度。
- 改动仅作用于工作区里拷贝的 bundle，不影响上游仓库。

## 示例
```bash
# 默认：临时目录构建
uv run test/buckal_fd_build.py

# 在原目录构建并运行测试
uv run test/buckal_fd_build.py --inplace --test

# 指定构建目标，跳过 fetch
uv run test/buckal_fd_build.py --buck2-target //:fd --no-fetch
```
