"""The JSON reported by JsonReporter."""

import contextlib
import io
import unittest

from ai_usage.reporters import JsonReporter

from .fixture_usages import FAILURE_EXAMPLE, USAGE_EXAMPLE

USAGE_JSON = """\
{
  "Claude Code": {
    "status": "logged in",
    "session": {
      "left": 73,
      "reset": "2026-10-06T19:50:00+03:00"
    },
    "week": {
      "left": 12,
      "reset": "2026-10-09T16:50:00+03:00"
    }
  },
  "Codex": {
    "status": "logged in",
    "session": {
      "left": 30,
      "reset": "2026-10-06T17:50:00+03:00"
    },
    "week": {
      "left": 98,
      "reset": "2026-10-10T11:04:00+03:00"
    }
  },
  "Antigravity": {
    "status": "absent"
  }
}
"""

FAILURE_JSON = """\
{
  "Codex": {
    "status": "error",
    "error": "timed out"
  }
}
"""


def render(usages):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        JsonReporter().report(usages)
    return out.getvalue()


class JsonReporterTest(unittest.TestCase):
    def test_usages(self):
        self.assertEqual(render(USAGE_EXAMPLE), USAGE_JSON)

    def test_failure(self):
        self.assertEqual(render(FAILURE_EXAMPLE), FAILURE_JSON)


if __name__ == "__main__":
    unittest.main()
