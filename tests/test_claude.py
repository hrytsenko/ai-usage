"""Detection and parsing of Claude Code output."""

import subprocess
import unittest
from datetime import UTC, datetime
from unittest import mock

from ai_usage.collectors import Status
from ai_usage.collectors.claude import Claude

# Trimmed `claude auth status --json` output when logged in, exit code 0.
LOGGED_IN_OUTPUT = '{"loggedIn": true}'

# Trimmed `claude auth status --json` output when logged out, exit code 1.
LOGGED_OUT_OUTPUT = '{"loggedIn": false}'


def detect(path, stdout="", returncode=0):
    """Run Claude.detect with `claude` found at path and `claude auth status` answering stdout."""
    proc = subprocess.CompletedProcess([], returncode, stdout=stdout, stderr="")
    with (
        mock.patch("ai_usage.collectors.claude.find", return_value=path),
        mock.patch("ai_usage.collectors.claude.run", return_value=proc),
    ):
        return Claude().detect()


class DetectTest(unittest.TestCase):
    def test_absent(self):
        self.assertEqual(detect(None), Status.ABSENT)

    def test_logged_in(self):
        self.assertEqual(detect("claude", LOGGED_IN_OUTPUT, 0), Status.LOGGED_IN)

    def test_logged_out(self):
        self.assertEqual(detect("claude", LOGGED_OUT_OUTPUT, 1), Status.LOGGED_OUT)


# Trimmed `claude -p "/usage"` output.
USAGE_OUTPUT = """\
Current session: 8% used · resets Oct 6, 9:29pm (Europe/Bucharest)
Current week (all models): 4% used · resets Oct 10, 1:59pm (Europe/Bucharest)"""


class CapturedNow(datetime):
    """Claude prints no year, so the collector infers it from now: pin now to when USAGE_OUTPUT was captured."""

    @classmethod
    def now(cls, tz=None):
        return datetime(2026, 10, 6, 16, 0, tzinfo=UTC).astimezone(tz)


class ParseTest(unittest.TestCase):
    @mock.patch("ai_usage.collectors.claude.datetime", CapturedNow)
    def test_parse(self):
        session, week = Claude().parse(USAGE_OUTPUT)

        self.assertEqual(session.left, 92)  # 8% used
        self.assertEqual(session.reset.isoformat(), "2026-10-06T18:29:00+00:00")  # Oct 6, 9:29pm
        self.assertEqual(week.left, 96)  # 4% used
        self.assertEqual(week.reset.isoformat(), "2026-10-10T10:59:00+00:00")  # Oct 10, 1:59pm


if __name__ == "__main__":
    unittest.main()
