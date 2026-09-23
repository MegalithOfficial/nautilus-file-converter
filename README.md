# nautilus-file-converter

A Nautilus extension that adds file conversion to the right-click menu. It uses ImageMagick for images, ffmpeg for audio and video, and LibreOffice for office documents.

## Supported conversions

| Input | Output |
| --- | --- |
| Images | JPEG, PNG, WebP, AVIF, JPEG XL, HEIC, TIFF, GIF, BMP, ICO, PDF |
| Video | MP4 (H.264), WebM (VP9), MKV (remux), animated GIF, audio track |
| Audio | MP3, M4A (AAC), Opus, OGG Vorbis, FLAC, WAV |
| Text documents | PDF, DOCX, ODT, RTF, TXT |
| Spreadsheets | PDF, XLSX, ODS, CSV |
| Presentations | PDF, PPTX, ODP |

JPEG, WebP, AVIF, JPEG XL and HEIC offer three quality presets: 95, 85 and 70.

Audio conversions keep tags. Cover art is kept for MP3, M4A and FLAC.

## Tools

| Input | Tool |
| --- | --- |
| Images | Resize, rotate, flip, grayscale, strip metadata, combine into one PDF |
| Video | Compress to 1080p, 720p or 480p (H.264), remove audio |

## Behavior

- Output is written next to the source file. Existing files are never overwritten: if `photo.webp` exists, the result is saved as `photo-1.webp`.
- Selecting several files runs them as one batch with a single notification when it finishes.
- Jobs are queued. Video encodes run two at a time, image jobs scale with the CPU count, and LibreOffice runs one document at a time.
- Videos and batches of three or more files show a progress window with a Cancel button. Cancelling stops the running process and removes the partial output.
- The menu hides the source format and any category whose backend is not installed. Mixed selections get one submenu per file type.

## Requirements

| Package | Needed for |
| --- | --- |
| `nautilus-python` | Loading the extension |
| ImageMagick 6 or 7 | Images |
| `ffmpeg`, `ffprobe` | Audio and video |
| LibreOffice | Documents (optional) |
| `zenity` | Progress windows (optional) |
| `notify-send` | Notifications (optional) |

AVIF, HEIC and JPEG XL depend on the delegates your ImageMagick build includes. Check with `magick -list format`.

Tested with Nautilus 4.1 (GNOME 50). The extension also targets the 3.0 and 4.0 APIs.

## Installation

```bash
git clone https://github.com/MegalithOfficial/nautilus-file-converter
cd nautilus-file-converter
./install.sh
nautilus -q
```

`install.sh` copies the extension to `~/.local/share/nautilus-python/extensions` and installs ImageMagick and ffmpeg through pacman, apt, dnf or zypper if they are missing. Pass `--dry-install` to skip package installation.

To remove it, run `./uninstall.sh` and restart Nautilus.

## Troubleshooting

**The menu does not appear.** Make sure `nautilus-python` is installed (`python-nautilus` on Arch, `python3-nautilus` on Debian and Ubuntu). Then run `nautilus -q` and start `nautilus` from a terminal to see Python errors.

**A category is missing.** The matching backend (`magick`, `ffmpeg` or `soffice`) is not on `PATH`.

**A conversion fails.** The notification shows the last lines of the tool's error output.

## License

See [LICENSE](LICENSE).
