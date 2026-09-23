import os
from typing import Any, Callable, List, Optional


PLAIN = "plain"
FFMPEG = "ffmpeg"


class Action:
    """
    A menu leaf that runs one command per selected file.

    build(input_path, output_path, workdir) returns the argv to run.
    extension is the output extension (None keeps the input one) and
    suffix is appended to the output name, e.g. photo-50pct.jpg.
    """

    def __init__(
        self,
        name: str,
        label: str,
        build: Callable,
        done: str,
        extension: Optional[str] = None,
        suffix: Optional[str] = None,
        runner: str = PLAIN,
        queue: str = "light",
        progress: bool = False,
        collect: bool = False,
        combine: bool = False,
    ):
        self.name = name
        self.label = label
        self.build = build
        self.done = done
        self.extension = extension
        self.suffix = suffix
        self.runner = runner
        self.queue = queue
        # Show a per-file progress window with a cancel button (ffmpeg only).
        self.progress = progress
        # The command writes into workdir and the single file found there
        # is moved to the output path afterwards (LibreOffice).
        self.collect = collect
        # One output from all selected files; build gets a list of inputs.
        self.combine = combine


class Submenu:
    def __init__(self, name: str, label: str, children: List[Any]):
        self.name = name
        self.label = label
        self.children = children


class BaseConverter:
    converter_id = "base"
    label = "Base"

    def available(self) -> bool:
        return True

    def supports(self, file_info: Any) -> bool:
        return False

    def convert_items(self, file_infos: List[Any]) -> List[Any]:
        return []

    def tool_items(self, file_infos: List[Any]) -> List[Any]:
        return []


def file_extension(file_info: Any) -> str:
    name = file_info.get_name() if hasattr(file_info, "get_name") else ""
    return os.path.splitext(name or "")[1].lstrip(".").lower()


def shared_extension(file_infos: List[Any], aliases=None) -> Optional[str]:
    """The extension all files share (after aliasing), or None if mixed."""
    aliases = aliases or {}
    extensions = {aliases.get(ext, ext) for ext in map(file_extension, file_infos)}
    return extensions.pop() if len(extensions) == 1 else None


def mime_type(file_info: Any) -> str:
    if file_info.is_directory():
        return ""
    return file_info.get_mime_type() or ""
