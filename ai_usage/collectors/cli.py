"""Helpers for invoking agent CLIs, shared by the collectors."""

import shutil
import subprocess
import threading
from contextlib import contextmanager

PROCESS_TIMEOUT = 30  # seconds per CLI process


def find(name):
    """Return the CLI's path, or None if it's not found."""
    # Windows: also finds .exe/.cmd shims, e.g. npm's codex.cmd.
    return shutil.which(name)


def run(name, *args, timeout=PROCESS_TIMEOUT, check=False):
    """Run `<name> <args>` and return the CompletedProcess; with check, raise on a non-zero exit."""
    # Windows: args go straight to CreateProcess, so Git Bash can't rewrite "/usage" into a path.
    proc = subprocess.run(
        [_resolve(name), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        stdin=subprocess.DEVNULL, timeout=timeout, check=False,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(f"{name} exited {proc.returncode}: {(proc.stderr or proc.stdout).strip()}")
    return proc


@contextmanager
def start(name, *args, timeout=PROCESS_TIMEOUT):
    """Start `<name> <args>` with piped stdin and stdout, and yield the Popen; it's killed on exit or after timeout."""
    # Exiting the Popen closes its pipes and waits for the process.
    with subprocess.Popen(
        [_resolve(name), *args],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        text=True, encoding="utf-8", errors="replace",
    ) as proc:
        # A timeout kill closes stdout, so a read waiting for an answer ends instead of hanging.
        timer = threading.Timer(timeout, proc.kill)
        timer.start()
        try:
            yield proc
        finally:
            timer.cancel()
            proc.kill()


def _resolve(name):
    """Return the CLI's path, raising if it's not found."""
    path = find(name)
    if not path:
        raise RuntimeError(f"'{name}' not found")
    return path
