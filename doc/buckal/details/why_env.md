为什么把abi叫成env？

这是一个很细节的问题，涉及到 **Rust target triple 的历史和设计习惯**。  

---

### 🔎 为什么不是直接叫 ABI，而是叫 `env`？
在 LLVM 和 Rust 的 target triple 设计里，最后一部分并不单纯是“ABI”，而是更广义的 **environment (环境)**。原因有几个：

1. **范围比 ABI 更宽**  
   - ABI（Application Binary Interface）通常只描述函数调用约定、二进制接口、库链接方式。  
   - 但在实际平台区分中，最后一段不仅仅是 ABI，还可能包含 **工具链/运行时环境** 的信息。  
   - 例如：
     - `gnu` → 表示使用 glibc 的 GNU 环境  
     - `musl` → 表示使用 musl libc 的环境  
     - `msvc` → 表示使用 MSVC 工具链和运行时的环境  
     - `none` → 表示裸机环境，没有操作系统和标准库  

   所以用 `Env` 更合适，因为它不仅是 ABI，还包括了 **C 库选择、工具链、运行时**。

---

2. **LLVM 的命名传统**  
   Rust 的 target triple 是直接继承自 LLVM 的设计。LLVM 把最后一部分叫做 **environment**，而不是 ABI。Rust 在实现时保持了这个术语一致性。  

---

3. **避免歧义**  
   如果直接叫 ABI，容易让人误解为只涉及调用约定。但实际上，Rust target triple 的最后部分经常决定：
   - 链接器用什么（GNU ld, MSVC link, Clang lld）  
   - C 库用什么（glibc, musl, uclibc）  
   - 是否有操作系统支持（none → 裸机）  

   这些都超出了 ABI 的范畴，因此用 `env` 更准确。

---

### ✅ 总结
- Rust target triple 的最后一部分在代码里叫 `Env`，是因为它继承了 LLVM 的术语。  
- 它的含义比 ABI 更广，既包括 ABI，也包括工具链、运行时环境、C 库选择。  
- 所以 `pub env: Env, // ABI` 的注释里写 ABI，是为了让读者直观理解，但在实现上 Rust 更倾向于用 “环境 (Env)” 来涵盖更宽的范围。  
