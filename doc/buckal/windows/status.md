
# Windows support status?

I’m trying `cargo-buckal` on Windows 11 and I’m not sure if Windows is currently supported / expected to work end-to-end. Can you share the current status (supported / in-progress / known blockers) and any recommended workaround?

The failure I’m hitting looks like a Windows encoding issue: `rustc_action.py` crashes with `UnicodeDecodeError` while `argparse` is reading an `@...args` file.

## Environment

- OS: Windows 11 (`Microsoft Windows [Version 10.0.26200.7171]`)
- Rust: `rustc 1.92.0 (ded5c06cf 2025-12-08)` / `cargo 1.92.0 (344c4567c 2025-10-21)` (`stable-x86_64-pc-windows-msvc`)
- `cargo-buckal`: commit `ad0dd74c70572b779a27e19e0129eb83fb27ad0d`
- Buck2 installed from: `https://github.com/facebook/buck2.git` @ `c6bfcc629378a00921aa04597551442c9e2ea2eb` (installed with `nightly-2025-08-01`)

## Repro

```bash
# install buck2
rustup install nightly-2025-08-01
cargo +nightly-2025-08-01 install --git https://github.com/facebook/buck2.git --rev c6bfcc629378a00921aa04597551442c9e2ea2eb buck2

# build fd with buck2 on windows11
git clone -b v10.3.0 --depth 1 https://github.com/sharkdp/fd.git
cd fd
buck2 init
cargo run --manifest-path <cargo-buckal-path>\\Cargo.toml -- buckal migrate --buck2
buck2 build //:fd
```

```
$ buck2 build //:fd
Starting new buck2 daemon...
Connected to new buck2 daemon.
Action failed: root//third-party/rust/crates/strsim/0.11.1:strsim (rustc rlib)
Local command returned non-zero exit code 1
Reproduce locally: `env -- "BUCK_SCRATCH_PATH=buck-out\\v2\\tmp\\root\\82cd0cf4f4f4c628\\rustc\\rlib" "buck-out\\v2\\gen ...<omitted>... 4ffe0299acc57a2\\third-party\\rust\\crates\\strsim\\0.11.1\\__strsim__\\LPTL\\strsim-link-diag.args" (run `buck2 log what-failed` to get the full command)`
stdout:
stderr:
Traceback (most recent call last):
  File "C:\Users\10469\AppData\Local\Temp\buckal-fd-3jqmjrpe\fd\buck-out\v2\gen\prelude\97667764a66ee3d4\rust\tools\__rustc_action__\__rustc_action__\rustc_action.py", line 460, in <module>
    sys.exit(asyncio.run(main()))
             ~~~~~~~~~~~^^^^^^^^
  File "C:\Users\10469\AppData\Local\Temp\buckal-fd-3jqmjrpe\fd\buck-out\v2\gen\toolchains\97667764a66ee3d4\__cpython_archive__\cpython_archive\Lib\asyncio\runners.py", line 195, in run
    return runner.run(main)
           ~~~~~~~~~~^^^^^^
  File "C:\Users\10469\AppData\Local\Temp\buckal-fd-3jqmjrpe\fd\buck-out\v2\gen\toolchains\97667764a66ee3d4\__cpython_archive__\cpython_archive\Lib\asyncio\runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "C:\Users\10469\AppData\Local\Temp\buckal-fd-3jqmjrpe\fd\buck-out\v2\gen\toolchains\97667764a66ee3d4\__cpython_archive__\cpython_archive\Lib\asyncio\base_events.py", line 725, in run_until_complete
    return future.result()
           ~~~~~~~~~~~~~^^
  File "C:\Users\10469\AppData\Local\Temp\buckal-fd-3jqmjrpe\fd\buck-out\v2\gen\prelude\97667764a66ee3d4\rust\tools\__rustc_action__\__rustc_action__\rustc_action.py", line 318, in main
    args = arg_parse()
  File "C:\Users\10469\AppData\Local\Temp\buckal-fd-3jqmjrpe\fd\buck-out\v2\gen\prelude\97667764a66ee3d4\rust\tools\__rustc_action__\__rustc_action__\rustc_action.py", line 192, in arg_parse
    return Args(**vars(parser.parse_args()))
                       ~~~~~~~~~~~~~~~~~^^
  File "C:\Users\10469\AppData\Local\Temp\buckal-fd-3jqmjrpe\fd\buck-out\v2\gen\toolchains\97667764a66ee3d4\__cpython_archive__\cpython_archive\Lib\argparse.py", line 1898, in parse_args
    args, argv = self.parse_known_args(args, namespace)
                 ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "C:\Users\10469\AppData\Local\Temp\buckal-fd-3jqmjrpe\fd\buck-out\v2\gen\toolchains\97667764a66ee3d4\__cpython_archive__\cpython_archive\Lib\argparse.py", line 1908, in parse_known_args
    return self._parse_known_args2(args, namespace, intermixed=False)
           ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\10469\AppData\Local\Temp\buckal-fd-3jqmjrpe\fd\buck-out\v2\gen\toolchains\97667764a66ee3d4\__cpython_archive__\cpython_archive\Lib\argparse.py", line 1937, in _parse_known_args2
    namespace, args = self._parse_known_args(args, namespace, intermixed)
                      ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\10469\AppData\Local\Temp\buckal-fd-3jqmjrpe\fd\buck-out\v2\gen\toolchains\97667764a66ee3d4\__cpython_archive__\cpython_archive\Lib\argparse.py", line 1951, in _parse_known_args
    arg_strings = self._read_args_from_files(arg_strings)
  File "C:\Users\10469\AppData\Local\Temp\buckal-fd-3jqmjrpe\fd\buck-out\v2\gen\toolchains\97667764a66ee3d4\__cpython_archive__\cpython_archive\Lib\argparse.py", line 2274, in _read_args_from_files
    arg_strings = self._read_args_from_files(arg_strings)
  File "C:\Users\10469\AppData\Local\Temp\buckal-fd-3jqmjrpe\fd\buck-out\v2\gen\toolchains\97667764a66ee3d4\__cpython_archive__\cpython_archive\Lib\argparse.py", line 2271, in _read_args_from_files
    for arg_line in args_file.read().splitlines():
                    ~~~~~~~~~~~~~~^^
  File "<frozen codecs>", line 325, in decode
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xf8 in position 856: invalid start byte
Build ID: 7578aa37-00f4-45e8-99d9-513ca3c18f03
Network: Up: 0B  Down: 35MiB
Loading targets.   Remaining     0/84                                                              239 dirs read, 491 targets declared
Analyzing targets. Remaining     0/373                                                             8267 actions, 14657 artifacts declared
Executing actions. Remaining     0/771                                                             20.5s exec time total
Command: build.    Finished 151 local
Time elapsed: 46.5s
BUILD FAILED
Failed to build 'root//third-party/rust/crates/strsim/0.11.1:strsim (cfg:<empty>#54ffe0299acc57a2)'
```
