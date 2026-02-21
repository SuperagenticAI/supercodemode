#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${GEPA_SOURCE_DIR:-}"
DST="$ROOT_DIR/vendor/gepa_new_files"

if [[ -z "$SRC" ]]; then
  echo "Set GEPA_SOURCE_DIR to your gepa checkout path"
  echo "Example: GEPA_SOURCE_DIR=/path/to/gepa ./scripts/sync_gepa_vendor.sh"
  exit 1
fi

mkdir -p "$DST/src/gepa/adapters/code_mode_adapter" \
         "$DST/src/gepa/examples/code_mode_adapter" \
         "$DST/tests" \
         "$DST/docs/docs/guides" \
         "$DST/docs/docs/api/adapters" \
         "$DST/docs/scripts"

cp "$SRC/src/gepa/adapters/code_mode_adapter/__init__.py" "$DST/src/gepa/adapters/code_mode_adapter/"
cp "$SRC/src/gepa/adapters/code_mode_adapter/code_mode_adapter.py" "$DST/src/gepa/adapters/code_mode_adapter/"
cp "$SRC/src/gepa/adapters/code_mode_adapter/runners.py" "$DST/src/gepa/adapters/code_mode_adapter/"
cp "$SRC/src/gepa/adapters/code_mode_adapter/README.md" "$DST/src/gepa/adapters/code_mode_adapter/"

cp "$SRC/src/gepa/examples/code_mode_adapter/__init__.py" "$DST/src/gepa/examples/code_mode_adapter/"
cp "$SRC/src/gepa/examples/code_mode_adapter/code_mode_optimization_example.py" "$DST/src/gepa/examples/code_mode_adapter/"
cp "$SRC/src/gepa/examples/code_mode_adapter/code_mode_two_tool_showcase.py" "$DST/src/gepa/examples/code_mode_adapter/"
cp "$SRC/src/gepa/examples/code_mode_adapter/README.md" "$DST/src/gepa/examples/code_mode_adapter/"

cp "$SRC/tests/test_code_mode_adapter.py" "$DST/tests/"
cp "$SRC/tests/test_code_mode_runners.py" "$DST/tests/"

cp "$SRC/docs/docs/guides/code-mode-adapter.md" "$DST/docs/docs/guides/"
cp "$SRC/docs/docs/api/adapters/CodeModeAdapter.md" "$DST/docs/docs/api/adapters/"
cp "$SRC/docs/scripts/generate_api_docs.py" "$DST/docs/scripts/"

echo "Synced GEPA Code Mode files into $DST"
