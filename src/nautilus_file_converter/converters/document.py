import os

from gi.repository import GLib  # type: ignore

from nautilus_file_converter import commands
from nautilus_file_converter.converters.base import Action, BaseConverter, file_extension


# (family, input extensions, [(output extension, label)])
_FAMILIES = [
    (
        "text",
        {"doc", "docx", "odt", "rtf", "txt", "fodt", "wpd", "pages"},
        [("pdf", "PDF"), ("docx", "Word (DOCX)"), ("odt", "OpenDocument (ODT)"), ("rtf", "RTF"), ("txt", "Plain Text")],
    ),
    (
        "sheet",
        {"xls", "xlsx", "ods", "csv", "fods", "numbers"},
        [("pdf", "PDF"), ("xlsx", "Excel (XLSX)"), ("ods", "OpenDocument (ODS)"), ("csv", "CSV (first sheet)")],
    ),
    (
        "slides",
        {"ppt", "pptx", "odp", "fodp", "key"},
        [("pdf", "PDF"), ("pptx", "PowerPoint (PPTX)"), ("odp", "OpenDocument (ODP)")],
    ),
]

# LibreOffice picks the export filter from the extension, except for these.
_FILTERS = {"txt": "txt:Text (encoded):UTF8"}


class DocumentConverter(BaseConverter):
    converter_id = "document"
    label = "Document"

    def available(self):
        return commands.has_executable("soffice", "libreoffice")

    def supports(self, file_info) -> bool:
        if file_info.is_directory():
            return False
        return _family(file_extension(file_info)) is not None

    def convert_items(self, file_infos):
        families = {_family(file_extension(info)) for info in file_infos}
        families.discard(None)
        extensions = {file_extension(info) for info in file_infos}
        current = extensions.pop() if len(extensions) == 1 else None

        # Only offer targets every selected family can produce.
        targets = None
        for family in families:
            family_targets = _targets(family)
            if targets is None:
                targets = family_targets
            else:
                targets = [target for target in targets if target in family_targets]

        return [
            _convert_action(ext, label)
            for ext, label in targets or []
            if ext != current
        ]


def _family(extension):
    for name, extensions, _targets_ in _FAMILIES:
        if extension in extensions:
            return name
    return None


def _targets(family):
    for name, _extensions, targets in _FAMILIES:
        if name == family:
            return targets
    return []


def _profile_url():
    # A private profile keeps us away from a running LibreOffice window,
    # which would otherwise swallow the job or block on its lock file.
    path = os.path.join(GLib.get_user_cache_dir(), "nautilus-file-converter", "libreoffice")
    return GLib.filename_to_uri(path, None)


def _convert_action(ext, label):
    def build(input_path, _output_path, workdir):
        return [
            commands.find_executable("soffice", "libreoffice"),
            f"-env:UserInstallation={_profile_url()}",
            "--headless",
            "--norestore",
            "--convert-to", _FILTERS.get(ext, ext),
            "--outdir", workdir,
            input_path,
        ]

    return Action(
        f"to-{ext}",
        label,
        build,
        f"Converted to {label}",
        extension=ext,
        queue="office",
        collect=True,
    )
