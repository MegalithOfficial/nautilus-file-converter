import os


# Paths are reserved by creating an empty file right away. Without that,
# converting a.png and a.jpg to WebP at once would pick a.webp for both.


def reserve_output_path(input_path, extension=None, suffix=None):
    """
    Reserve a free path next to input_path.

    extension replaces the input extension (None keeps it), suffix is
    appended to the base name: photo.jpg -> photo-50pct.jpg.
    """
    base, input_ext = os.path.splitext(input_path)
    ext = f".{extension}" if extension else input_ext
    stem = f"{base}-{suffix}" if suffix else base
    return _reserve(stem, ext)


def discard(path):
    """Remove a reserved path after its job failed or was cancelled."""
    try:
        os.remove(path)
    except OSError:
        pass


def _reserve(stem, ext):
    candidate = f"{stem}{ext}"
    counter = 0
    while True:
        try:
            fd = os.open(candidate, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            counter += 1
            candidate = f"{stem}-{counter}{ext}"
            continue
        os.close(fd)
        return candidate
