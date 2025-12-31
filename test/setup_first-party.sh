#!/bin/bash

source /home/seven/Workspace/r8s_c/buckal_c/.venv/bin/activate

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$SCRIPT_DIR/first-party-demo"
cd "$ROOT_DIR"

echo "=== Initializing Buck2 ==="
git clean -fdx
buck2 clean
buck2 init

echo "=== Updating .buckconfig ==="
# Add buckal to cells section
sed -i '/^  none = none$/a\  buckal = buckal' .buckconfig

# Add buckal = git to external_cells section
sed -i '/^  prelude = bundled$/a\  buckal = git' .buckconfig

# Add external_cell_buckal section after external_cells section
sed -i '/^\[external_cells\]/,/^$/{
  /^$/i\
\
[external_cell_buckal]\
  git_origin = https://github.com/buck2hub/buckal-bundles\
  commit_hash = f9c4f306b1aad816fa520fe361f4f03d28cd5b7b
}' .buckconfig

echo "=== Migrating demo-util ==="
cd $ROOT_DIR/crates/demo-util/
touch BUCK
python3 /home/seven/Workspace/r8s_c/buckal_c/script/cargo-buckal-wrapper.py --origin -- migrate --separate


echo "=== Migrating demo-lib ==="
cd $ROOT_DIR/crates/demo-lib/
touch BUCK
python3 /home/seven/Workspace/r8s_c/buckal_c/script/cargo-buckal-wrapper.py --origin -- migrate --separate

buck2 clean

echo "=== Migrating demo-lib ==="
cd $ROOT_DIR/crates/demo-lib/
python3 /home/seven/Workspace/r8s_c/buckal_c/script/cargo-buckal-wrapper.py --origin -- migrate --separate

echo "=== Migrating demo-root ==="
cd $ROOT_DIR/
python3 /home/seven/Workspace/r8s_c/buckal_c/script/cargo-buckal-wrapper.py --origin -- migrate --separate

buck2 build //:
