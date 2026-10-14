"""Antigravity collector."""

from datetime import datetime

from ..cli import find, run
from .base import Collector
from .model import Quota, Status, clamp_percent

GROUP = "gemini models"
WINDOW_LABELS = {"five hour limit remaining": "session", "weekly limit remaining": "week"}


class Antigravity(Collector):
    NAME = "Antigravity"

    def detect(self):
        """Check installation only: agy has no login status command."""
        return Status.INSTALLED if find("agy") else Status.ABSENT

    def fetch(self):
        """Run `agy -p "/usage"`."""
        return run("agy", "-p", "/usage", check=True).stdout.strip()

    def parse(self, raw):
        """Read the "Gemini Models" limits from tab-separated output, one window per line."""
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
            windows[key] = Quota(left=clamp_percent(float(remaining.rstrip("%"))), reset=resets_at)
        if not windows:
            raise RuntimeError(f"no Gemini Models limits in agy /usage output:\n{raw}")
        return windows.get("session"), windows.get("week")
