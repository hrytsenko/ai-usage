"""The table printed by the app."""

import contextlib
import io
import unittest
from datetime import datetime, timedelta, timezone

from ai_usage.app import Colors, Resets, print_table
from ai_usage.collectors import Agent, Failure, Quota, Status, Usage

# The time zone and current time of the README example.
LOCAL = timezone(timedelta(hours=3))
# Seconds past the minute, so the relative reset times are rounded down, as in the README.
NOW = datetime(2026, 10, 6, 16, 50, 30, tzinfo=LOCAL)


def reset_at(day, hour, minute):
    """A reset on that day of October 2026, in local time."""
    return datetime(2026, 10, day, hour, minute, tzinfo=LOCAL)


# The example in the README.
USAGES = [
    Usage(
        Agent("Claude Code", Status.LOGGED_IN, usable=True),
        session=Quota(73, reset_at(6, 19, 50)),
        week=Quota(12, reset_at(9, 16, 50)),
    ),
    Usage(
        Agent("Codex", Status.LOGGED_IN, usable=True),
        session=Quota(30, reset_at(6, 17, 50)),
        week=Quota(98, reset_at(10, 11, 4)),
    ),
    Usage(Agent("Antigravity", Status.ABSENT, usable=False)),
]

TABLE = """\
AGENT        STATUS     WINDOW   QUOTA                 LEFT  LEVEL   RESET
Claude Code  logged in  session  ███████████████░░░░░   73%  high    Tue Oct 06 19:50 (in 2h 59m)
                        week     ██░░░░░░░░░░░░░░░░░░   12%  low     Fri Oct 09 16:50 (in 2d 23h)
Codex        logged in  session  ██████░░░░░░░░░░░░░░   30%  medium  Tue Oct 06 17:50 (in 0h 59m)
                        week     ████████████████████   98%  high    Sat Oct 10 11:04 (in 3d 18h)
Antigravity  absent
"""


def render(colors, usages=USAGES):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        print_table(usages, colors, Resets(NOW, LOCAL))
    return out.getvalue()


class PrintTableTest(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(render(Colors(enabled=False)), TABLE)

    def test_colored(self):
        colored = render(Colors(enabled=True))

        self.assertIn("\x1b[", colored)
        self.assertEqual(Colors.strip(colored), TABLE)

    def test_failure(self):
        table = render(Colors(enabled=False), [Failure("Codex", "fetch: timed out")])

        self.assertEqual(table.splitlines()[1], "Codex  error   fetch: timed out")


if __name__ == "__main__":
    unittest.main()
