# OpenSpec Documentation

This directory contains technical design documents for cargo-buckal architecture and features.

## Documents

### [Fine-Grained Platform Support Architecture](./fine-grained-platform-support.md)
**Status**: Design Document
**Audience**: Engineers implementing platform extensions

Comprehensive guide for extending cargo-buckal's platform model from 3-OS classification (linux/macos/windows) to fine-grained support for 17+ OS variants including Android, FreeBSD, NetBSD, Emscripten, WASI, etc.

**Key Topics**:
- Current architecture analysis (Os enum, SUPPORTED_TARGETS, Buck constraints)
- Extended Os enum design (17 variants with custom Buck constraints)
- Implementation plan (6-week phased rollout)
- Code examples (BUCK generation, wrapper.bzl updates)
- Migration path (backward compatibility, coarse vs fine mode)
- Performance considerations (cfg cache, Buck analysis time)
- Risks and trade-offs (complexity, testing, ecosystem fragmentation)

**Use This When**:
- Planning to add Android, BSD, or Emscripten platform support
- Need to understand platform model architecture
- Evaluating fine-grained vs coarse platform granularity

**Related OpenSpec Changes**:
- `integrate-cross-targets` (uses coarse model)
- Future: `fine-grained-platform-model` (potential follow-up)

---

## Contributing

When adding new design documents:
1. Create a descriptive filename (kebab-case, `.md` extension)
2. Add entry to this README with status, audience, and summary
3. Link from related OpenSpec changes if applicable
4. Use consistent heading structure (see fine-grained-platform-support.md as template)
