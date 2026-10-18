"""Detection and parsing of Codex output."""

import json
import subprocess
import unittest
from unittest import mock

from ai_usage.collectors import Status
from ai_usage.collectors.codex import Codex

# Trimmed `codex login status` output when logged in, exit code 0.
LOGGED_IN_OUTPUT = "Logged in using ChatGPT"

# Trimmed `codex login status` output when logged out, exit code 1.
LOGGED_OUT_OUTPUT = "Not logged in"


def detect(path, stderr="", returncode=0):
    """Run Codex.detect with `codex` found at path and `codex login status` answering stderr."""
    proc = subprocess.CompletedProcess([], returncode, stdout="", stderr=stderr)
    with (
        mock.patch("ai_usage.collectors.codex.find", return_value=path),
        mock.patch("ai_usage.collectors.codex.run", return_value=proc),
    ):
        return Codex().detect()


class DetectTest(unittest.TestCase):
    def test_absent(self):
        self.assertEqual(detect(None), Status.ABSENT)

    def test_logged_in(self):
        self.assertEqual(detect("codex", LOGGED_IN_OUTPUT, 0), Status.LOGGED_IN)

    def test_logged_out(self):
        self.assertEqual(detect("codex", LOGGED_OUT_OUTPUT, 1), Status.LOGGED_OUT)


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


class ParseTest(unittest.TestCase):
    def test_parse(self):
        # Codex.fetch returns the reply's "result".
        session, week = Codex().parse(json.loads(USAGE_REPLY)["result"])

        self.assertEqual(session.left, 100)  # usedPercent 0
        self.assertEqual(session.reset.isoformat(), "2026-10-06T19:03:38+00:00")  # resetsAt 1791313418
        self.assertEqual(week.left, 98)  # usedPercent 2
        self.assertEqual(week.reset.isoformat(), "2026-10-10T08:04:50+00:00")  # resetsAt 1791619490


if __name__ == "__main__":
    unittest.main()
