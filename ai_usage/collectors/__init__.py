"""Quota collectors, one per agent CLI.

Each has a `NAME` and a `collect()` that returns a `Usage`, or a `Failure` if it went wrong.
"""

from .agy import Antigravity
from .claude import Claude
from .codex import Codex
from .model import Agent, Failure, Quota, Status, Usage

COLLECTORS = [Claude(), Codex(), Antigravity()]

__all__ = ["COLLECTORS", "Agent", "Failure", "Quota", "Status", "Usage"]
