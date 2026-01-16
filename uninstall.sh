#!/usr/bin/env bash
set -euo pipefail

EXT_DIR="${HOME}/.local/share/nautilus-python/extensions"

echo "Removing Nautilus File Converter..."

rm -f  "${EXT_DIR}/nautilus_file_converter_extension.py"
rm -rf "${EXT_DIR}/nautilus_file_converter"

echo "Removed from ${EXT_DIR}"
echo "Restart Nautilus to unload the extension:"
echo "  nautilus -q"
