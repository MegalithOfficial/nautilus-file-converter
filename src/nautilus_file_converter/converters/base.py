import os
from typing import Any

from nautilus_file_converter import notify, output


class ConversionTarget:
    def __init__(self, name, label, extension, quality=85):
        self.name = name
        self.label = label
        self.extension = extension
        self.quality = quality


class BaseConverter:
    converter_id = "base"
    label = "Base"
    targets = []

    def supports(self, file_info: Any) -> bool:
        return False

    def convert(
        self, input_path: str, output_path: str, target: ConversionTarget
    ) -> None:
        raise NotImplementedError

    def request_convert(self, file_info: Any, target: ConversionTarget) -> None:
        input_path = _get_local_path(file_info)
        if not input_path:
            notify.notify_error("Conversion failed", "Selected file is not local")
            return

        output_path = output.build_output_path(input_path, target.extension)
        self.convert(input_path, output_path, target)

    def get_quality_variants(self, base_target: ConversionTarget):
        """Generate quality variants for formats that benefit from it."""
        if base_target.extension in ['jpg', 'jpeg', 'webp', 'avif']:
            return [
                ConversionTarget(
                    f"{base_target.name}_high",
                    f"{base_target.label} (High Quality)",
                    base_target.extension,
                    quality=95
                ),
                ConversionTarget(
                    f"{base_target.name}_medium",
                    f"{base_target.label} (Balanced)",
                    base_target.extension,
                    quality=85
                ),
                ConversionTarget(
                    f"{base_target.name}_low",
                    f"{base_target.label} (Fast/Small)",
                    base_target.extension,
                    quality=70
                ),
            ]
        return [base_target]


def _get_local_path(file_info: Any):
    if file_info.is_directory():
        return None

    location = file_info.get_location()
    if not location:
        return None

    path = location.get_path()
    if not path or not os.path.exists(path):
        return None

    return path
