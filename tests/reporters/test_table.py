"""The table reported by TableReporter."""

import contextlib
import io
import unittest

from ai_usage.reporters import TableReporter

from .fixture_usages import FAILURE_EXAMPLE, LOCAL, NOW, USAGE_EXAMPLE

USAGE_TABLE = """\
AGENT        STATUS     WINDOW   QUOTA                 LEFT  LEVEL   RESET
Claude Code  logged in  session  ███████████████░░░░░   73%  high    Tue Oct 06 19:50 (in 2h 59m)
                        week     ██░░░░░░░░░░░░░░░░░░   12%  low     Fri Oct 09 16:50 (in 2d 23h)
Codex        logged in  session  ██████░░░░░░░░░░░░░░   30%  medium  Tue Oct 06 17:50 (in 0h 59m)
                        week     ████████████████████   98%  high    Sat Oct 10 11:04 (in 3d 18h)
Antigravity  absent
"""

FAILURE_TABLE = """\
AGENT  STATUS  WINDOW  QUOTA  LEFT  LEVEL  RESET
Codex  error   timed out
"""


def render(usages, colors):
    reporter = TableReporter(colors, TableReporter.Resets(NOW, LOCAL))
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        reporter.report(usages)
    return out.getvalue()


class TableReporterTest(unittest.TestCase):
    def test_usages(self):
        self.assertEqual(render(USAGE_EXAMPLE, TableReporter.Colors(enabled=False)), USAGE_TABLE)

    def test_usages_colored(self):
        colored = render(USAGE_EXAMPLE, TableReporter.Colors(enabled=True))

        self.assertIn("\x1b[", colored)
        self.assertEqual(TableReporter.Colors.strip(colored), USAGE_TABLE)

    def test_failure(self):
        self.assertEqual(render(FAILURE_EXAMPLE, TableReporter.Colors(enabled=False)), FAILURE_TABLE)


if __name__ == "__main__":
    unittest.main()
