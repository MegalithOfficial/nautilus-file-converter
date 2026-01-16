#!/usr/bin/env bash
set -euo pipefail

EXT_DIR="${HOME}/.local/share/nautilus-python/extensions"
DRY_RUN=false

if [[ "${1:-}" == "--dry-install" ]]; then
    DRY_RUN=true
    echo "Dry install mode: no packages will be installed."
fi

has_cmd() {
    command -v "$1" >/dev/null 2>&1
}

install_pkg() {
    local pkg="$1"

    if $DRY_RUN; then
        echo "[dry] Would install: $pkg"
        return
    fi

    if has_cmd pacman; then
        sudo pacman -S --needed --noconfirm "$pkg"
    elif has_cmd apt; then
        sudo apt install -y "$pkg"
    elif has_cmd dnf; then
        sudo dnf install -y "$pkg"
    elif has_cmd zypper; then
        sudo zypper install -y "$pkg"
    else
        echo "No supported package manager found. Install $pkg manually."
        return 1
    fi
}

echo "Checking ImageMagick..."
if ! has_cmd convert; then
    echo "ImageMagick not found."
    install_pkg imagemagick
else
    echo "ImageMagick found."
fi

echo "Checking ffmpeg..."
if ! has_cmd ffmpeg; then
    echo "ffmpeg not found."
    install_pkg ffmpeg
else
    echo "ffmpeg found."
fi

echo "Installing Nautilus extension files..."

mkdir -p "${EXT_DIR}"

rm -f  "${EXT_DIR}/nautilus_file_converter_extension.py"
rm -rf "${EXT_DIR}/nautilus_file_converter"

cp -f "src/nautilus_file_converter_extension.py" \
      "${EXT_DIR}/nautilus_file_converter_extension.py"

cp -R "src/nautilus_file_converter" \
      "${EXT_DIR}/nautilus_file_converter"

echo "Installed Nautilus File Converter to ${EXT_DIR}"

echo "Checking Nautilus Python bindings..."
python3 - <<'PY'
try:
    import gi
    try:
        gi.require_version("Nautilus", "4.1")
    except (ValueError, AttributeError):
        try:
            gi.require_version("Nautilus", "4.0")
        except (ValueError, AttributeError):
            gi.require_version("Nautilus", "3.0")

    from gi.repository import Nautilus  # noqa
    print("Nautilus GI bindings OK.")
except Exception as exc:
    print("Warning: Nautilus GI bindings not available.")
    print("Install package: python-nautilus / python3-nautilus")
    print(f"Details: {exc}")
PY

echo
echo "Installation complete."
echo "Restart Nautilus with:"
echo "  nautilus -q"
