import collections
import functools
import re
import shutil

from gi.repository import Gio, GLib  # type: ignore


# Nautilus embeds Python without ever releasing the GIL, so Python threads
# barely run inside it. Everything here uses Gio.Subprocess and async reads
# instead, which keeps all callbacks on the GLib main loop.

_PROGRESS_LINE = re.compile(r"^[a-z0-9_]+=")
_ACTIVE = set()


@functools.lru_cache(maxsize=None)
def find_executable(*candidates):
    for candidate in candidates:
        if shutil.which(candidate):
            return candidate
    return None


def has_executable(*candidates):
    return find_executable(*candidates) is not None


def run_command_async(args, on_success=None, on_error=None, on_line=None):
    """
    Run a command without blocking the Nautilus main loop.

    stderr is merged into stdout and read line by line. on_line(line) may
    return True to consume a line; unconsumed lines are kept and the last
    few are passed to on_error(message) on failure.

    Returns the Gio.Subprocess, or None if it could not be started.
    """
    try:
        proc = Gio.Subprocess.new(
            args,
            Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_MERGE,
        )
    except GLib.Error as exc:
        _call(on_error, exc.message)
        return None

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
            if proc.get_if_exited():
                status = f"Exited with status {proc.get_exit_status()}"
            else:
                status = f"Killed by signal {proc.get_term_sig()}"
            message = "\n".join(tail) or status
            _call(on_error, message)

    stream.read_bytes_async(8192, GLib.PRIORITY_DEFAULT, None, _on_read)
    return proc


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

    return run_command_async(args, on_success=on_success, on_error=on_error, on_line=_on_line)


def probe_duration_async(input_path, callback):
    """Call callback(seconds) with the media duration, or None if unknown."""
    binary = find_executable("ffprobe")
    if not binary:
        callback(None)
        return

    cmd = [
        binary,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        input_path,
    ]

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
