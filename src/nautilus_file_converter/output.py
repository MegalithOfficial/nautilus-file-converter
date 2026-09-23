import os


# Paths are reserved by creating an empty file right away. Without that,
# converting a.png and a.jpg to WebP at once would pick a.webp for both.


def build_output_path(input_path, target_extension):
    base, _ = os.path.splitext(input_path)
    return _reserve(f"{base}", f".{target_extension}")


def build_suffixed_output_path(input_path, suffix):
    base, ext = os.path.splitext(input_path)
    return _reserve(f"{base}-{suffix}", ext)


def discard(path):
    """Remove a reserved path that a failed conversion left empty."""
    try:
        if os.path.getsize(path) == 0:
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
