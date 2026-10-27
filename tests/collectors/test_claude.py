"""Collection of Claude Code quotas from its CLI output."""

import subprocess
import unittest
from datetime import UTC, datetime
from unittest import mock

from ai_usage.collectors.claude import Claude
from ai_usage.model import Agent, Status, Usage

# Trimmed `claude auth status --json` output when logged in, exit code 0.
LOGGED_IN_OUTPUT = '{"loggedIn": true}'

# Trimmed `claude auth status --json` output when logged out, exit code 1.
LOGGED_OUT_OUTPUT = '{"loggedIn": false}'

# Trimmed `claude -p "/usage"` output.
USAGE_OUTPUT = """\
Current session: 8% used · resets Oct 6, 9:29pm (Europe/Bucharest)
Current week (all models): 4% used · resets Oct 10, 1:59pm (Europe/Bucharest)"""


class CapturedNow(datetime):
    """Claude prints no year, so the collector infers it from now: pin now to when USAGE_OUTPUT was captured."""

    @classmethod
    def now(cls, tz=None):
        return datetime(2026, 10, 6, 16, 0, tzinfo=UTC).astimezone(tz)


def collect(path, status="", returncode=0):
    """Run Claude.collect with `claude` found at path, `claude auth status` answering status and `/usage` USAGE_OUTPUT."""

    def run(name, *args, **kwargs):
        if args[:1] == ("auth",):
            return subprocess.CompletedProcess([], returncode, stdout=status, stderr="")
        if args[:1] == ("-p",):
            return subprocess.CompletedProcess([], 0, stdout=USAGE_OUTPUT, stderr="")
        raise AssertionError(f"unexpected call: {name} {args}")

    with (
        mock.patch("ai_usage.collectors.claude.find", return_value=path),
        mock.patch("ai_usage.collectors.claude.run", side_effect=run),
        mock.patch("ai_usage.collectors.claude.datetime", CapturedNow),
    ):
        return Claude().collect()


class CollectTest(unittest.TestCase):
    def test_absent(self):
        self.assertEqual(collect(None), Usage(Agent(Claude.NAME, Status.ABSENT, usable=False)))

    def test_logged_out(self):
        self.assertEqual(
            collect("claude", LOGGED_OUT_OUTPUT, 1),
            Usage(Agent(Claude.NAME, Status.LOGGED_OUT, usable=False)),
        )

    def test_logged_in(self):
        usage = collect("claude", LOGGED_IN_OUTPUT, 0)

        self.assertEqual(usage.agent, Agent(Claude.NAME, Status.LOGGED_IN, usable=True))
        self.assertEqual(usage.session.left, 92)  # 8% used
        self.assertEqual(usage.session.reset.isoformat(), "2026-10-06T18:29:00+00:00")  # Oct 6, 9:29pm
        self.assertEqual(usage.week.left, 96)  # 4% used
        self.assertEqual(usage.week.reset.isoformat(), "2026-10-10T10:59:00+00:00")  # Oct 10, 1:59pm


if __name__ == "__main__":
    unittest.main()
