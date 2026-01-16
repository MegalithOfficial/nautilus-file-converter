import os

from nautilus_file_converter import commands, notify
from nautilus_file_converter.converters.base import BaseConverter, ConversionTarget


class ImageConverter(BaseConverter):
    converter_id = "image"
    label = "Image Formats"

    _base_targets = [
        ConversionTarget("jpg", "JPEG", "jpg"),
        ConversionTarget("png", "PNG", "png"),
        ConversionTarget("webp", "WebP", "webp"),
        ConversionTarget("avif", "AVIF", "avif"),
        ConversionTarget("tiff", "TIFF", "tiff"),
        ConversionTarget("gif", "GIF", "gif"),
        ConversionTarget("bmp", "BMP", "bmp"),
        ConversionTarget("heic", "HEIC", "heic"),
        ConversionTarget("ico", "Icon", "ico"),
        ConversionTarget("pdf", "PDF", "pdf"),
    ]

    @property
    def targets(self):
        """Generate targets with quality variants for lossy formats."""
        result = []
        for base_target in self._base_targets:
            variants = self.get_quality_variants(base_target)
            result.extend(variants)
        return result

    def supports(self, file_info) -> bool:
        if file_info.is_directory():
            return False

        mime_type = file_info.get_mime_type()
        return bool(mime_type and mime_type.startswith("image/"))

    def convert(self, input_path, output_path, target):
        cmd = commands.build_magick_command(input_path, output_path, quality=target.quality)
        if not cmd:
            notify.notify_error(
                "Image conversion failed",
                "ImageMagick not found. Install magick or convert.",
            )
            return

        def _on_success():
            notify.notify_success(
                f"Converted to {target.label}",
                _format_paths(input_path, output_path),
            )

        def _on_error(result):
            message = result.stderr.strip() if result.stderr else "Conversion failed"
            notify.notify_error(
                f"Image conversion failed ({target.label})",
                message,
            )

        commands.run_command_async(cmd, on_success=_on_success, on_error=_on_error)


def _format_paths(input_path, output_path):
    return f"{os.path.basename(input_path)} -> {os.path.basename(output_path)}"
