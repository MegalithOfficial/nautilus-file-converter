import collections
import os
import shutil
import tempfile

from gi.repository import GLib  # type: ignore

from nautilus_file_converter import commands, notify, output
from nautilus_file_converter.converters.base import FFMPEG


# Files selected together form one batch with a single summary notification.
# Batches of this size or more get a progress window with a cancel button.
_BATCH_PROGRESS_MIN = 3


class _Queue:
    """Runs at most `limit` jobs at a time, the rest wait their turn."""

    def __init__(self, limit):
        self.limit = limit
        self.running = 0
        self.waiting = collections.deque()

    def submit(self, start):
        self.waiting.append(start)
        self._pump()

    def _pump(self):
        while self.running < self.limit and self.waiting:
            start = self.waiting.popleft()
            self.running += 1
            start(self._finished)

    def _finished(self):
        self.running -= 1
        # Deferred so a job that fails instantly cannot recurse into _pump.
        GLib.idle_add(self._pump_idle)

    def _pump_idle(self):
        self._pump()
        return False


_QUEUES = {
    "light": _Queue(max(2, (os.cpu_count() or 4) // 2)),
    # ffmpeg already uses every core on its own.
    "heavy": _Queue(2),
    # LibreOffice jobs share one profile and must not overlap.
    "office": _Queue(1),
}


def run(action, input_paths):
    if not input_paths:
        return

    if action.combine:
        batch = _Batch(action, 1)
        _QUEUES[action.queue].submit(
            lambda finished: _start(action, input_paths, batch, finished)
        )
        return

    batch = _Batch(action, len(input_paths))
    for input_path in input_paths:
        _QUEUES[action.queue].submit(
            lambda finished, input_path=input_path: _start(action, input_path, batch, finished)
        )


class _Batch:
    def __init__(self, action, total):
        self.action = action
        self.total = total
        self.outputs = []
        self.failures = []
        self.cancelled = 0
        self.aborted = False
        self.progress = None
        # Cancel callbacks of the jobs that are running right now.
        self.running = set()

        if total >= _BATCH_PROGRESS_MIN and not action.progress:
            self.progress = notify.Progress(
                action.done,
                f"{total} files",
                on_cancel=self._abort,
            )

    def _abort(self):
        self.aborted = True
        for cancel in list(self.running):
            cancel()

    def succeeded(self, input_path, output_path):
        self.outputs.append((input_path, output_path))
        self._step()

    def failed(self, input_path, message):
        self.failures.append((input_path, message))
        self._step()

    def skipped(self):
        self.cancelled += 1
        self._step()

    def _step(self):
        finished = len(self.outputs) + len(self.failures) + self.cancelled
        if self.progress:
            self.progress.update(finished * 100 / self.total, f"{finished} / {self.total}")
        if finished == self.total:
            if self.progress:
                self.progress.close()
            self._report()

    def _report(self):
        done = self.action.done
        ok = len(self.outputs)

        if self.failures:
            name, message = self.failures[0]
            if self.total == 1:
                title = f"{done}: failed"
            else:
                title = f"{done}: {len(self.failures)} of {self.total} failed"
                if ok:
                    title += f", {ok} done"
            notify.notify_error(title, f"{name}\n{message}")
            return

        if ok == 1 and self.total == 1:
            input_path, output_path = self.outputs[0]
            if isinstance(input_path, list):
                body = f"{len(input_path)} files -> {os.path.basename(output_path)}"
            else:
                body = f"{os.path.basename(input_path)} -> {os.path.basename(output_path)}"
            notify.notify_success(done, body)
        elif ok:
            folder = os.path.dirname(self.outputs[0][1])
            body = f"{ok} files in {folder}"
            if self.cancelled:
                body += f", {self.cancelled} cancelled"
            notify.notify_success(done, body)


def _start(action, input_path, batch, finished):
    if batch.aborted:
        batch.skipped()
        finished()
        return

    first_input = input_path[0] if action.combine else input_path
    display_name = f"{len(input_path)} files" if action.combine else os.path.basename(input_path)
    try:
        output_path = output.reserve_output_path(first_input, action.extension, action.suffix)
    except OSError as exc:
        batch.failed(display_name, exc.strerror or str(exc))
        finished()
        return

    workdir = tempfile.mkdtemp(prefix="nautilus-file-converter-") if action.collect else None
    state = {"cancelled": False, "proc": None, "progress": None}

    def _cleanup():
        batch.running.discard(_cancel)
        if workdir:
            shutil.rmtree(workdir, ignore_errors=True)
        if state["progress"]:
            state["progress"].close()
        finished()

    def _on_success():
        if workdir:
            try:
                _collect(workdir, output_path)
            except OSError as exc:
                _on_error(str(exc))
                return
        _cleanup()
        batch.succeeded(input_path, output_path)

    def _on_error(message):
        output.discard(output_path)
        _cleanup()
        if state["cancelled"]:
            batch.skipped()
        else:
            batch.failed(display_name, message)

    def _cancel():
        state["cancelled"] = True
        if state["proc"]:
            state["proc"].force_exit()

    batch.running.add(_cancel)

    try:
        cmd = action.build(input_path, output_path, workdir)
    except Exception as exc:
        _on_error(f"Could not build command: {exc}")
        return

    if action.runner != FFMPEG:
        state["proc"] = commands.run_command_async(cmd, on_success=_on_success, on_error=_on_error)
        return

    def _launch(duration):
        if batch.aborted:
            _on_error("Cancelled")
            return

        on_progress = None
        if action.progress:
            state["progress"] = notify.Progress(
                action.done,
                f"{os.path.basename(first_input)} -> {os.path.basename(output_path)}",
                pulsate=duration is None,
                on_cancel=_cancel,
            )

            def on_progress(percent, elapsed):
                text = _format_time(elapsed)
                if duration:
                    text += f" / {_format_time(duration)}"
                state["progress"].update(percent, text)

        state["proc"] = commands.run_ffmpeg_async(
            cmd,
            duration,
            on_progress=on_progress,
            on_success=_on_success,
            on_error=_on_error,
        )

    if action.progress:
        commands.probe_duration_async(first_input, _launch)
    else:
        _launch(None)


def _collect(workdir, output_path):
    produced = [
        os.path.join(root, name)
        for root, _dirs, files in os.walk(workdir)
        for name in files
    ]
    if len(produced) != 1:
        raise OSError("The converter produced no output file")
    shutil.move(produced[0], output_path)


def _format_time(seconds):
    total_seconds = max(0, int(seconds))
    minutes, secs = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:d}:{secs:02d}"
