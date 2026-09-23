import os

from gi.repository import Nautilus  # type: ignore

from nautilus_file_converter import jobs, notify, registry
from nautilus_file_converter.converters.base import Action, Submenu


_MENU_PREFIX = "NautilusFileConverter"


def build_menu_items(file_infos):
    groups = []
    for converter in registry.get_converters():
        matching = [info for info in file_infos if converter.supports(info)]
        if matching:
            groups.append((converter, matching))

    if not groups:
        return []

    items = []
    for kind, label, getter in [
        ("convert", "Convert To", lambda c, infos: c.convert_items(infos)),
        ("tools", "Tools", lambda c, infos: c.tool_items(infos)),
    ]:
        sections = []
        for converter, matching in groups:
            children = getter(converter, matching)
            if children:
                sections.append((converter, matching, children))

        if not sections:
            continue

        top = Nautilus.MenuItem(name=f"{_MENU_PREFIX}::{kind}", label=label, tip="")
        submenu = Nautilus.Menu()

        if len(sections) == 1:
            converter, matching, children = sections[0]
            _append(submenu, f"{kind}-{converter.converter_id}", children, matching)
        else:
            # Mixed selection: one submenu per file kind, each acting only
            # on the files of that kind.
            for converter, matching, children in sections:
                path = f"{kind}-{converter.converter_id}"
                item = Nautilus.MenuItem(
                    name=f"{_MENU_PREFIX}::{path}",
                    label=f"{converter.label} ({len(matching)})",
                    tip="",
                )
                inner = Nautilus.Menu()
                _append(inner, path, children, matching)
                item.set_submenu(inner)
                submenu.append_item(item)

        top.set_submenu(submenu)
        items.append(top)

    return items


def _append(menu, path, nodes, file_infos):
    for node in nodes:
        node_path = f"{path}-{node.name}"
        item = Nautilus.MenuItem(
            name=f"{_MENU_PREFIX}::{node_path}",
            label=node.label,
            tip="",
        )

        if isinstance(node, Submenu):
            inner = Nautilus.Menu()
            _append(inner, node_path, node.children, file_infos)
            item.set_submenu(inner)
        elif isinstance(node, Action):
            item.connect("activate", _on_activate, node, file_infos)

        menu.append_item(item)


def _on_activate(_menu_item, action, file_infos):
    paths = [path for path in map(_get_local_path, file_infos) if path]
    skipped = len(file_infos) - len(paths)
    if skipped:
        notify.notify_error(
            f"{action.done}: skipped {skipped} file(s)",
            "Only local files can be converted.",
        )
    jobs.run(action, paths)


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
