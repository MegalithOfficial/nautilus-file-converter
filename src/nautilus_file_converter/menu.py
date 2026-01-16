import os

from gi.repository import Nautilus # type: ignore

from nautilus_file_converter import commands, notify, output, registry


_MENU_PREFIX = "NautilusFileConverter"


def build_menu_items(file_infos):
    converters = registry.get_converters()
    eligible = [
        converter
        for converter in converters
        if any(converter.supports(info) for info in file_infos)
    ]
    has_images = any(_is_image(info) for info in file_infos)
    if not eligible and not has_images:
        return []

    items = []
    top_item = Nautilus.MenuItem(
        name=f"{_MENU_PREFIX}::ConvertTo",
        label="Convert To",
        tip="Convert selected files",
    )
    top_menu = Nautilus.Menu()

    for converter in eligible:
        converter_item = Nautilus.MenuItem(
            name=f"{_MENU_PREFIX}::{converter.converter_id}",
            label=converter.label,
            tip=f"Convert files using {converter.label}",
        )
        converter_menu = Nautilus.Menu()

        format_groups = _group_targets_by_format(converter.targets)

        for format_name, targets in format_groups.items():
            if len(targets) == 1:
                target = targets[0]
                target_item = Nautilus.MenuItem(
                    name=f"{_MENU_PREFIX}::{converter.converter_id}-{target.name}",
                    label=target.label,
                    tip=f"Convert to {target.label}",
                )
                target_item.connect(
                    "activate",
                    _on_convert_activate,
                    converter,
                    target,
                    file_infos,
                )
                converter_menu.append_item(target_item)
            else:
                format_item = Nautilus.MenuItem(
                    name=f"{_MENU_PREFIX}::{converter.converter_id}-{format_name}",
                    label=targets[0].label.split(" (")[0],
                    tip=f"Convert to {format_name.upper()}",
                )
                format_submenu = Nautilus.Menu()

                for target in targets:
                    quality_item = Nautilus.MenuItem(
                        name=f"{_MENU_PREFIX}::{converter.converter_id}-{target.name}",
                        label=target.label.split(" (")[1].rstrip(")") if " (" in target.label else target.label,
                        tip=f"Convert to {target.label}",
                    )
                    quality_item.connect(
                        "activate",
                        _on_convert_activate,
                        converter,
                        target,
                        file_infos,
                    )
                    format_submenu.append_item(quality_item)

                format_item.set_submenu(format_submenu)
                converter_menu.append_item(format_item)

        converter_item.set_submenu(converter_menu)
        top_menu.append_item(converter_item)

    top_item.set_submenu(top_menu)
    if eligible:
        items.append(top_item)

    if has_images:
        strip_item = Nautilus.MenuItem(
            name=f"{_MENU_PREFIX}::StripMetadata",
            label="Strip Metadata",
            tip="Remove metadata from selected images",
        )
        strip_item.connect("activate", _on_strip_metadata_activate, file_infos)
        items.append(strip_item)

    return items


def _group_targets_by_format(targets):
    """Group conversion targets by their base format (extension)."""
    groups = {}
    for target in targets:
        base_format = target.extension
        if base_format not in groups:
            groups[base_format] = []
        groups[base_format].append(target)
    return groups


def _on_convert_activate(menu_item, converter, target, file_infos):
    for info in file_infos:
        if converter.supports(info):
            converter.request_convert(info, target)


def _on_strip_metadata_activate(menu_item, file_infos):
    for info in file_infos:
        if not _is_image(info):
            continue

        input_path = _get_local_path(info)
        if not input_path:
            notify.notify_error("Metadata strip failed", "Selected file is not local")
            continue

        output_path = output.build_suffixed_output_path(input_path, "stripped")
        cmd = commands.build_magick_strip_command(input_path, output_path)
        if not cmd:
            notify.notify_error(
                "Metadata strip failed",
                "ImageMagick not found. Install magick or convert.",
            )
            return

        def _on_success(input_path=input_path, output_path=output_path):
            notify.notify_success(
                "Metadata stripped",
                _format_paths(input_path, output_path),
            )

        def _on_error(result):
            message = result.stderr.strip() if result.stderr else "Metadata stripping failed"
            notify.notify_error("Metadata strip failed", message)

        commands.run_command_async(cmd, on_success=_on_success, on_error=_on_error)


def _format_paths(input_path, output_path):
    return f"{os.path.basename(input_path)} -> {os.path.basename(output_path)}"


def _is_image(file_info):
    if file_info.is_directory():
        return False

    mime_type = file_info.get_mime_type()
    return bool(mime_type and mime_type.startswith("image/"))


def _get_local_path(file_info):
    if file_info.is_directory():
        return None

    location = file_info.get_location()
    if not location:
        return None

    path = location.get_path()
    if not path or not os.path.exists(path):
        return None

    return path
