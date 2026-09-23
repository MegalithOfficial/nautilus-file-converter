import os
import re

from nautilus_file_converter import commands
from nautilus_file_converter.converters.base import (
    Action,
    BaseConverter,
    Submenu,
    file_extension,
    mime_type,
    shared_extension,
)


_ALIASES = {"jpeg": "jpg", "jpe": "jpg", "tif": "tiff", "heif": "heic"}

# (extension, label, lossy)
_FORMATS = [
    ("jpg", "JPEG", True),
    ("png", "PNG", False),
    ("webp", "WebP", True),
    ("avif", "AVIF", True),
    ("jxl", "JPEG XL", True),
    ("heic", "HEIC", True),
    ("tiff", "TIFF", False),
    ("gif", "GIF", False),
    ("bmp", "BMP", False),
    ("ico", "Icon", False),
    ("pdf", "PDF", False),
]

_QUALITIES = [
    ("high", "High Quality", 95),
    ("balanced", "Balanced", 85),
    ("small", "Smaller File", 70),
]

# Formats that hold a single frame. Animated or multi-page input would
# otherwise be split into name-0.jpg, name-1.jpg, ...
_SINGLE_FRAME = {"jpg", "png", "bmp", "ico", "heic", "jxl"}

_RESIZES = [
    ("75pct", "75%", "75%"),
    ("50pct", "50%", "50%"),
    ("25pct", "25%", "25%"),
    ("3840px", "Fit 3840 px (4K)", "3840x3840>"),
    ("1920px", "Fit 1920 px (Full HD)", "1920x1920>"),
    ("1280px", "Fit 1280 px", "1280x1280>"),
    ("640px", "Fit 640 px", "640x640>"),
]

_TRANSFORMS = [
    ("rotate_right", "Rotate Right", ["-rotate", "90"], "rotated", "Rotated"),
    ("rotate_left", "Rotate Left", ["-rotate", "-90"], "rotated", "Rotated"),
    ("rotate_180", "Rotate 180°", ["-rotate", "180"], "rotated", "Rotated"),
    ("flip_h", "Flip Horizontally", ["-flop"], "flipped", "Flipped"),
    ("flip_v", "Flip Vertically", ["-flip"], "flipped", "Flipped"),
]


class ImageConverter(BaseConverter):
    converter_id = "image"
    label = "Image"

    def available(self):
        return commands.has_executable("magick", "convert")

    def supports(self, file_info) -> bool:
        mime = mime_type(file_info)
        if mime.startswith("image/"):
            return True
        return not file_info.is_directory() and file_extension(file_info) in {"gif", "heic", "jxl"}

    def convert_items(self, file_infos):
        current = shared_extension(file_infos, _ALIASES)
        items = []
        for ext, label, lossy in _FORMATS:
            if ext == current:
                continue

            if not lossy:
                items.append(_convert_action(ext, label, None))
                continue

            items.append(Submenu(
                f"to-{ext}",
                label,
                [_convert_action(ext, label, quality) for quality in _QUALITIES],
            ))
        return items

    def tool_items(self, file_infos):
        items = [
            Submenu("resize", "Resize", [
                _tool_action(f"resize-{key}", label, ["-resize", geometry], key, f"Resized ({label})")
                for key, label, geometry in _RESIZES
            ]),
            Submenu("rotate", "Rotate / Flip", [
                _tool_action(key, label, args, suffix, done)
                for key, label, args, suffix, done in _TRANSFORMS
            ]),
            _tool_action("grayscale", "Grayscale", ["-colorspace", "Gray"], "gray", "Converted to grayscale"),
            _tool_action("strip", "Strip Metadata", ["-strip"], "stripped", "Metadata stripped"),
        ]
        if len(file_infos) > 1:
            items.append(Action(
                "combine-pdf",
                "Combine into PDF",
                _build_combine_pdf,
                "Combined into PDF",
                extension="pdf",
                suffix="combined",
                combine=True,
            ))
        return items


def _magick():
    return commands.find_executable("magick", "convert")


def _source(input_path, output_ext):
    if output_ext in _SINGLE_FRAME:
        return f"{input_path}[0]"
    return input_path


def _convert_action(ext, label, quality):
    if quality:
        key, quality_label, value = quality
        name = f"to-{ext}-{key}"
        item_label = quality_label
        done = f"Converted to {label} ({quality_label})"
    else:
        value = 92
        name = f"to-{ext}"
        item_label = label
        done = f"Converted to {label}"

    def build(input_path, output_path, _workdir):
        cmd = [_magick(), _source(input_path, ext), "-auto-orient", "-quality", str(value)]
        if ext == "jpg":
            cmd.extend(["-interlace", "Plane"])
        elif ext == "png":
            cmd.extend(["-define", "png:compression-level=6"])
        elif ext == "webp":
            cmd.extend(["-define", "webp:method=4"])
        elif ext == "avif":
            cmd.extend(["-define", "heic:speed=6"])
        elif ext == "jxl":
            cmd.extend(["-define", "jxl:effort=5"])
        elif ext == "ico":
            # ICO frames are capped at 256x256.
            cmd.extend(["-resize", "256x256>"])
        cmd.append(output_path)
        return cmd

    return Action(name, item_label, build, done, extension=ext)


def _tool_action(name, label, args, suffix, done):
    def build(input_path, output_path, _workdir):
        cmd = [_magick(), input_path]
        if input_path.lower().endswith(".gif"):
            # Operate on full frames, not the deltas GIFs store.
            cmd.append("-coalesce")
        cmd.extend(["-auto-orient", *args])
        if input_path.lower().endswith(".gif"):
            cmd.extend(["-layers", "Optimize"])
        cmd.append(output_path)
        return cmd

    return Action(name, label, build, done, suffix=suffix)


def _build_combine_pdf(input_paths, output_path, _workdir):
    sources = [f"{path}[0]" for path in sorted(input_paths, key=_natural_key)]
    return [_magick(), *sources, "-auto-orient", "-quality", "92", output_path]


def _natural_key(path):
    # page2.png before page10.png
    name = os.path.basename(path).lower()
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", name)]
