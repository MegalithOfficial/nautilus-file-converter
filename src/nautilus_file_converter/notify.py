import shutil

from gi.repository import Gio, GLib  # type: ignore


_APP_NAME = "Nautilus File Converter"
_MAX_BODY = 400


def notify_success(title, body):
    _notify(title, body, urgency="normal")


def notify_error(title, body):
    _notify(title, body, urgency="critical")


def _notify(title, body, urgency):
    if not shutil.which("notify-send"):
        return

    if len(body) > _MAX_BODY:
        body = "..." + body[-_MAX_BODY:]

    _spawn(["notify-send", "-a", _APP_NAME, "-u", urgency, title, body])


def _spawn(args, flags=Gio.SubprocessFlags.NONE):
    try:
        return Gio.Subprocess.new(args, flags)
    except GLib.Error:
        return None


class Progress:
    """
    A zenity progress window fed through a pipe, or a no-op without zenity.

    on_cancel is called if the user closes the window or presses Cancel
    before close() is called.
    """

    def __init__(self, title, text, pulsate=False, on_cancel=None):
        self._proc = None
        self._stdin = None
        self._text = text
        self._closed = False
        self._on_cancel = on_cancel

        if not shutil.which("zenity"):
            return

        args = [
            "zenity", "--progress",
            "--title", title,
            "--text", text,
            "--auto-close",
            "--width", "360",
        ]
        if not on_cancel:
            args.append("--no-cancel")
        args.append("--pulsate" if pulsate else "--percentage=0")

        self._proc = _spawn(args, Gio.SubprocessFlags.STDIN_PIPE)
        if self._proc:
            self._stdin = self._proc.get_stdin_pipe()
            self._proc.wait_async(None, self._on_exit)

    def update(self, percent=None, text=None):
        if percent is not None:
            # 100 would trigger --auto-close before the job is really done.
            self._write(f"{min(99, int(percent))}\n")
        if text:
            # zenity replaces the whole label, so keep the original text on top.
            self._write(f"# {self._text}\\n{text}\n")

    def close(self):
        if self._closed:
            return

        self._closed = True
        self._write("100\n")
        if self._stdin:
            try:
                self._stdin.close(None)
            except GLib.Error:
                pass
            self._stdin = None
        if self._proc:
            self._proc.force_exit()
            self._proc = None

    def _on_exit(self, proc, result):
        try:
            proc.wait_finish(result)
        except GLib.Error:
            pass

        if self._closed:
            return

        self._closed = True
        self._stdin = None
        self._proc = None
        if self._on_cancel:
            self._on_cancel()

    def _write(self, text):
        if not self._stdin:
            return

        try:
            self._stdin.write_all(text.encode("utf-8"), None)
        except GLib.Error:
            self._stdin = None
