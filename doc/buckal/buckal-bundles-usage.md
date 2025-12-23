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

`cargo buckal migrate --fetch` 用于更新 buckal-bundles 到最新版本，同时重新生成 BUCK 文件。

### 功能说明

该命令执行以下操作：

1. **获取最新 commit hash**：通过 GitHub API 查询 `buck2hub/buckal-bundles` 仓库的最新 commit sha。
2. **更新 `.buckconfig`**：修改 `[external_cell_buckal]` 段，将 `commit_hash` 更新为最新值。
3. **重新生成 BUCK 文件**：基于 Cargo 元数据和缓存差异，更新项目中的 BUCK 文件。

### 使用场景

- 升级 bundles 规则以获取 bug 修复或新功能
- 解决因 bundles 版本不匹配导致的构建错误
- 确保使用最新的 Rust 规则实现

### 注意事项

- `--fetch` 与 `--buck2` 互斥，不能同时使用。`--buck2` 用于初始化 Buck2 工程，而 `--fetch` 假设工程已初始化。
- 如果 GitHub API 请求失败，会退回到 `DEFAULT_BUNDLE_HASH` 固定版本。

### 实现位置

- `cargo-buckal/src/commands/migrate.rs`
- `cargo-buckal/src/bundles.rs:fetch_buckal_cell()`

## migrate 命令对比

`cargo buckal migrate` 有两种主要模式：标准模式和初始化模式（`--buck2`）。

### `cargo buckal migrate`（标准模式）

用于在已有 Buck2 工程中重新生成 BUCK 文件：

1. **检查 Buck2 工程**：验证当前目录是有效的 Buck2 package
2. **读取 Cargo 元数据**：解析 `Cargo.toml` 和依赖关系
3. **差异化生成**：基于缓存只更新变化的 BUCK 文件

适用场景：
- 添加/移除 Cargo 依赖后同步 BUCK 文件
- 修改 crate 配置后重新生成

### `cargo buckal migrate --buck2`（初始化模式）

用于首次设置或重新初始化 Buck2 工程，在标准模式基础上额外执行：

1. **跳过 Buck2 工程检查**：不要求已有 Buck2 配置
2. **初始化 Buck2**：执行 `buck2 init`
3. **创建第三方目录**：创建 `RUST_CRATES_ROOT` 目录
4. **更新 `.gitignore`**：追加 `/buck-out`
5. **配置 buckal cell**：在 `.buckconfig` 中设置 `[external_cell_buckal]`
6. **初始化 cfg modifiers**：设置平台配置

适用场景：
- 将现有 Cargo 项目迁移到 Buck2
- 重新初始化损坏的 Buck2 配置

### 功能对比表

| 功能 | `migrate` | `migrate --buck2` |
|------|-----------|-------------------|
| 要求已有 Buck2 工程 | 是 | 否 |
| 执行 `buck2 init` | 否 | 是 |
| 创建第三方目录 | 否 | 是 |
| 更新 `.gitignore` | 否 | 是 |
| 配置 buckal cell | 否 | 是 |
| 生成 BUCK 文件 | 是 | 是 |

### 实现位置

- `cargo-buckal/src/commands/migrate.rs:execute()`

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

