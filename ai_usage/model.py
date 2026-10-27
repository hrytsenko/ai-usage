"""The model shared by the collectors and reporters: agents and their usage."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Status(StrEnum):
    """What detection found about an agent."""

    ABSENT = "absent"  # CLI not on PATH
    INSTALLED = "installed"  # on PATH; the CLI can't report its login
    LOGGED_IN = "logged in"
    LOGGED_OUT = "logged out"


@dataclass
class Agent:
    """The agent as its collector detected it."""

    name: str
    status: Status
    usable: bool  # whether quotas can be read


@dataclass
class Quota:
    """One rate-limit window."""

    left: int  # percent of the limit left: 0 = exhausted, 100 = untouched
    reset: datetime | None  # in UTC

    @classmethod
    def of(cls, left, reset):
        """Make a Quota from a raw percent left, rounded to an int within 0..100."""
        return cls(max(0, min(100, round(left))), reset)


@dataclass
class Usage:
    """The agent and its session (5-hour) and weekly quotas (None when not read or not reported)."""

    agent: Agent
    session: Quota | None = None
    week: Quota | None = None


@dataclass
class Failure:
    """The agent's quotas couldn't be collected."""

    name: str
    reason: str

    @classmethod
    def of(cls, name, error):
        """Make the Failure of an error, keeping the first line of its message."""
        text = str(error).strip()
        return cls(name, text.splitlines()[0] if text else type(error).__name__)
