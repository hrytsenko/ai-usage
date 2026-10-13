"""The table printed by `ai-usage`."""

import contextlib
import io
import unittest
from datetime import datetime, timedelta, timezone
from functools import partial

from ai_usage.collectors import Agent, Quota, Result, Status
from ai_usage.usage import ANSI_RE, format_ansi, format_plain, format_reset, print_table

# Local time for the test. Fixed, so the output doesn't depend on the machine's time zone.
LOCAL = timezone(timedelta(hours=3))

# When the README example was taken: each reset below is that far ahead, rounded down to the minute.
NOW = datetime(2026, 10, 6, 16, 50, 30, tzinfo=LOCAL)


def reset_at(day, hour, minute):
    """A reset on that day of October 2026, in local time."""
    return datetime(2026, 10, day, hour, minute, tzinfo=LOCAL)


# The example in the README.
RESULTS = [
    Result(
        Agent("Claude Code", Status.LOGGED_IN),
        session=Quota(73, reset_at(6, 19, 50)),
        week=Quota(12, reset_at(9, 16, 50)),
    ),
    Result(
        Agent("Codex", Status.LOGGED_IN),
        session=Quota(30, reset_at(6, 17, 50)),
        week=Quota(98, reset_at(10, 11, 4)),
    ),
    Result(Agent("Antigravity", Status.ABSENT)),
]

TABLE = """\
AGENT        STATUS     WINDOW   QUOTA                 LEFT  LEVEL   RESET
Claude Code  logged in  session  ███████████████░░░░░   73%  high    Tue Oct 06 19:50 (in 2h 59m)
                        week     ██░░░░░░░░░░░░░░░░░░   12%  low     Fri Oct 09 16:50 (in 2d 23h)
Codex        logged in  session  ██████░░░░░░░░░░░░░░   30%  medium  Tue Oct 06 17:50 (in 0h 59m)
                        week     ████████████████████   98%  high    Sat Oct 10 11:04 (in 3d 18h)
Antigravity  absent
"""


def render(format_color):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        print_table(RESULTS, format_color, partial(format_reset, now=NOW, tz=LOCAL))
    return out.getvalue()


class PrintTableTest(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(render(format_plain), TABLE)

    def test_colors_dont_shift_columns(self):
        colored = render(format_ansi)

        self.assertIn("\x1b[", colored)
        self.assertEqual(ANSI_RE.sub("", colored), TABLE)


if __name__ == "__main__":
    unittest.main()
