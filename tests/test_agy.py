"""Antigravity: parsing `agy -p "/usage"` output."""

import unittest

from ai_usage.collectors.agy import Antigravity

# Real `agy -p "/usage"` output: group, window, percent left, reset (UTC).
# The columns are separated by literal tab characters, as agy prints them.
OUTPUT = """\
Gemini Models	Weekly Limit Remaining	99%	2026-10-09T16:34:43Z
Gemini Models	Five Hour Limit Remaining	100%	2026-10-06T19:03:41Z
Claude and GPT models	Weekly Limit Remaining	100%	2026-10-13T14:03:41Z
Claude and GPT models	Five Hour Limit Remaining	100%	2026-10-06T19:03:41Z"""


class ParseTest(unittest.TestCase):
    def test_reads_session_and_week(self):
        session, week = Antigravity().parse(OUTPUT)

        self.assertEqual(session.left, 100)  # Five Hour Limit Remaining 100%
        self.assertEqual(session.reset.isoformat(), "2026-10-06T19:03:41+00:00")  # 2026-10-06T19:03:41Z
        self.assertEqual(week.left, 99)  # Weekly Limit Remaining 99%
        self.assertEqual(week.reset.isoformat(), "2026-10-09T16:34:43+00:00")  # 2026-10-09T16:34:43Z


if __name__ == "__main__":
    unittest.main()
