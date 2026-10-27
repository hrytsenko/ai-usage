"""Claude Code collector."""

import json
import re
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from ..model import Agent, Failure, Quota, Status, Usage
from .cli import find, run

LINE_RE = re.compile(
    r"^Current (?P<window>session|week \(all models\)):\s*(?P<used>\d+(?:\.\d+)?)% used"
    r"(?:.*?resets (?:(?P<month>[A-Z][a-z]{2}) (?P<day>\d{1,2}),? )?"
    r"(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?\s*(?P<ampm>am|pm)"
    r"(?:\s*\((?P<tz>[^)]+)\))?)?",
    re.MULTILINE | re.IGNORECASE,
)
MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")


class Claude:
    NAME = "Claude Code"

    def collect(self):
        """Detect the agent, then fetch its quotas if it's logged in; a step that raises makes a Failure."""
        try:
            agent = self._detect()
            if not agent.usable:
                return Usage(agent)
            session, week = self._fetch()
        except Exception as e:  # noqa: BLE001 - whatever a step raises becomes the agent's Failure
            return Failure.of(self.NAME, e)
        return Usage(agent, session, week)

    def _detect(self):
        """Check `claude auth status --json`, which reports {"loggedIn": true, ...}."""
        if not find("claude"):
            return Agent(self.NAME, Status.ABSENT, usable=False)
        proc = run("claude", "auth", "status", "--json")
        try:
            logged_in = bool(json.loads(proc.stdout).get("loggedIn"))
        except (json.JSONDecodeError, AttributeError):  # not a JSON object: trust the exit code
            logged_in = proc.returncode == 0
        return Agent(self.NAME, Status.LOGGED_IN if logged_in else Status.LOGGED_OUT, usable=logged_in)

    def _fetch(self):
        """Run `claude -p "/usage"` and read the lines that start with "Current session" and "Current week"."""
        raw = run("claude", "-p", "/usage", check=True).stdout.strip()
        windows = {}
        for m in LINE_RE.finditer(raw):
            key = "session" if m["window"].lower() == "session" else "week"
            windows[key] = Quota.of(100 - float(m["used"]), _parse_reset(m))
        if not windows:
            raise RuntimeError(f"could not parse claude /usage output:\n{raw}")
        return windows.get("session"), windows.get("week")


def _zone(name):
    """Return the named zone, or None when it's unknown or Python has no tz database."""
    if not name:
        return None
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):  # unknown zone, no tz database, or a malformed name
        return None


def _parse_reset(m):
    """Return the reset time from a LINE_RE match in UTC, or None if the line has none."""
    if not m["hour"]:
        return None
    hour = int(m["hour"]) % 12 + (12 if m["ampm"].lower() == "pm" else 0)
    minute = int(m["minute"] or 0)
    tz = _zone(m["tz"])
    # Work in naive wall-clock time of the reported zone, then attach it once the date is known.
    now = datetime.now(tz).replace(tzinfo=None)  # tz=None gives local time, already naive

    if m["month"]:
        month = MONTHS.index(m["month"].lower()) + 1
        reset = now.replace(month=month, day=int(m["day"]), hour=hour, minute=minute, second=0, microsecond=0)
        if reset < now - timedelta(days=1):  # no year in the output: a date long past means next year
            reset = reset.replace(year=reset.year + 1)
    else:
        reset = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if reset < now:
            reset += timedelta(days=1)
    # Without a known zone, assume Claude printed the reset in the machine's own zone;
    # astimezone() on a naive datetime applies the local offset (DST included) for that date.
    aware = reset.replace(tzinfo=tz) if tz else reset.astimezone()
    return aware.astimezone(UTC)
