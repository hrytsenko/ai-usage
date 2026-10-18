"""Detection and parsing of Antigravity output."""

import unittest
from unittest import mock

from ai_usage.collectors import Status
from ai_usage.collectors.agy import Antigravity


def detect(path):
    """Run Antigravity.detect with `agy` found at path."""
    with mock.patch("ai_usage.collectors.agy.find", return_value=path):
        return Antigravity().detect()


class DetectTest(unittest.TestCase):
    def test_absent(self):
        self.assertEqual(detect(None), Status.ABSENT)

    def test_installed(self):
        self.assertEqual(detect("agy"), Status.INSTALLED)


# Trimmed `agy -p "/usage"` output.
USAGE_OUTPUT = """\
Gemini Models	Weekly Limit Remaining	99%	2026-10-09T16:34:43Z
Gemini Models	Five Hour Limit Remaining	100%	2026-10-06T19:03:41Z"""


class ParseTest(unittest.TestCase):
    def test_parse(self):
        session, week = Antigravity().parse(USAGE_OUTPUT)

        self.assertEqual(session.left, 100)  # Five Hour Limit Remaining 100%
        self.assertEqual(session.reset.isoformat(), "2026-10-06T19:03:41+00:00")  # 2026-10-06T19:03:41Z
        self.assertEqual(week.left, 99)  # Weekly Limit Remaining 99%
        self.assertEqual(week.reset.isoformat(), "2026-10-09T16:34:43+00:00")  # 2026-10-09T16:34:43Z


if __name__ == "__main__":
    unittest.main()
