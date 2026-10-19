"""Show session and weekly quotas for the Claude Code, Codex and Antigravity (agy) CLIs.

Checks each agent and reads quotas only from those that are installed and logged in.

Usage:
    ai-usage           # table
    ai-usage --json    # structured output
"""

import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from . import __version__
from .collectors import COLLECTORS, Level, Status

WINDOWS = ["session", "week"]  # Usage attributes, in display order

BAR_WIDTH = 20


class Resets:
    """Reset times in local time and relative to now; tz=None means the system time zone."""

    def __init__(self, now, tz=None):
        self.now = now
        self.tz = tz

    @classmethod
    def for_system(cls):
        """Relative to the current time, in the system time zone."""
        return cls(datetime.now().astimezone())

    def format(self, dt):
        """Format a reset time, e.g. `Tue Oct 06 19:50 (in 2h 59m)`."""
        if dt is None:
            return "-"
        dt = dt.astimezone(self.tz)
        mins = max(0, int((dt - self.now).total_seconds() // 60))
        days, rem = divmod(mins, 24 * 60)
        hours, mins = divmod(rem, 60)
        relative = f"{days}d {hours}h" if days else f"{hours}h {mins:02d}m"
        return f"{dt:%a %b %d %H:%M} (in {relative})"


class Colors:
    """ANSI colors for terminal text; when disabled, text stays plain."""

    GREEN, YELLOW, RED, GRAY, RESET = "\x1b[32m", "\x1b[33m", "\x1b[31m", "\x1b[90m", "\x1b[0m"
    ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

    def __init__(self, enabled):
        self.enabled = enabled

    @classmethod
    def for_stdout(cls):
        """Enabled when stdout is a terminal that can show ANSI colors (honours NO_COLOR)."""
        return cls(cls._stdout_supports_ansi())

    @staticmethod
    def _stdout_supports_ansi():
        if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
            return False
        if os.name == "nt":
            # Turn on ENABLE_VIRTUAL_TERMINAL_PROCESSING; Windows Terminal has it on already, classic conhost doesn't.
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = ctypes.c_uint32()
            if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                return False
            return bool(kernel32.SetConsoleMode(handle, mode.value | 0x0004))
        return True

    @classmethod
    def strip(cls, text):
        """Remove ANSI color codes, leaving the text as it shows on screen."""
        return cls.ANSI_RE.sub("", text)

    def paint(self, text, color):
        return f"{color}{text}{self.RESET}" if self.enabled and color else text


LEVEL_COLORS = {Level.HIGH: Colors.GREEN, Level.MEDIUM: Colors.YELLOW, Level.LOW: Colors.RED, Level.EXHAUSTED: Colors.RED}
STATUS_COLORS = {Status.ABSENT: Colors.GRAY, Status.LOGGED_OUT: Colors.YELLOW, Status.ERROR: Colors.RED}


def format_bar(quota, colors):
    """Format a bar of the percent left, e.g. `███████████████░░░░░`, colored by level."""
    left = round(quota.left / 100 * BAR_WIDTH)
    return colors.paint("█" * left + "░" * (BAR_WIDTH - left), LEVEL_COLORS[quota.level])


def print_rows(rows, right_aligned=()):
    """Print rows as aligned columns. A row may have fewer cells; its last cell is never padded."""
    def visible_len(text):
        return len(Colors.strip(text))

    widths = [max((visible_len(r[i]) for r in rows if i < len(r) - 1), default=0) for i in range(max(map(len, rows)))]
    for row in rows:
        cells = []
        for i, c in enumerate(row[:-1]):
            gap = " " * (widths[i] - visible_len(c))
            cells.append(gap + c if i in right_aligned else c + gap)
        print("  ".join([*cells, row[-1]]))


def print_table(usages, colors, resets):
    """Print usages as a table, with cells painted by colors and reset times formatted by resets."""
    rows = [("AGENT", "STATUS", "WINDOW", "QUOTA", "LEFT", "LEVEL", "RESET")]
    for u in usages:
        agent = u.agent
        status = colors.paint(agent.status, STATUS_COLORS.get(agent.status))
        if not agent.usable:
            rows.append((agent.name, status, u.error) if u.error else (agent.name, status))
            continue
        for i, window in enumerate(WINDOWS):
            quota = getattr(u, window)
            lead = (agent.name, status) if i == 0 else ("", "")
            if quota is None:
                rows.append((*lead, window, "", "-", "n/a", "-"))
                continue
            color = LEVEL_COLORS[quota.level]
            rows.append((*lead, window, format_bar(quota, colors), colors.paint(f"{quota.left}%", color),
                         colors.paint(quota.level, color), resets.format(quota.reset)))
    print_rows(rows, right_aligned={4})  # LEFT


def print_json(usages):
    def quota_json(q):
        if q is None:
            return None
        return {"level": q.level, "left": q.left, "reset": q.reset.isoformat() if q.reset else None}

    out = {}
    for u in usages:
        entry = {"status": u.agent.status}
        if u.error:
            entry["error"] = u.error
        if u.agent.usable:
            entry.update(session=quota_json(u.session), week=quota_json(u.week))
        out[u.agent.name] = entry
    print(json.dumps(out, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(prog="ai-usage", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", action="store_true", help="print structured JSON")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args()

    # Windows consoles may default to a legacy codepage that can't print the bar characters.
    sys.stdout.reconfigure(encoding="utf-8")

    with ThreadPoolExecutor(len(COLLECTORS)) as pool:
        usages = list(pool.map(lambda c: c.collect(), COLLECTORS))

    if args.json:
        print_json(usages)
    else:
        print_table(usages, Colors.for_stdout(), Resets.for_system())

    ok = any(u.agent.usable for u in usages)
    failed = any(u.agent.status is Status.ERROR for u in usages)
    sys.exit(0 if ok and not failed else 1)

