"""Table reporter."""

import os
import re
import sys
from datetime import datetime
from typing import ClassVar

from ..model import Failure, Status


class TableReporter:
    """Reports usages as a table."""

    class Levels:
        """Grades quotas by percent left: low below `low`, medium below `medium`."""

        EXHAUSTED, LOW, MEDIUM, HIGH = "exhausted", "low", "medium", "high"

        def __init__(self, low=15, medium=40):
            self.low = low
            self.medium = medium

        def of(self, quota):
            """Return the level of a quota."""
            if quota.left <= 0:
                return self.EXHAUSTED
            if quota.left < self.low:
                return self.LOW
            if quota.left < self.medium:
                return self.MEDIUM
            return self.HIGH

    class Resets:
        """Formats reset times in local time and relative to now; tz=None means the system time zone."""

        def __init__(self, now, tz=None):
            self.now = now
            self.tz = tz

        @classmethod
        def for_system(cls):
            """Create resets relative to now, in the system time zone."""
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
        """Paints text with ANSI colors when enabled."""

        GREEN, YELLOW, RED, GRAY, RESET = "\x1b[32m", "\x1b[33m", "\x1b[31m", "\x1b[90m", "\x1b[0m"
        ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

        def __init__(self, enabled):
            self.enabled = enabled

        @classmethod
        def for_stdout(cls):
            """Create colors enabled when stdout can show them, unless NO_COLOR is set."""
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

    WINDOWS = ("session", "week")  # usage attributes, in display order
    BAR_WIDTH = 20
    FAILED_STATUS = "error"  # the status shown for a Failure

    STATUS_COLORS: ClassVar = {Status.ABSENT: Colors.GRAY, Status.LOGGED_OUT: Colors.YELLOW}
    LEVEL_COLORS: ClassVar = {Levels.HIGH: Colors.GREEN, Levels.MEDIUM: Colors.YELLOW, Levels.LOW: Colors.RED, Levels.EXHAUSTED: Colors.RED}

    def __init__(self, colors, resets, levels=None):
        self.colors = colors
        self.resets = resets
        self.levels = levels or self.Levels()

    @classmethod
    def for_stdout(cls):
        """Create a reporter for stdout, with reset times in the system time zone."""
        return cls(cls.Colors.for_stdout(), cls.Resets.for_system())

    def report(self, usages):
        """Report usages as a table."""
        rows = [("AGENT", "STATUS", "WINDOW", "QUOTA", "LEFT", "LEVEL", "RESET")]
        for u in usages:
            if isinstance(u, Failure):
                rows.append((u.name, self.colors.paint(self.FAILED_STATUS, self.Colors.RED), u.reason))
                continue
            agent = u.agent
            status = self.colors.paint(agent.status, self.STATUS_COLORS.get(agent.status))
            if not agent.usable:
                rows.append((agent.name, status))
                continue
            for i, window in enumerate(self.WINDOWS):
                quota = getattr(u, window)
                lead = (agent.name, status) if i == 0 else ("", "")
                if quota is None:
                    rows.append((*lead, window, "", "-", "n/a", "-"))
                    continue
                level = self.levels.of(quota)
                color = self.LEVEL_COLORS[level]
                rows.append((*lead, window, self.colors.paint(self._bar(quota), color),
                             self.colors.paint(f"{quota.left}%", color), self.colors.paint(level, color),
                             self.resets.format(quota.reset)))
        self._print_rows(rows, right_aligned={4})  # LEFT

    def _bar(self, quota):
        left = round(quota.left / 100 * self.BAR_WIDTH)
        return "█" * left + "░" * (self.BAR_WIDTH - left)

    def _print_rows(self, rows, right_aligned=()):
        """Print rows as aligned columns. A row may have fewer cells; its last cell is never padded."""
        def visible_len(text):
            return len(self.Colors.strip(text))

        widths = [max((visible_len(r[i]) for r in rows if i < len(r) - 1), default=0) for i in range(max(map(len, rows)))]
        for row in rows:
            cells = []
            for i, c in enumerate(row[:-1]):
                gap = " " * (widths[i] - visible_len(c))
                cells.append(gap + c if i in right_aligned else c + gap)
            print("  ".join([*cells, row[-1]]))
