import shutil
import subprocess


def notify_success(title, body):
    _notify(title, body, urgency="normal")


def notify_error(title, body):
    _notify(title, body, urgency="critical")


def _notify(title, body, urgency=None):
    if not shutil.which("notify-send"):
        return

    args = ["notify-send"]
    if urgency:
        args.extend(["-u", urgency])
    args.extend([title, body])
    subprocess.run(args, check=False)

