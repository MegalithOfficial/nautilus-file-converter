# nautilus-file-converter
Right-click image conversion for Nautilus. Install it once, then convert files from the context menu using ImageMagick under the hood.

## Features
- Fast conversions with tuned ImageMagick flags
- Quality presets for lossy formats (JPEG, WebP, AVIF)
  - High Quality (95): best quality, larger files
  - Balanced (85): good quality, reasonable size (default)
  - Fast/Small (70): faster conversion, smaller files
- Context menu only shows converters that make sense for the file
- Separate metadata stripping option that creates a clean copy

### Menu Structure
When you right-click an image, you get:
```
Convert To →
  └─ Image Formats →
      ├─ JPEG →
      │   ├─ High Quality
      │   ├─ Balanced
      │   └─ Fast/Small
      ├─ WebP →
      │   ├─ High Quality
      │   ├─ Balanced
      │   └─ Fast/Small
      ├─ AVIF →
      │   ├─ High Quality
      │   ├─ Balanced
      │   └─ Fast/Small
      ├─ PNG (lossless)
      ├─ TIFF (lossless)
      ├─ GIF (lossless)
      ├─ BMP (lossless)
      ├─ HEIC
      ├─ Icon
      └─ PDF
Strip Metadata
```

## Supported Formats
Images: JPEG, PNG, WebP, AVIF, HEIC, TIFF, GIF, BMP, ICO, PDF

## Requirements
- `nautilus-python` (GI bindings for Nautilus)
- ImageMagick (`magick` or `convert`)

## Compatibility
- Nautilus 3.0, 4.0, 4.1+
- The extension adapts to your Nautilus version automatically

## Installation
Run `./install.sh`, then restart Nautilus with `nautilus -q`.

## Usage
1. Right-click an image in Nautilus
2. Select **Convert To** → **Image Formats**
3. Pick a format
   - Lossless formats (PNG, TIFF, GIF, etc.) convert directly
   - Lossy formats (JPEG, WebP, AVIF) ask for a quality preset

To strip metadata without converting:
1. Right-click an image in Nautilus
2. Select **Strip Metadata** (creates a `-stripped` copy)

## Troubleshooting
Menu missing:
1. Ensure `nautilus-python` is installed (e.g., `pacman -S nautilus-python` on Arch)
2. Restart Nautilus with `nautilus -q`
3. Check logs: `journalctl --user -b | rg -i "nautilus|file\\.converter"`
