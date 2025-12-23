What prelude = native means in Buck2

prelude = native is a pattern used in Buck2 BUCK files to create a convenient alias for accessing the build system's native rules and functions.

The Pattern Explained

When you see:

prelude = native

This is creating a local variable named prelude that points to the native module, which contains all the built-in Buck2 rules and functions.

Why This Pattern Exists

1. Convenience: It provides a shorter, more convenient way to access Buck2 rules
2. Consistency: It creates a consistent naming pattern across different BUCK files
3. Readability: It makes BUCK files more readable by using prelude.rule_name() instead of the longer native.rule_name()

What native Actually Contains

The native module (defined in /home/seven/Workspace/r8s_c/buckal_c/buck2/prelude/native.bzl) is a comprehensive collection that includes:

1. Built-in Buck2 rules like:
  • cxx_library, rust_library, python_library
  • cxx_binary, rust_binary
  • genrule, export_file, filegroup
  • Platform-specific rules like android_library, apple_bundle
2. Utility functions like:
  • package_name(), glob()
  • select(), read_config()
  • Various helper functions for different languages
3. Macro wrappers that provide additional functionality on top of base rules

Usage Examples

Instead of writing:

native.cxx_library(
    name = "my_lib",
    srcs = ["main.cpp"],
    visibility = ["PUBLIC"],
)

You can write:

prelude = native

prelude.cxx_library(
    name = "my_lib",
    srcs = ["main.cpp"],
    visibility = ["PUBLIC"],
)

Context in Different Files

The pattern appears in two main contexts:

1. In the prelude itself (/home/seven/Workspace/r8s_c/buckal_c/buck2/prelude/native.bzl): Here native is constructed as a struct containing all the rules and functions
2. In shim files (/home/seven/Workspace/r8s_c/buckal_c/buck2/shim/shims.bzl): Here prelude = native is used to provide compatibility layers

Summary

prelude = native is essentially a naming convention that creates a convenient alias for accessing Buck2's built-in build rules and utilities. It's like importing a module and giving it a shorter name, making BUCK files cleaner and more consistent across the codeba
se.
seven@buck2✨ for `source_listing()`, explain `Relative paths: All file paths are made relative to the current package` by example
• I'll explain how the relative paths work in source_listing() with a concrete example. Let me first look at the implementation again to understand the exact logic:
• Used ReadFile (prelude/utils/source_listing_impl.bzl)
• Now let me create a practical example to demonstrate how the relative paths work:
• Used WriteFile (example_demo.sh)
  Rejected by user
seven@buck2✨ just print ehte example
• Here's a concrete example to explain how relative paths work in source_listing():

Directory Structure Example

main_pkg/
├── BUCK                    # source_listing() called here
├── main.cpp
├── main.h
├── sub_pkg1/
│   ├── BUCK               # source_listing() called here too
│   ├── utils.cpp
│   └── utils.h
└── sub_pkg2/
    ├── BUCK               # source_listing() called here too
    ├── helpers.cpp
    └── helpers.h

How Relative Paths Work

When source_listing() is called in main_pkg/BUCK:

• main.cpp → "main.cpp" (relative to main_pkg/)
• main.h → "main.h" (relative to main_pkg/)
• sub_pkg1/utils.cpp → "sub_pkg1/utils.cpp" (relative to main_pkg/)
• sub_pkg1/utils.h → "sub_pkg1/utils.h" (relative to main_pkg/)
• sub_pkg2/helpers.cpp → "sub_pkg2/helpers.cpp" (relative to main_pkg/)
• sub_pkg2/helpers.h → "sub_pkg2/helpers.h" (relative to main_pkg/)

When source_listing() is called in main_pkg/sub_pkg1/BUCK:

• utils.cpp → "utils.cpp" (relative to sub_pkg1/)
• utils.h → "utils.h" (relative to sub_pkg1/)

The key insight: All file paths are made relative to the package directory where source_listing() is called, not relative to the repository root!

This is achieved by the code:

rel_loc = d.label.package.removeprefix(package)
sources.update({rel_loc + "/" + p: art for p, art in d[SourceListingInfo].sources.items()})

Where package is the current package path, and rel_loc strips that prefix from sub-package paths.