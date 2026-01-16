import os


def build_output_path(input_path, target_extension):
    base, _ = os.path.splitext(input_path)
    candidate = f"{base}.{target_extension}"
    if not os.path.exists(candidate):
        return candidate

    counter = 1
    while True:
        candidate = f"{base}-{counter}.{target_extension}"
        if not os.path.exists(candidate):
            return candidate
        counter += 1


def build_suffixed_output_path(input_path, suffix):
    base, ext = os.path.splitext(input_path)
    candidate = f"{base}-{suffix}{ext}"
    if not os.path.exists(candidate):
        return candidate

    counter = 1
    while True:
        candidate = f"{base}-{suffix}-{counter}{ext}"
        if not os.path.exists(candidate):
            return candidate
        counter += 1
