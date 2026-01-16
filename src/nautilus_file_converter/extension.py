import gi

try:
    gi.require_version("Nautilus", "4.1")
    NAUTILUS_VERSION = "4.1"
except (ValueError, AttributeError):
    try:
        gi.require_version("Nautilus", "4.0")
        NAUTILUS_VERSION = "4.0"
    except (ValueError, AttributeError):
        try:
            gi.require_version("Nautilus", "3.0")
            NAUTILUS_VERSION = "3.0"
        except (ValueError, AttributeError):
            NAUTILUS_VERSION = "unknown"

from gi.repository import GObject, Nautilus # type: ignore

from nautilus_file_converter import menu


class NautilusFileConverterExtension(GObject.GObject, Nautilus.MenuProvider):
    def get_file_items(self, *args):
        if len(args) == 1:
            files = args[0]
        elif len(args) == 2:
            window, files = args
        else:
            return []

        if not files:
            return []
        return menu.build_menu_items(files)
