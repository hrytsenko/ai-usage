"""Antigravity collector.

detect: agy has no login status command, so only installation is checked.
fetch:  `agy -p "/usage"`, keeping only the "Gemini Models" limits. Output is tab-separated, one window per line:
    Gemini Models	Weekly Limit Remaining	99%	2026-10-09T16:34:43Z
    Gemini Models	Five Hour Limit Remaining	100%	2026-10-05T19:58:09Z
    Claude and GPT models	Weekly Limit Remaining	100%	2026-10-12T14:58:30Z
"""

from datetime import datetime

from ..cli import find, run
from .base import Collector
from .model import Quota, Status, clamp_percent

GROUP = "gemini models"
WINDOW_LABELS = {"five hour limit remaining": "session", "weekly limit remaining": "week"}


class Antigravity(Collector):
    NAME = "Antigravity"

    def detect(self):
        return Status.INSTALLED if find("agy") else Status.ABSENT

    def fetch(self):
        return run("agy", "-p", "/usage", check=True).stdout.strip()

    def parse(self, raw):
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
