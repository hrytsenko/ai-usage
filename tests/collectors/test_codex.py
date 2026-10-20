"""Collection of Codex quotas from its CLI output."""

import contextlib
import io
import json
import subprocess
import unittest
from unittest import mock

from ai_usage.collectors import Agent, Status, Usage
from ai_usage.collectors.codex import Codex

# Trimmed `codex login status` output when logged in, exit code 0.
LOGGED_IN_OUTPUT = "Logged in using ChatGPT"

# Trimmed `codex login status` output when logged out, exit code 1.
LOGGED_OUT_OUTPUT = "Not logged in"

# Codex app-server reply to the rate-limit read, trimmed to the 5-hour and 7-days windows.
USAGE_REPLY = """\
{
  "id": 2,
  "result": {
    "rateLimitsByLimitId": {
      "codex": {
        "primary": {"usedPercent": 0, "windowDurationMins": 300, "resetsAt": 1791313418},
        "secondary": {"usedPercent": 2, "windowDurationMins": 10080, "resetsAt": 1791619490}
      }
    }
  }
}"""


def collect(path, stderr="", returncode=0):
    """Run Codex.collect with `codex` found at path, `codex login status` answering stderr and app-server USAGE_REPLY."""

    def run(name, *args, **kwargs):
        if args[:1] == ("login",):
            return subprocess.CompletedProcess([], returncode, stdout="", stderr=stderr)
        raise AssertionError(f"unexpected call: {name} {args}")

    def start(name, *args, **kwargs):
        if args[:1] == ("app-server",):
            # The app-server writes one JSON message per line.
            stdout = io.StringIO(json.dumps(json.loads(USAGE_REPLY)) + "\n")
            return contextlib.nullcontext(mock.Mock(stdin=io.StringIO(), stdout=stdout))
        raise AssertionError(f"unexpected call: {name} {args}")

    with (
        mock.patch("ai_usage.collectors.codex.find", return_value=path),
        mock.patch("ai_usage.collectors.codex.run", side_effect=run),
        mock.patch("ai_usage.collectors.codex.start", side_effect=start),
    ):
        return Codex().collect()


class CollectTest(unittest.TestCase):
    def test_absent(self):
        self.assertEqual(collect(None), Usage(Agent(Codex.NAME, Status.ABSENT, usable=False)))

    def test_logged_out(self):
        self.assertEqual(
            collect("codex", LOGGED_OUT_OUTPUT, 1),
            Usage(Agent(Codex.NAME, Status.LOGGED_OUT, usable=False)),
        )

    def test_logged_in(self):
        usage = collect("codex", LOGGED_IN_OUTPUT, 0)

        self.assertEqual(usage.agent, Agent(Codex.NAME, Status.LOGGED_IN, usable=True))
        self.assertEqual(usage.session.left, 100)  # usedPercent 0
        self.assertEqual(usage.session.reset.isoformat(), "2026-10-06T19:03:38+00:00")  # resetsAt 1791313418
        self.assertEqual(usage.week.left, 98)  # usedPercent 2
        self.assertEqual(usage.week.reset.isoformat(), "2026-10-10T08:04:50+00:00")  # resetsAt 1791619490


if __name__ == "__main__":
    unittest.main()
