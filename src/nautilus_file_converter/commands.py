import collections
import re
import shutil

from gi.repository import Gio, GLib  # type: ignore


# Nautilus embeds Python without ever releasing the GIL, so Python threads
# barely run inside it. Everything here uses Gio.Subprocess and async reads
# instead, which keeps all callbacks on the GLib main loop.

_SINGLE_FRAME_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "ico", "heic"}
_PROGRESS_LINE = re.compile(r"^[a-z0-9_]+=")
_ACTIVE = set()


def find_executable(candidates):
    for candidate in candidates:
        if shutil.which(candidate):
            return candidate
    return None


def _extension(path):
    return path.lower().rsplit(".", 1)[-1]


def build_magick_command(input_path, output_path, quality=85):
    """
    Build an ImageMagick command for a single conversion.

    Returns None if ImageMagick is not installed.
    """
    binary = find_executable(["magick", "convert"])
    if not binary:
        return None

    ext = _extension(output_path)

    # Animated or multi-page input would otherwise be split into
    # name-0.jpg, name-1.jpg, ... for formats that hold one frame.
    source = f"{input_path}[0]" if ext in _SINGLE_FRAME_EXTENSIONS else input_path

    cmd = [binary, source, "-auto-orient", "-quality", str(quality)]

    if ext in ["jpg", "jpeg"]:
        cmd.extend(["-interlace", "Plane"])
    elif ext == "png":
        cmd.extend(["-define", "png:compression-level=6"])
    elif ext == "webp":
        cmd.extend(["-define", "webp:method=4"])
    elif ext == "avif":
        cmd.extend(["-define", "avif:speed=6"])
    elif ext == "ico":
        # ICO frames are capped at 256x256.
        cmd.extend(["-resize", "256x256>"])

    cmd.append(output_path)
    return cmd


def build_magick_strip_command(input_path, output_path):
    binary = find_executable(["magick", "convert"])
    if not binary:
        return None

    return [binary, input_path, "-strip", output_path]


def build_ffmpeg_command(input_path, output_path):
    """
    Build an ffmpeg command for video to audio/GIF conversions.

    Progress is written to stdout as key=value lines, errors to stderr.
    Returns None if ffmpeg is not installed.
    """
    binary = find_executable(["ffmpeg"])
    if not binary:
        return None

    ext = _extension(output_path)
    cmd = [
        binary,
        "-hide_banner",
        "-nostdin",
        "-y",
        "-v", "error",
        "-progress", "pipe:1",
        "-nostats",
        "-i", input_path,
    ]

    if ext == "mp3":
        cmd.extend(["-vn", "-c:a", "libmp3lame", "-q:a", "2"])
    elif ext in ["m4a", "aac"]:
        cmd.extend(["-vn", "-c:a", "aac", "-b:a", "192k"])
    elif ext == "wav":
        cmd.extend(["-vn", "-c:a", "pcm_s16le"])
    elif ext == "flac":
        cmd.extend(["-vn", "-c:a", "flac"])
    elif ext == "ogg":
        cmd.extend(["-vn", "-c:a", "libvorbis", "-q:a", "5"])
    elif ext == "opus":
        cmd.extend(["-vn", "-c:a", "libopus", "-b:a", "128k"])
    elif ext == "gif":
        cmd.extend([
            "-filter_complex",
            "fps=12,scale=w='min(640,iw)':h=-2:flags=lanczos,split[s0][s1];"
            "[s0]palettegen[p];[s1][p]paletteuse",
            "-loop", "0",
        ])

    cmd.append(output_path)
    return cmd


def build_ffprobe_duration_command(input_path):
    binary = find_executable(["ffprobe"])
    if not binary:
        return None

    return [
        binary,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        input_path,
    ]


def run_command_async(args, on_success=None, on_error=None, on_line=None):
    """
    Run a command without blocking the Nautilus main loop.

    stderr is merged into stdout and read line by line. on_line(line) may
    return True to consume a line; unconsumed lines are kept and the last
    few are passed to on_error(message) on failure.
    """
    try:
        proc = Gio.Subprocess.new(
            args,
            Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_MERGE,
        )
    except GLib.Error as exc:
        _call(on_error, exc.message)
        return

    stream = proc.get_stdout_pipe()
    job = (proc, stream)
    _ACTIVE.add(job)
    tail = collections.deque(maxlen=8)
    pending = bytearray()

    def _handle_line(raw):
        line = raw.decode("utf-8", errors="replace").strip()
        if line and not _call(on_line, line):
            tail.append(line)

    def _on_read(stream, result):
        try:
            chunk = stream.read_bytes_finish(result).get_data()
        except GLib.Error:
            chunk = b""

        if not chunk:
            if pending:
                _handle_line(bytes(pending))
            proc.wait_async(None, _on_exit)
            return

        pending.extend(chunk)
        *lines, rest = pending.split(b"\n")
        pending[:] = rest
        for raw in lines:
            _handle_line(raw)
        stream.read_bytes_async(8192, GLib.PRIORITY_DEFAULT, None, _on_read)

    def _on_exit(proc, result):
        _ACTIVE.discard(job)
        try:
            proc.wait_finish(result)
        except GLib.Error:
            pass

        if proc.get_successful():
            _call(on_success)
        else:
            message = "\n".join(tail) or f"Exited with status {proc.get_exit_status()}"
            _call(on_error, message)

    stream.read_bytes_async(8192, GLib.PRIORITY_DEFAULT, None, _on_read)


def run_ffmpeg_async(args, duration, on_progress=None, on_success=None, on_error=None):
    def _on_line(line):
        if not _PROGRESS_LINE.match(line):
            return False

        key, _, value = line.partition("=")
        if key == "out_time_us" and on_progress:
            try:
                elapsed = max(0.0, int(value) / 1_000_000)
            except ValueError:
                return True
            percent = None
            if duration:
                percent = int(min(100, elapsed / duration * 100))
            on_progress(percent, elapsed)
        return True

    run_command_async(args, on_success=on_success, on_error=on_error, on_line=_on_line)


def probe_duration_async(input_path, callback):
    """Call callback(seconds) with the media duration, or None if unknown."""
    cmd = build_ffprobe_duration_command(input_path)
    if not cmd:
        callback(None)
        return

    lines = []

    def _on_line(line):
        lines.append(line)
        return True

    def _on_done():
        try:
            duration = float(lines[0]) if lines else None
        except ValueError:
            duration = None
        callback(duration if duration and duration > 0 else None)

    run_command_async(
        cmd,
        on_success=_on_done,
        on_error=lambda _message: callback(None),
        on_line=_on_line,
    )


def _call(callback, *args):
    if not callback:
        return None

    try:
        return callback(*args)
    except Exception as exc:
        print(f"nautilus-file-converter: callback failed: {exc!r}")
        return None
