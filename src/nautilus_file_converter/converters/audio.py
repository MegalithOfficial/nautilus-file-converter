from nautilus_file_converter import commands
from nautilus_file_converter.converters.base import (
    FFMPEG,
    Action,
    BaseConverter,
    file_extension,
    mime_type,
    shared_extension,
)


AUDIO_EXTENSIONS = {"aac", "aiff", "aif", "alac", "ape", "flac", "m4a", "mp3", "oga", "ogg", "opus", "wav", "wma"}

_ALIASES = {"aif": "aiff", "oga": "ogg"}

# (extension, label, codec args)
AUDIO_FORMATS = [
    ("mp3", "MP3", ["-c:a", "libmp3lame", "-q:a", "2"]),
    ("m4a", "M4A (AAC)", ["-c:a", "aac", "-b:a", "256k"]),
    ("opus", "Opus", ["-c:a", "libopus", "-b:a", "160k"]),
    ("ogg", "OGG Vorbis", ["-c:a", "libvorbis", "-q:a", "6"]),
    ("flac", "FLAC", ["-c:a", "flac"]),
    ("wav", "WAV", ["-c:a", "pcm_s16le"]),
]

# Containers that can carry the cover art of the source file.
_COVER_ART = {"mp3", "flac", "m4a"}


def ffmpeg_base(input_path):
    return [
        commands.find_executable("ffmpeg"),
        "-hide_banner",
        "-nostdin",
        "-y",
        "-v", "error",
        "-progress", "pipe:1",
        "-nostats",
        "-i", input_path,
    ]


class AudioConverter(BaseConverter):
    converter_id = "audio"
    label = "Audio"

    def available(self):
        return commands.has_executable("ffmpeg")

    def supports(self, file_info) -> bool:
        if not mime_type(file_info).startswith("audio/"):
            return False
        return file_extension(file_info) in AUDIO_EXTENSIONS

    def convert_items(self, file_infos):
        current = shared_extension(file_infos, _ALIASES)
        return [
            _convert_action(ext, label, codec)
            for ext, label, codec in AUDIO_FORMATS
            if ext != current
        ]


def _convert_action(ext, label, codec):
    def build(input_path, output_path, _workdir):
        cmd = ffmpeg_base(input_path)
        cmd.extend(["-map", "0:a", "-map_metadata", "0"])
        if ext in _COVER_ART:
            cmd.extend(["-map", "0:v?", "-c:v", "copy", "-disposition:v", "attached_pic"])
        cmd.extend(codec)
        cmd.append(output_path)
        return cmd

    return Action(
        f"to-{ext}",
        label,
        build,
        f"Converted to {label}",
        extension=ext,
        runner=FFMPEG,
    )
