"""Claude Code: parsing `claude -p "/usage"` output."""

import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from ai_usage.collectors.claude import Claude

# Real `claude -p "/usage"` output. Only the "Current session" and "Current week (all models)" lines matter.
OUTPUT = """\
You are currently using your subscription to power your Claude Code usage

Current session: 8% used · resets Oct 6, 9:29pm (Europe/Bucharest)
Current week (all models): 4% used · resets Oct 10, 1:59pm (Europe/Bucharest)

What's contributing to your limits usage?
Approximate, based on local sessions on this machine — does not include other devices or claude.ai. Behaviors are independent characteristics, not a breakdown.

Last 7d · 460 requests · 32 sessions
  34% of your usage was at >150k context
  Top skills: /headless-run:headless-run 6%
  Top plugins: headless-run 6%"""


# Europe/Bucharest in October (EEST). Fixed, so the test doesn't need a tz database.
BUCHAREST = timezone(timedelta(hours=3))


class CapturedNow(datetime):
    """Claude prints no year, so the collector infers it from now: pin now to when OUTPUT was captured."""

    @classmethod
    def now(cls, tz=None):
        return datetime(2026, 10, 6, 16, 0, tzinfo=timezone.utc).astimezone(tz)


class ParseTest(unittest.TestCase):
    @mock.patch("ai_usage.collectors.claude.datetime", CapturedNow)
    @mock.patch("ai_usage.collectors.claude._zone", return_value=BUCHAREST)
    def test_reads_session_and_week(self, _zone):
        session, week = Claude().parse(OUTPUT)

        self.assertEqual(session.left, 92)  # 8% used
        self.assertEqual(session.reset.isoformat(), "2026-10-06T18:29:00+00:00")  # Oct 6, 9:29pm
        self.assertEqual(week.left, 96)  # 4% used
        self.assertEqual(week.reset.isoformat(), "2026-10-10T10:59:00+00:00")  # Oct 10, 1:59pm


if __name__ == "__main__":
    unittest.main()
