"""Collection of Antigravity quotas from its CLI output."""

import subprocess
import unittest
from unittest import mock

from ai_usage.collectors.agy import Antigravity
from ai_usage.model import Agent, Status, Usage

# Trimmed `agy -p "/usage"` output.
USAGE_OUTPUT = """\
Gemini Models	Weekly Limit Remaining	99%	2026-10-09T16:34:43Z
Gemini Models	Five Hour Limit Remaining	100%	2026-10-06T19:03:41Z"""


def collect(path):
    """Run Antigravity.collect with `agy` found at path and `/usage` answering USAGE_OUTPUT."""

    def run(name, *args, **kwargs):
        if args[:1] == ("-p",):
            return subprocess.CompletedProcess([], 0, stdout=USAGE_OUTPUT, stderr="")
        raise AssertionError(f"unexpected call: {name} {args}")

    with (
        mock.patch("ai_usage.collectors.agy.find", return_value=path),
        mock.patch("ai_usage.collectors.agy.run", side_effect=run),
    ):
        return Antigravity().collect()


class CollectTest(unittest.TestCase):
    def test_absent(self):
        self.assertEqual(collect(None), Usage(Agent(Antigravity.NAME, Status.ABSENT, usable=False)))

    def test_installed(self):
        usage = collect("agy")

        self.assertEqual(usage.agent, Agent(Antigravity.NAME, Status.INSTALLED, usable=True))
        self.assertEqual(usage.session.left, 100)  # Five Hour Limit Remaining 100%
        self.assertEqual(usage.session.reset.isoformat(), "2026-10-06T19:03:41+00:00")  # 2026-10-06T19:03:41Z
        self.assertEqual(usage.week.left, 99)  # Weekly Limit Remaining 99%
        self.assertEqual(usage.week.reset.isoformat(), "2026-10-09T16:34:43+00:00")  # 2026-10-09T16:34:43Z


if __name__ == "__main__":
    unittest.main()
