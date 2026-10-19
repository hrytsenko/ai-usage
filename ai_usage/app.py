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
from .collectors import COLLECTORS, Failure, Status

WINDOWS = ["session", "week"]  # Usage attributes, in display order

BAR_WIDTH = 20

FAILED = "error"  # the status shown for a Failure


class Levels:
    """How much of a quota is left: low below `low` percent left, medium below `medium`."""

    EXHAUSTED, LOW, MEDIUM, HIGH = "exhausted", "low", "medium", "high"

    def __init__(self, low=15, medium=40):
        self.low = low
        self.medium = medium

    def of(self, quota):
        """The level of a quota by percent left."""
        if quota.left <= 0:
            return self.EXHAUSTED
        if quota.left < self.low:
            return self.LOW
        if quota.left < self.medium:
            return self.MEDIUM
        return self.HIGH


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
        """Enable colors when stdout is a terminal that can show ANSI colors (honour NO_COLOR)."""
        if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
            return cls(False)
        if os.name == "nt":
            # Turn on ENABLE_VIRTUAL_TERMINAL_PROCESSING; Windows Terminal has it on already, classic conhost doesn't.
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = ctypes.c_uint32()
            if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                return cls(False)
            return cls(bool(kernel32.SetConsoleMode(handle, mode.value | 0x0004)))
        return cls(True)

    @classmethod
    def strip(cls, text):
        """Remove ANSI color codes."""
        return cls.ANSI_RE.sub("", text)

    def paint(self, text, color):
        """Add ANSI color codes when enabled."""
        return f"{color}{text}{self.RESET}" if self.enabled and color else text


STATUS_COLORS = {Status.ABSENT: Colors.GRAY, Status.LOGGED_OUT: Colors.YELLOW}
LEVEL_COLORS = {Levels.HIGH: Colors.GREEN, Levels.MEDIUM: Colors.YELLOW, Levels.LOW: Colors.RED, Levels.EXHAUSTED: Colors.RED}


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


def print_table(usages, levels, colors, resets):
    """Print usages as a table, with quotas leveled by levels, cells painted by colors and reset times formatted by resets."""
    def format_bar(quota):
        left = round(quota.left / 100 * BAR_WIDTH)
        return "█" * left + "░" * (BAR_WIDTH - left)

    rows = [("AGENT", "STATUS", "WINDOW", "QUOTA", "LEFT", "LEVEL", "RESET")]
    for u in usages:
        if isinstance(u, Failure):
            rows.append((u.name, colors.paint(FAILED, Colors.RED), u.reason))
            continue
        agent = u.agent
        status = colors.paint(agent.status, STATUS_COLORS.get(agent.status))
        if not agent.usable:
            rows.append((agent.name, status))
            continue
        for i, window in enumerate(WINDOWS):
            quota = getattr(u, window)
            lead = (agent.name, status) if i == 0 else ("", "")
            if quota is None:
                rows.append((*lead, window, "", "-", "n/a", "-"))
                continue
            level = levels.of(quota)
            color = LEVEL_COLORS[level]
            rows.append((*lead, window, colors.paint(format_bar(quota), color), colors.paint(f"{quota.left}%", color),
                         colors.paint(level, color), resets.format(quota.reset)))
    print_rows(rows, right_aligned={4})  # LEFT


def print_json(usages, levels):
    def quota_json(q):
        if q is None:
            return None
        return {"level": levels.of(q), "left": q.left, "reset": q.reset.isoformat() if q.reset else None}

    out = {}
    for u in usages:
        if isinstance(u, Failure):
            out[u.name] = {"status": FAILED, "error": u.reason}
            continue
        entry = {"status": u.agent.status}
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

    levels = Levels()
    if args.json:
        print_json(usages, levels)
    else:
        print_table(usages, levels, Colors.for_stdout(), Resets.for_system())

    failed = any(isinstance(u, Failure) for u in usages)
    sys.exit(1 if failed else 0)

