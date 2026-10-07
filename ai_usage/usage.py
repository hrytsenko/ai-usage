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

WINDOWS = ["session", "week"]  # Result attributes, in display order

BAR_WIDTH = 20
PARTIAL_BLOCKS = " ▏▎▍▌▋▊▉"  # index = eighths of a cell filled
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
GREEN, YELLOW, RED, GRAY, RESET = "\x1b[32m", "\x1b[33m", "\x1b[31m", "\x1b[90m", "\x1b[0m"
LEVEL_COLORS = {Level.HIGH: GREEN, Level.MEDIUM: YELLOW, Level.LOW: RED, Level.EXHAUSTED: RED}
STATUS_COLORS = {Status.ABSENT: GRAY, Status.LOGGED_OUT: YELLOW, Status.ERROR: RED}


def fmt_reset(dt):
    """Format a reset time in local time, e.g. `Tue Oct 06 19:50 (in 2h 59m)`."""
    if dt is None:
        return "-"
    dt = dt.astimezone()
    delta = dt - datetime.now().astimezone()
    mins = max(0, int(delta.total_seconds() // 60))
    days, rem = divmod(mins, 24 * 60)
    hours, mins = divmod(rem, 60)
    relative = f"{days}d {hours}h" if days else f"{hours}h {mins:02d}m"
    return f"{dt:%a %b %d %H:%M} (in {relative})"


def enable_color():
    """Return True when stdout is a terminal that can show ANSI colors (honours NO_COLOR)."""
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


def paint(text, code, use_color):
    return f"{code}{text}{RESET}" if use_color and code else text


def fmt_bar(quota, use_color):
    """A bar of the percent left, e.g. `██████████████▌░░░░░`, colored by level."""
    full, part = divmod(round(quota.left / 100 * BAR_WIDTH * 8), 8)
    filled = "█" * full + (PARTIAL_BLOCKS[part] if part else "")
    track = "░" * (BAR_WIDTH - len(filled))
    return f"{paint(filled, LEVEL_COLORS[quota.level], use_color)}{paint(track, GRAY, use_color)}"


def visible_len(text):
    return len(ANSI_RE.sub("", text))


def print_rows(rows, right_aligned=()):
    """Print rows as aligned columns. A row may have fewer cells; its last cell is never padded."""
    widths = [max((visible_len(r[i]) for r in rows if i < len(r) - 1), default=0) for i in range(max(map(len, rows)))]
    for row in rows:
        cells = []
        for i, c in enumerate(row[:-1]):
            gap = " " * (widths[i] - visible_len(c))
            cells.append(gap + c if i in right_aligned else c + gap)
        print("  ".join([*cells, row[-1]]))


def print_table(results, use_color):
    rows = [("AGENT", "STATUS", "WINDOW", "QUOTA", "LEFT", "LEVEL", "RESET")]
    for r in results:
        agent = r.agent
        status = paint(agent.status, STATUS_COLORS.get(agent.status), use_color)
        if not agent.status.usable:
            rows.append((agent.name, status, agent.error) if agent.error else (agent.name, status))
            continue
        for i, window in enumerate(WINDOWS):
            quota = getattr(r, window)
            lead = (agent.name, status) if i == 0 else ("", "")
            if quota is None:
                rows.append((*lead, window, "", "-", "n/a", "-"))
                continue
            code = LEVEL_COLORS[quota.level]
            rows.append((*lead, window, fmt_bar(quota, use_color), paint(f"{quota.left}%", code, use_color),
                         paint(quota.level, code, use_color), fmt_reset(quota.reset)))
    print_rows(rows, right_aligned={4})  # LEFT


def to_json(results):
    def quota_json(q):
        if q is None:
            return None
        return {"level": q.level, "left": q.left, "reset": q.reset.isoformat() if q.reset else None}

    out = {}
    for r in results:
        entry = {"status": r.agent.status}
        if r.agent.error:
            entry["error"] = r.agent.error
        if r.agent.status.usable:
            entry.update(session=quota_json(r.session), week=quota_json(r.week))
        out[r.agent.name] = entry
    return json.dumps(out, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(prog="ai-usage", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", action="store_true", help="print structured JSON")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args()

    # Windows consoles may default to a legacy codepage that can't print the bar characters.
    sys.stdout.reconfigure(encoding="utf-8")

    with ThreadPoolExecutor(len(COLLECTORS)) as pool:
        results = list(pool.map(lambda c: c.collect(), COLLECTORS))

    if args.json:
        print(to_json(results))
    else:
        print_table(results, enable_color())

    ok = any(r.agent.status.usable for r in results)
    failed = any(r.agent.status is Status.ERROR for r in results)
    sys.exit(0 if ok and not failed else 1)

