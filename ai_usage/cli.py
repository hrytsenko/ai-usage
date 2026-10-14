"""Helpers for invoking agent CLIs, shared by the collectors."""

import shutil
import subprocess

TIMEOUT = 120  # seconds per CLI call
DETECT_TIMEOUT = 30  # seconds for a login status check


def find(name):
    """Return the CLI's path, or None if it's not on PATH."""
    # Windows: also finds .exe/.cmd shims, e.g. npm's codex.cmd.
    return shutil.which(name)


def resolve(name):
    """Return the CLI's path, raising if it's not on PATH."""
    path = find(name)
    if not path:
        raise RuntimeError(f"'{name}' not found on PATH")
    return path


def run(name, *args, timeout=TIMEOUT, check=False):
    """Run `<name> <args>` and return the CompletedProcess; with check, raise on a non-zero exit."""
    # Windows: args go straight to CreateProcess, so Git Bash can't rewrite "/usage" into a path.
    proc = subprocess.run(
        [resolve(name), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        stdin=subprocess.DEVNULL, timeout=timeout, check=False,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(f"{name} exited {proc.returncode}: {(proc.stderr or proc.stdout).strip()}")
    return proc
