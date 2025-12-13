### 为 Buckal 实现多平台支持

#### 背景描述

Rust 依赖图中存在一些平台特定的条件依赖关系，例如指定只有 Windows 平台上才会依赖某个 crate。

目前 Buckal 项目并未针对此实现多平台支持，生成的 BUCK 文件只能在当前平台运行。例如 rk8s 仓库的 BUCK 文件是在 Linux 上生成的，因此 Macos 拉取下来无法直接构建，需要 `cargo buckal migrate --no-cache` 重新生成，然而生成的 BUCK 又只能在 Macos 构建。

#### 目标与范围

- 生成的 BUCK2 规则一次生成、多平台可用，在 Linux 上运行 `cargo buckal migrate` 后产物能在 macOS、Windows 直接构建。
- 覆盖 Tier 1 host 工具链（linux-gnu、apple-darwin、pc-windows-msvc），不要求 Tier 2+ 或交叉编译到非主流架构。
- 支持工作区、三方依赖、proc-macro、build script 相关规则的条件依赖；保持现有 CLI 行为零配置。

#### 非目标

- 不解决跨架构（如 x86_64 ↔ aarch64）优化或二进制重定位问题。
- 不自动生成 Buck platform 配置，本次仅消费已存在的 `prelude//os:*` 平台约束。
- 不处理 `cfg(target_env)`、`cfg(target_vendor)` 的细粒度矩阵，默认按 target_os/target_family 推导。

#### 需求描述

1. **Platform Target 建模**：按照 Tier 1 列表定义 Buckal 内部平台模型（可参考 [buckal-target-example.rs](https://gist.github.com/jjl9807/1ff356e851110a7eace25595eb5b589f)），将 Rust triple 映射到 Buck 的 `prelude//os:{linux,macos,windows}` 约束，可扩展出 CPU 维度但本期只启用 OS。
2. **条件依赖收敛为 os_deps**：解析 Cargo metadata 中的 `target`/`cfg` 条件，将平台特定依赖写入 `os_deps`（形如 `("linux", [":dep_linux"])`）。若条件无法解析，回退为“所有平台”以保证可构建。
3. **规则生成**：
   - 平台受限的 crate 填充 `compatible_with`，阻止在不支持的平台被选中。
   - 平台受限的依赖通过 `os_deps` 传递到 `rust_library`/`rust_binary`/`rust_test`，由 bundles 规则展开为 `select()` 或 platform 约束。
4. **CLI 兼容性**：沿用 `cargo buckal migrate`/`build` 等命令，无需新增旗标；缓存/快照逻辑需包含平台模型变更避免脏缓存。
5. **验证覆盖**：提供含条件依赖的样例 workspace，能在至少一个非生成平台上验证构建（示例：在 Linux 生成后在 macOS/Windows 机器或以 `--target-platform` 运行 Buck2 进行验证）。

#### 方案概述

- **数据流**：`cargo metadata` → 解析 target-specific dependencies → 将 `cfg(target_os/target_family)` 转换为平台集合 → 在 buckify 阶段对节点标记 `compatible_with`、对边标记 `os_deps` → 由 `buckal-bundles` 将 `os_deps` 翻译成 Buck `select`/platform 约束。
- **解析策略**：使用 `cargo_platform` 解析 `cfg` 表达式，最小支持 `any/all/not` + `target_os`/`target_family`；解析失败回退为“全平台”。
- **平台字典**：预置 Tier 1 triple 与 `prelude//os` 名称映射，保留表驱动方式便于未来拓展；兼容现有 `PACKAGE_PLATFORMS` 手写白名单。
- **规则改动**：在 `buckal-bundles` 里新增/扩展 `os_deps` 参数，复用现有 `apply_platform_attrs` 生成 `compatible_with`，对依赖列表生成 `select({platform: deps, ...})`，默认分支指向通用依赖。
- **兼容性**：未带平台条件的依赖仍走现有 `deps`，以保持当前输出稳定；无 Buck 平台配置时，`os_deps` 自动折叠为普通依赖避免构建失败。

#### 验收标准

- 在 Linux 上运行 `cargo buckal migrate` 后，生成的 BUCK 文件可在 macOS、Windows 各执行一次 `buck2 build //...`（或等价 target-platform 构建）成功，无需重新生成。
- 条件依赖示例：`winapi` 仅在 Windows 构建链路出现；`nix/termios` 仅在 Linux/macOS 构建链路出现；默认依赖始终存在。
- 平台受限 crate（如 `hyper-named-pipe`）的规则包含 `compatible_with = ["prelude//os:windows"]`。
- 没有改变现有无条件依赖的输出格式和构建成功率。

#### 任务拆解

- [ ] 1) 梳理当前平台处理：审阅 `cargo-buckal/src/platform.rs`、`buckify.rs` 依赖收集与 `buckal-bundles` 中 `apply_platform_attrs` 的用法，列出差距。
- [ ] 2) 定义平台模型：引入 Tier 1 triple ↔ `prelude//os` 映射表，补齐 `Platform` 结构（OS/arch 字段预留）并单元测试映射结果。
- [ ] 3) `cfg` 解析：利用 `cargo_platform` 将 `target` 字段解析为平台集合，覆盖 `any/all/not/target_os/target_family`，无法解析时记录日志并回退全平台。
- [ ] 4) 依赖建模：在 buckify 阶段为节点设置 `compatible_with`，为边生成 `os_deps`（含默认分支），并将数据传入 emitter。
- [ ] 5) Starlark 支持：扩展 `buckal-bundles` 规则接受 `os_deps`，将其转换为 Buck `select()` 或 platform 过滤，保持无平台场景的向后兼容。
- [ ] 6) 样例与验证：构造包含 `winapi`/`nix` 等条件依赖的 workspace，生成 BUCK 后在不同平台或借助 `buck2 --target-platform` 完成一次构建，记录输出。
- [ ] 7) 文档与交付：更新 `doc/buckal_intro.md`/README 说明平台支持范围与限制，补充迁移指引；如使用 OpenSpec，则以 `add-multi-platform-support` 之类的 change-id 补充 proposal/spec/tasks，并通过 `openspec validate --strict`。

#### 风险与待决问题

- Buck 平台配置依赖宿主仓库，若缺少 `prelude//os:*` 定义，需要文档化默认回退策略。
- 复杂 `cfg`（如 `target_arch`, `target_env`, feature gate 嵌套）可能仍无法完美覆盖；需决定未识别条件的默认行为（当前建议回退为全平台，以避免构建中断）。
- Windows/macOS CI 可用性与 toolchain 路径差异可能导致验证成本上升，需提前确认可用的验证环境。
- build script 执行平台与目标平台差异（host vs target）需验证是否受新 `compatible_with`/`os_deps` 影响。
