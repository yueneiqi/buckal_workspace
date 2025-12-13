# Buckal 项目简介

## 背景

[rk8s](https://github.com/rk8s-dev/rk8s), [libra](https://github.com/web3infra-foundation/libra), [git-internal](https://github.com/web3infra-foundation/git-internal) 等项目采用 [Buck2](https://buck2.build/) 构建，以解决 Cargo 在构建大型 Rust 项目时的局限性。

但是，Buck2 无法取代 Cargo 的包管理功能，需要手动为工作区项目以及所有第三档依赖手动编写 BUCK 文件。Meta 提供的自动化方案（[reindeer](https://github.com/facebookincubator/reindeer)）效果有限，需要大量手动修补，增加开发者心智负担。

[Buckal](https://github.com/buck2hub/cargo-buckal) 作为一款开箱即用的 Cargo 插件，希望在不改变原有工作流的情况下在 Cargo 中无缝集成 Buck2，完全自动接管 Buck2 构建，实现零配置迁移。

| 操作 | Reindeer | Buckal |
| :--- | :--- | :--- |
| **添加依赖** | • 修改 `third-party/Cargo.toml` 文件<br>• 解析新增依赖<br>&nbsp;&nbsp;`reindeer --third-party-dir third-party buckify`<br>• 生成 BUCK 文件<br>&nbsp;&nbsp;`reindeer --third-party-dir third-party vendor`<br>• 如有需要，编写 `fixup.toml` 文件 | `cargo buckal add` |
| **修补配置** | • Extra sources<br>• Environment variables<br>• Build scripts | / |
| **整体构建** | `reindeer --third-party-dir third-party vendor`<br>`reindeer --third-party-dir third-party buckify`<br>`Buck2 build //project/example:example` | `cargo buckal build` |

## 架构

Buckal 项目架构主要分为 CLI, Snapshot, Core, Prelude 四层，其中前三层为 Buckal 本体 ([buck2hub/cargo-buckal](https://github.com/buck2hub/cargo-buckal))，最底层为自定义的 Buck2 规则实现 ([buck2hub/buckal-bundles](https://github.com/buck2hub/buckal-bundles))。

```text
+---------------------------------------------------------------------------------------+
| CLI                                                                                   |
|                                     +--------------+                                  |
|                                     | cargo-buckal |                                  |
|                                     +--------------+                                  |
|                                                                                       |
|   +-------+     +-------+     +-------+     +-----------+     +-------+               |
|   |  add  |     | build |     |  new  |     |  migrate  |     |  ...  |               |
|   +-------+     +-------+     +-------+     +-----------+     +-------+               |
|                                                                                       |
+---------------------------------------------------------------------------------------+

+--------------------------------------------------+    +-------------------------------+
| Snapshot (cache)                                 |    | Utilities                     |
|                                                  |    |                               |
|  +-------------+  +-------------+  +------+      |    |  +-------------------------+  |
|  | Fingerprint |  | BuckalCache |  | Diff |      |    |  |     Cargo Metadata      |  |
|  +-------------+  +-------------+  +------+      |    |  +-------------------------+  |
|                                                  |    |                               |
+--------------------------------------------------+    |  +-------------------------+  |
                                                        |  |      BuckalContext      |  |
+--------------------------------------------------+    |  +-------------------------+  |
| Core (buckify)                                   |    |                               |
|                                                  |    |  +-------------------------+  |
|  +-------------+          +-------------+        |    |  |      BuckalChange       |  |
|  |  Resolver   |          | BuckEmitter |        |    |  +-------------------------+  |
|  +-------------+          +-------------+        |    |                               |
|                                                  |    |  +-------------------------+  |
|  +-------------+          +-------------+        |    |  |    Buck2 cli wrapper    |  |
|  | RulePacther |          |   Buckify   |        |    |  +-------------------------+  |
|  +-------------+          +-------------+        |    |                               |
|                                                  |    +-------------------------------+
+--------------------------------------------------+

+---------------------------------------------------------------------------------------+
| Prelude (bundles)                                                                     |
|                                                                                       |
|  +----------------+  +--------------+  +-------------+  +-----------------+           |
|  | cargo_manifest |  | rust_library |  | rust_binary |  | buildscript_run |           |
|  +----------------+  +--------------+  +-------------+  +-----------------+           |
|                                                                                       |
+---------------------------------------------------------------------------------------+
```

其中，CLI 模块负责提供与 Cargo 一致的命令行接口，解析用户输入并执行相应操作；所有命令行操作最终都将反应为项目依赖图的更改，由 Snapshot 模块进行差异比较后调用 buckify 模块对 BUCK 文件进行增量更新。

### 什么是 “bundle”
在 Buckal 语境下，“bundle” 指配套的 Buck2 规则与工具集（仓库 `buckal-bundles`）。它作为一个 Buck2 cell（名为 `buckal`）被引入，包含：
- Starlark 规则与宏：例如 `wrapper.bzl`、`cargo_buildscript.bzl`，用于把 Cargo 元数据映射到 Buck2 目标（rust_binary、rust_library 等）。
- 辅助脚本与默认配置：工具脚本、默认 `PACKAGE`、模式配置等。
- 生成的 BUCK 文件通过 `load("@buckal//:wrapper.bzl", ...)` 调用这些规则完成编译。

不同版本或精简版的 bundle 可能导出的符号集合不同（比如有的没有 `rust_test`），因此在自动生成 BUCK 时需要与实际 bundle 内容保持一致，避免加载缺失符号导致的解析错误。
