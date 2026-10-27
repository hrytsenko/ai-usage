"""The usages shared by the reporter tests: collected quotas and a failed collection."""

from datetime import datetime, timedelta, timezone

from ai_usage.model import Agent, Failure, Quota, Status, Usage

# The local time zone and the current time.
LOCAL = timezone(timedelta(hours=3))
# Seconds past the minute, so the relative reset times are rounded down.
NOW = datetime(2026, 10, 6, 16, 50, 30, tzinfo=LOCAL)


def reset_at(day, hour, minute):
    """A reset on that day of October 2026, in local time."""
    return datetime(2026, 10, day, hour, minute, tzinfo=LOCAL)


# Two logged-in agents with high, medium and low quotas, and an absent one.
USAGE_EXAMPLE = [
    Usage(
        Agent("Claude Code", Status.LOGGED_IN, usable=True),
        session=Quota(73, reset_at(6, 19, 50)),
        week=Quota(12, reset_at(9, 16, 50)),
    ),
    Usage(
        Agent("Codex", Status.LOGGED_IN, usable=True),
        session=Quota(30, reset_at(6, 17, 50)),
        week=Quota(98, reset_at(10, 11, 4)),
    ),
    Usage(Agent("Antigravity", Status.ABSENT, usable=False)),
]

# A collector that failed.
FAILURE_EXAMPLE = [Failure("Codex", "timed out")]
