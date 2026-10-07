"""Shared result types for the collectors."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

LOW_THRESHOLD = 15  # percent left at or below which a quota counts as low
MEDIUM_THRESHOLD = 40  # percent left at or below which a quota counts as medium


class Status(Enum):
    """How far a collector got with an agent."""

    ABSENT = "absent"  # CLI not on PATH
    INSTALLED = "installed"  # on PATH; the CLI can't report its login
    LOGGED_IN = "logged in"
    LOGGED_OUT = "logged out"
    ERROR = "error"  # a step failed; Agent.error says which and why

    @property
    def usable(self):
        """Installed, and not known to be logged out."""
        return self in (Status.INSTALLED, Status.LOGGED_IN)


@dataclass
class Agent:
    name: str
    status: Status
    error: str | None = None  # "<step>: <reason>" when status is ERROR


@dataclass
class Quota:
    """One rate-limit window."""

    left: int  # percent of the limit left: 0 = exhausted, 100 = untouched
    reset: datetime | None  # in UTC

    @property
    def level(self):
        """"exhausted", "low", "medium" or "high", by percent left."""
        if self.left <= 0:
            return "exhausted"
        if self.left <= LOW_THRESHOLD:
            return "low"
        if self.left <= MEDIUM_THRESHOLD:
            return "medium"
        return "high"


@dataclass
class Result:
    """The agent and its session (5-hour) and weekly quotas (None when not read or not reported)."""

    agent: Agent
    session: Quota | None = None
    week: Quota | None = None


def clamp_percent(value):
    """Round to an int percent within 0..100."""
    return max(0, min(100, round(value)))

