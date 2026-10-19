"""Shared result types for the collectors."""

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


def clamp_percent(value):
    """Round to an int percent within 0..100."""
    return max(0, min(100, round(value)))

