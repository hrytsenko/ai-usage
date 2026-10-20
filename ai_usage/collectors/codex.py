"""Codex collector."""

import json
from datetime import UTC, datetime

from .cli import find, run, start
from .model import Agent, Failure, Quota, Status, Usage

RATE_LIMITS_ID = 2  # request id of the rate-limit read, to pick out its reply

MESSAGES = [
    {"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "quota-reader", "version": "1.0"}}},
    {"method": "initialized"},
    {"id": RATE_LIMITS_ID, "method": "account/rateLimits/read", "params": {"excludeResetCreditDetails": True}},
]

SESSION_MINS = 5 * 60  # the session is the 5-hour window
WEEK_MINS = 7 * 24 * 60


class Codex:
    NAME = "Codex"

    def collect(self):
        """Detect the agent, then fetch its quotas if it's logged in; a step that raises makes a Failure."""
        step = "detect"
        try:
            agent = self._detect()
            if not agent.usable:
                return Usage(agent)
            step = "fetch"
            session, week = self._fetch()
        except Exception as e:  # noqa: BLE001 - whatever a step raises becomes the agent's Failure
            return Failure.of(self.NAME, step, e)
        return Usage(agent, session, week)

    def _detect(self):
        """Check `codex login status`, which prints e.g. "Logged in using ChatGPT"."""
        if not find("codex"):
            return Agent(self.NAME, Status.ABSENT, usable=False)
        proc = run("codex", "login", "status")
        output = (proc.stdout + proc.stderr).lower()
        logged_in = proc.returncode == 0 and "logged in" in output and "not logged in" not in output
        return Agent(self.NAME, Status.LOGGED_IN if logged_in else Status.LOGGED_OUT, usable=logged_in)

    def _fetch(self):
        """Read the 5-hour and weekly windows of the "codex" bucket from `codex app-server` over JSON-RPC on stdio."""
        with start("codex", "app-server", "--listen", "stdio://") as proc:
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
                result = msg["result"]
                break
            else:
                raise RuntimeError("codex app-server exited without answering (timed out?)")

        # Only the main "codex" bucket; "rateLimits" is its backward-compatible single-bucket copy.
        snap = (result.get("rateLimitsByLimitId") or {}).get("codex") or result.get("rateLimits")
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
    return Quota.of(100 - window["usedPercent"], datetime.fromtimestamp(resets_at, tz=UTC) if resets_at else None)
