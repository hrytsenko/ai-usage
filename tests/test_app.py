"""The agents shown by the app and its notes on stderr."""

import contextlib
import io
import json
import sys
import unittest
from unittest import mock

from ai_usage import app
from ai_usage.model import Agent, Status, Usage

ABSENT = Usage(Agent("Codex", Status.ABSENT, usable=False))
INSTALLED = Usage(Agent("Antigravity", Status.INSTALLED, usable=True))


class Collector:
    """A collector that returns a fixed usage."""

    def __init__(self, usage):
        self.usage = usage

    def collect(self):
        return self.usage


def run(usages, *args):
    """Run the app with args and collectors returning usages; return its exit code, the JSON agents and stderr."""
    # The app reconfigures stdout, which StringIO can't do.
    stdout, stderr = io.TextIOWrapper(io.BytesIO(), encoding="utf-8", newline=""), io.StringIO()
    with (
        mock.patch.object(sys, "argv", ["ai-usage", "--json", *args]),
        mock.patch("ai_usage.app.COLLECTORS", [Collector(u) for u in usages]),
        contextlib.redirect_stdout(stdout),
        contextlib.redirect_stderr(stderr),
    ):
        try:
            app.main()
        except SystemExit as e:
            code = e.code
    stdout.flush()
    return code, list(json.loads(stdout.buffer.getvalue())), stderr.getvalue()


class AppTest(unittest.TestCase):
    def test_absent_hidden_by_default(self):
        self.assertEqual(run([ABSENT, INSTALLED]), (0, ["Antigravity"], ""))

    def test_absent_shown_with_all(self):
        self.assertEqual(run([ABSENT, INSTALLED], "--all"), (0, ["Codex", "Antigravity"], ""))

    def test_none_found(self):
        code, agents, stderr = run([ABSENT])

        self.assertEqual((code, agents), (0, []))
        self.assertIn("no agents found", stderr)


if __name__ == "__main__":
    unittest.main()
