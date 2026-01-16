import shutil
import subprocess
import threading


def find_executable(candidates):
    for candidate in candidates:
        if shutil.which(candidate):
            return candidate
    return None


def build_magick_command(input_path, output_path, quality=85):
    """
    Build an optimized ImageMagick command for fast conversions.

    Args:
        input_path: Source image path
        output_path: Destination image path
        quality: JPEG/WebP quality (1-100, default 85 for good balance)

    Returns:
        Command array or None if ImageMagick not found
    """
    binary = find_executable(["magick", "convert"])
    if not binary:
        return None

    cmd = [binary, input_path]

    cmd.extend([
        "-quality", str(quality),
    ])

    ext = output_path.lower().split('.')[-1]

    if ext in ['jpg', 'jpeg']:
        cmd.extend(["-interlace", "Plane"])
    elif ext == 'png':
        cmd.extend(["-define", "png:compression-level=6"])
    elif ext == 'webp':
        cmd.extend(["-define", "webp:method=4"])
    elif ext == 'avif':
        # AVIF optimizations
        cmd.extend(["-define", "avif:speed=6"])

    cmd.append(output_path)
    return cmd


def build_magick_strip_command(input_path, output_path):
    """
    Build an ImageMagick command to strip metadata from an image.

    Args:
        input_path: Source image path
        output_path: Destination image path

    Returns:
        Command array or None if ImageMagick not found
    """
    binary = find_executable(["magick", "convert"])
    if not binary:
        return None

    return [binary, input_path, "-strip", output_path]


def run_command_async(args, on_success=None, on_error=None):
    def _run():
        result = subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            _run_callback(on_success)
        else:
            _run_callback(on_error, result)

    threading.Thread(target=_run, daemon=True).start()


def _run_callback(callback, *args):
    if not callback:
        return

    try:
        from gi.repository import GLib # type: ignore
    except Exception:
        callback(*args)
        return

    GLib.idle_add(callback, *args)
