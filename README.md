# nautilus-file-converter
Right-click image conversion for Nautilus. Install it once, then convert files from the context menu using ImageMagick under the hood.

## Features
- Fast conversions with tuned ImageMagick flags
- Quality presets for lossy formats (JPEG, WebP, AVIF)
  - High Quality (95): best quality, larger files
  - Balanced (85): good quality, reasonable size (default)
  - Fast/Small (70): faster conversion, smaller files
- Video to audio (MP3, M4A, WAV, FLAC, OGG, Opus) and GIF
- Context menu only shows converters that make sense for the file
- Separate metadata stripping option that creates a clean copy

### Menu Structure
When you right-click an image, you get:
```
Convert To →
  ├─ Image Formats →
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
  └─ Video Formats →
      ├─ MP3 (Audio)
      ├─ M4A (Audio)
      ├─ WAV (Audio)
      ├─ FLAC (Audio)
      ├─ OGG (Audio)
      ├─ Opus (Audio)
      └─ GIF (Animated)
Strip Metadata
```

## Supported Formats
Images: JPEG, PNG, WebP, AVIF, HEIC, TIFF, GIF, BMP, ICO, PDF
Video outputs: MP3, M4A, WAV, FLAC, OGG, Opus, GIF

## Requirements
- `nautilus-python` (GI bindings for Nautilus)
- ImageMagick (`magick` or `convert`)
- `ffmpeg` for video to audio/GIF conversions

## Compatibility
- Nautilus 3.0, 4.0, 4.1+
- The extension adapts to your Nautilus version automatically

## Installation
Clone the repository then run `./install.sh`, then restart Nautilus with `nautilus -q`.

Or install in one shot:
```bash
curl -fsSL https://github.com/MegalithOfficial/nautilus-file-converter/archive/refs/heads/main.tar.gz \
  | tar -xz && cd nautilus-file-converter-main && ./install.sh
```

## Usage
1. Right-click an image in Nautilus
2. Select **Convert To** → **Image Formats**
3. Pick a format
   - Lossless formats (PNG, TIFF, GIF, etc.) convert directly
   - Lossy formats (JPEG, WebP, AVIF) ask for a quality preset

For video files:
1. Right-click a video in Nautilus
2. Select **Convert To** → **Video Formats**
3. Choose an audio format or GIF

To strip metadata without converting:
1. Right-click an image in Nautilus
2. Select **Strip Metadata** (creates a `-stripped` copy)

## Troubleshooting
Menu missing:
1. Ensure `nautilus-python` is installed (e.g., `pacman -S nautilus-python` on Arch)
2. Restart Nautilus with `nautilus -q`
3. Check logs: `journalctl --user -b | rg -i "nautilus|file\\.converter"`

Video conversions failing:
- Ensure `ffmpeg` is installed (`ffmpeg -version`)
