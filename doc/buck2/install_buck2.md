## install buck2

ref: https://github.com/facebook/buck2/issues/1144#issue-3631172079
```bash
rustup install nightly-2025-08-01
cargo +nightly-2025-08-01 install --git https://github.com/facebook/buck2.git --rev c6bfcc629378a00921aa04597551442c9e2ea2eb buck2
```

## test buck2

```bash
mkdir test
cd test
git clone https://github.com/web3infra-foundation/libra.git
cd libra
buck2 build //:libra
```

- Built //:libra with `buck2 build //:libra`
- Binary output: `buck-out/v2/gen/root/b42aeba648b8c415/__libra__/libra`.
- Run library tests: `buck2 test //:libra-unittest`.
- Run CLI integration tests: `buck2 test //:command_test`.

