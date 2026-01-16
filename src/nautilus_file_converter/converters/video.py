import os

from nautilus_file_converter import commands, notify
from nautilus_file_converter.converters.base import BaseConverter, ConversionTarget


class VideoConverter(BaseConverter):
    converter_id = "video"
    label = "Video Formats"

    targets = [
        ConversionTarget("mp3", "MP3 (Audio)", "mp3"),
        ConversionTarget("m4a", "M4A (Audio)", "m4a"),
        ConversionTarget("wav", "WAV (Audio)", "wav"),
        ConversionTarget("flac", "FLAC (Audio)", "flac"),
        ConversionTarget("ogg", "OGG (Audio)", "ogg"),
        ConversionTarget("opus", "Opus (Audio)", "opus"),
        ConversionTarget("gif", "GIF (Animated)", "gif"),
    ]

    def supports(self, file_info) -> bool:
        if file_info.is_directory():
            return False

        mime_type = file_info.get_mime_type()
        if not (mime_type and mime_type.startswith("video/")):
            return False

        name = file_info.get_name() if hasattr(file_info, "get_name") else None
        if name:
            ext = os.path.splitext(name)[1].lstrip(".").lower()
            if ext in _AUDIO_EXTENSIONS or ext == "gif":
                return False

        return True

    def convert(self, input_path, output_path, target):
        cmd = commands.build_ffmpeg_command(input_path, output_path)
        if not cmd:
            notify.notify_error(
                "Video conversion failed",
                "ffmpeg not found. Install ffmpeg.",
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
                f"Video conversion failed ({target.label})",
                message,
            )

        commands.run_command_async(cmd, on_success=_on_success, on_error=_on_error)


def _format_paths(input_path, output_path):
    return f"{os.path.basename(input_path)} -> {os.path.basename(output_path)}"


_AUDIO_EXTENSIONS = {
    "aac",
    "flac",
    "m4a",
    "mp3",
    "ogg",
    "opus",
    "wav",
}
