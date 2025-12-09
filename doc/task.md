### 为 Buckal 实现多平台支持

#### 背景描述

Rust 依赖图中存在一些平台特定的条件依赖关系，例如指定只有 Windows 平台上才会依赖某个 crate。

目前 Buckal 项目并未针对此实现多平台支持，生成的 BUCK 文件只能在当前平台运行。例如 rk8s 仓库的 BUCK 文件是在 Linux 上生成的，因此 Macos 拉取下来无法直接构建，需要 `cargo buckal migrate --no-cache` 重新生成，然而生成的 BUCK 又只能在 Macos 构建。

#### 需求描述

现在需要针对条件依赖为 Buckal 项目提供相对完整的多平台支持，具体如下：

- 为 Buckal 实现完整的 Platform Target 建模（可以参考 [buckal-target-example.rs](https://gist.github.com/jjl9807/1ff356e851110a7eace25595eb5b589f)）
- 以 `os_deps` 参数的形式在 [Tier 1 Targets](https://doc.rust-lang.org/nightly/rustc/platform-support.html#tier-1-with-host-tools) 范围内实现相对完整的多平台条件依赖支持

```python
os_deps = [
    ("linux", ["fbsource//third-party/rust:nix", "fbsource//third-party/rust:termios"]),
    ("macos", ["fbsource//third-party/rust:nix", "fbsource//third-party/rust:termios"]),
    ("windows", ["fbsource//third-party/rust:winapi"]),
]
```

#### 实现效果

Buckal 生成的 BUCK 文件可以在 Win, Mac, Linux 任一平台直接构建成功

