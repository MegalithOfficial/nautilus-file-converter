from nautilus_file_converter import commands
from nautilus_file_converter.converters.audio import AUDIO_EXTENSIONS, AUDIO_FORMATS, ffmpeg_base
from nautilus_file_converter.converters.base import (
    FFMPEG,
    Action,
    BaseConverter,
    Submenu,
    file_extension,
    mime_type,
    shared_extension,
)


_H264 = [
    "-c:v", "libx264", "-preset", "medium", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
]

# x264 needs even dimensions.
_EVEN = "scale=trunc(iw/2)*2:trunc(ih/2)*2"

# (extension, label, args, done)
_VIDEO_FORMATS = [
    ("mp4", "MP4 (H.264)", ["-vf", _EVEN, "-crf", "20", *_H264], "Converted to MP4"),
    ("webm", "WebM (VP9)", [
        "-c:v", "libvpx-vp9", "-crf", "32", "-b:v", "0", "-row-mt", "1",
        "-deadline", "good", "-cpu-used", "4",
        "-c:a", "libopus", "-b:a", "128k",
    ], "Converted to WebM"),
    ("mkv", "MKV (no re-encode)", ["-map", "0", "-c", "copy"], "Remuxed to MKV"),
]

# (key, label, short side limit, crf)
_COMPRESS = [
    ("1080", "Smaller (1080p)", 1080, 26),
    ("720", "Much Smaller (720p)", 720, 29),
    ("480", "Tiny (480p)", 480, 32),
]


class VideoConverter(BaseConverter):
    converter_id = "video"
    label = "Video"

    def available(self):
        return commands.has_executable("ffmpeg")

    def supports(self, file_info) -> bool:
        if not mime_type(file_info).startswith("video/"):
            return False
        ext = file_extension(file_info)
        return ext not in AUDIO_EXTENSIONS and ext != "gif"

    def convert_items(self, file_infos):
        current = shared_extension(file_infos)
        video = [
            _action(f"to-{ext}", label, args, done, extension=ext)
            for ext, label, args, done in _VIDEO_FORMATS
            if ext != current
        ]
        gif = _action(
            "to-gif",
            "Animated GIF",
            [
                "-filter_complex",
                "fps=12,scale=w='min(640,iw)':h='min(640,ih)'"
                ":force_original_aspect_ratio=decrease:flags=lanczos,split[s0][s1];"
                "[s0]palettegen[p];[s1][p]paletteuse",
                "-loop", "0",
            ],
            "Converted to GIF",
            extension="gif",
        )
        audio = Submenu("extract-audio", "Extract Audio", [
            _action(f"audio-{ext}", label, ["-vn", "-map", "0:a:0", *codec], f"Extracted audio ({label})", extension=ext)
            for ext, label, codec in AUDIO_FORMATS
        ])
        return [*video, gif, audio]

    def tool_items(self, file_infos):
        return [
            Submenu("compress", "Compress", [
                _action(
                    f"compress-{key}",
                    label,
                    ["-vf", _fit_short_side(limit), "-crf", str(crf), *_H264],
                    f"Compressed ({label})",
                    extension="mp4",
                    suffix=f"{key}p",
                )
                for key, label, limit, crf in _COMPRESS
            ]),
            _action(
                "mute",
                "Remove Audio",
                ["-map", "0", "-map", "-0:a", "-c", "copy"],
                "Audio removed",
                suffix="muted",
            ),
        ]


def _fit_short_side(limit):
    # Scale the shorter side down to `limit`, never up, keeping both even.
    return (
        f"scale='if(gte(iw,ih),-2,trunc(min({limit},iw)/2)*2)'"
        f":'if(gte(iw,ih),trunc(min({limit},ih)/2)*2,-2)'"
    )


def _action(name, label, args, done, extension=None, suffix=None):
    def build(input_path, output_path, _workdir):
        return [*ffmpeg_base(input_path), *args, output_path]

    return Action(
        name,
        label,
        build,
        done,
        extension=extension,
        suffix=suffix,
        runner=FFMPEG,
        queue="heavy",
        progress=True,
    )
