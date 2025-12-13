# buckal-bundles 在 cargo-buckal 中的使用方式

本文描述 `buckal-bundles`（Buckal bundles / Prelude）在 `cargo-buckal` 中如何被引入、更新，以及生成的 BUCK 文件如何依赖它。

## 角色定位

Buckal 架构分为 CLI、Snapshot、Core（buckify）和 Prelude（bundles）四层。`cargo-buckal` 负责前三层：读取 Cargo 元数据、生成/合并 BUCK 文件、管理缓存；真正实现 Cargo 语义的 Buck2 Starlark 规则放在 `buckal-bundles` 仓库里。生成的 BUCK 文件通过 `@buckal` cell 来 `load()` 这些规则。参见 `doc/buckal_intro.md`。

## Buck2 cell 引入（buckal cell wiring）

`buckal-bundles` 以一个 Buck2 cell 的形式被接入到用户工程中，cell 名为 `buckal`。

在以下命令中会自动完成接入：

- `cargo buckal init --lite` 或 `cargo buckal init --repo`
- `cargo buckal migrate --buck2`

接入逻辑位于 `cargo-buckal/src/bundles.rs`：

1. 修改 `.buckconfig`：
   - 在 `[cells]` 中加入 `buckal = buckal`
   - 在 `[external_cells]` 中声明 `buckal = git`
   - 创建 `[external_cell_buckal]` 段，配置：
     - `git_origin = https://github.com/buck2hub/buckal-bundles`
     - `commit_hash = <sha>`
2. 创建/更新 Buck2 项目基础文件：
   - `toolchains/BUCK`（Linux 下覆盖 demo toolchain）
   - `platforms/BUCK`（写入常见 Rust triples → prelude constraints）
3. 生成 `buckal/` 目录中的 `PACKAGE`，用于配置 cfg modifiers 和模式别名。

`commit_hash` 的来源：

- 默认会通过 GitHub API 拉取 `buck2hub/buckal-bundles` 的最新 commit（`cargo-buckal/src/bundles.rs:fetch()`）。
- 如果拉取失败，则退回到 `cargo-buckal/src/main.rs` 中的 `DEFAULT_BUNDLE_HASH` 固定版本。

## bundles 更新（fetch）

`cargo buckal migrate --fetch` 仅更新 `.buckconfig` 中的 `[external_cell_buckal]` 段，把 `commit_hash` 改成远端最新 sha，不重新初始化 Buck2 工程。对应实现见：

- `cargo-buckal/src/commands/migrate.rs`
- `cargo-buckal/src/bundles.rs:fetch_buckal_cell()`

## BUCK 生成时的依赖方式

在 buckify 阶段，`cargo-buckal` 会把所有生成的 BUCK 文件前置两个 `load()`：

```python
load("@buckal//:cargo_manifest.bzl", "cargo_manifest")
load("@buckal//:wrapper.bzl", "rust_library", "rust_binary", "rust_test", "buildscript_run")
```

这些符号全部来自 `buckal-bundles`：

- `cargo_manifest`：描述 Cargo package/target 元数据
- `rust_library` / `rust_binary` / `rust_test`：对 Buck2 Rust 规则的 Cargo 语义封装
- `buildscript_run`：build.rs 执行与产物收集

生成逻辑见 `cargo-buckal/src/buckify.rs:gen_buck_content()`。

因此，`cargo-buckal` 本身不携带 Buck2 Rust 规则实现；只负责生成对 bundles 的调用。

## 本地 bundles 覆盖（开发/调试）

如果希望在本地调试 bundles 规则，可以把仓库内的 `buckal-bundles/` 作为本地 cell 引入（而不是 git external cell）。常见做法：

1. 把 `buckal-bundles` 拷贝/软链到工程根目录的 `buckal/`。
2. 在 `.buckconfig` 中将：
   - `[cells] buckal = buckal` 保持不变
   - 移除/注释 `[external_cells] buckal = git` 与 `[external_cell_buckal] ...`

参考端到端脚本 `doc/details/buckal_fd_build.md` 和 `test/buckal_fd_build.py` 的做法。

## 兼容性注意事项

- bundles 的导出符号集合必须与 `cargo-buckal` 生成的 `load()` 保持一致，否则 Buck2 解析会失败（例如缺少 `rust_test`）。
- 平台相关字段（如 `os_deps`、`compatible_with`）的解释由 bundles 规则完成，`cargo-buckal` 只负责把 Cargo 的 cfg/target 信息转换为 bundles 需要的形态。

## 故障排查

- 解析错误提示找不到 `@buckal//...`：通常是 `.buckconfig` 中 buckal cell 未正确写入，或 bundles 版本被手动移除。
- bundles 规则不匹配：尝试 `cargo buckal migrate --fetch` 更新到最新 bundles，或回退到已知可用的 `commit_hash`。
- Linux 链接器/工具链问题：`cargo buckal init`/`migrate --buck2` 会写入 `toolchains/BUCK` 覆盖 demo toolchains，必要时检查该文件是否被修改。

