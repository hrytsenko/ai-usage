"""Antigravity collector."""

from datetime import datetime

from .cli import find, run
from .model import Agent, Failure, Quota, Status, Usage

GROUP = "gemini models"
WINDOW_LABELS = {"five hour limit remaining": "session", "weekly limit remaining": "week"}


class Antigravity:
    NAME = "Antigravity"

    def collect(self):
        """Detect the agent, then fetch its quotas if it's usable; a step that raises makes a Failure."""
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
        """Check installation only: agy has no login status command, so an installed agy counts as usable."""
        if not find("agy"):
            return Agent(self.NAME, Status.ABSENT, usable=False)
        return Agent(self.NAME, Status.INSTALLED, usable=True)

    def _fetch(self):
        """Run `agy -p "/usage"` and read the "Gemini Models" limits, one tab-separated window per line."""
        raw = run("agy", "-p", "/usage", check=True).stdout.strip()
        windows = {}
        for line in raw.splitlines():
            parts = [p.strip() for p in line.split("\t")]
            if len(parts) != 4:
                continue
            group, label, remaining, resets = parts
            key = WINDOW_LABELS.get(label.lower())
            if group.lower() != GROUP or not key:
                continue
            resets_at = datetime.fromisoformat(resets) if resets else None
            windows[key] = Quota.of(float(remaining.rstrip("%")), resets_at)
        if not windows:
            raise RuntimeError(f"no Gemini Models limits in agy /usage output:\n{raw}")
        return windows.get("session"), windows.get("week")
