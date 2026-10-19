"""Codex collector."""

import json
import subprocess
import threading
from datetime import UTC, datetime

from ..cli import DETECT_TIMEOUT, TIMEOUT, find, resolve, run
from .base import Collector
from .model import Agent, Quota, Status, clamp_percent

RATE_LIMITS_ID = 2  # request id of the rate-limit read, to pick out its reply

MESSAGES = [
    {"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "quota-reader", "version": "1.0"}}},
    {"method": "initialized"},
    {"id": RATE_LIMITS_ID, "method": "account/rateLimits/read", "params": {"excludeResetCreditDetails": True}},
]

SESSION_MINS = 5 * 60  # the session is the 5-hour window
WEEK_MINS = 7 * 24 * 60


class Codex(Collector):
    NAME = "Codex"

    def detect(self):
        """Check `codex login status`, which prints e.g. "Logged in using ChatGPT"."""
        if not find("codex"):
            return Agent(self.NAME, Status.ABSENT, usable=False)
        proc = run("codex", "login", "status", timeout=DETECT_TIMEOUT)
        output = (proc.stdout + proc.stderr).lower()
        logged_in = proc.returncode == 0 and "logged in" in output and "not logged in" not in output
        return Agent(self.NAME, Status.LOGGED_IN if logged_in else Status.LOGGED_OUT, usable=logged_in)

    def fetch(self):
        """Read rate limits from `codex app-server` over JSON-RPC on stdio."""
        proc = subprocess.Popen(
            [resolve("codex"), "app-server", "--listen", "stdio://"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, encoding="utf-8", errors="replace",
        )
        timer = threading.Timer(TIMEOUT, proc.kill)
        timer.start()
        try:
            for msg in MESSAGES:
                proc.stdin.write(json.dumps(msg) + "\n")
            proc.stdin.flush()
            # Skip notifications and the initialize response until the rate-limit reply arrives.
            for line in proc.stdout:
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if msg.get("id") != RATE_LIMITS_ID:
                    continue
                if "error" in msg:
                    raise RuntimeError(f"codex error: {msg['error']}")
                return msg["result"]
            raise RuntimeError("codex app-server exited without answering (timed out?)")
        finally:
            timer.cancel()
            proc.kill()
            proc.wait()

    def parse(self, raw):
        """Read the 5-hour and weekly windows of the "codex" bucket."""
        # Only the main "codex" bucket; "rateLimits" is its backward-compatible single-bucket copy.
        snap = (raw.get("rateLimitsByLimitId") or {}).get("codex") or raw.get("rateLimits")
        if not snap:
            raise RuntimeError("no codex rate limits in app-server response")
        # Match windows by duration: "primary"/"secondary" don't promise which one is which.
        by_duration = {w.get("windowDurationMins"): w for w in (snap.get("primary"), snap.get("secondary")) if w}
        session, week = by_duration.get(SESSION_MINS), by_duration.get(WEEK_MINS)
        if not session and not week:
            raise RuntimeError(f"no 5-hour or weekly window in codex rate limits: {sorted(by_duration)}")
        return (_quota(session) if session else None), (_quota(week) if week else None)


def _quota(window):
    """Turn an app-server rate-limit window into a Quota."""
    resets_at = window.get("resetsAt")
    return Quota(
        left=clamp_percent(100 - window["usedPercent"]),
        reset=datetime.fromtimestamp(resets_at, tz=UTC) if resets_at else None,
    )
