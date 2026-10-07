"""Quota collectors, one per agent CLI.

Each is a `base.Collector` that implements detect, fetch and parse; `collect()` runs them and returns a `Result`.
"""

from .agy import Antigravity
from .claude import Claude
from .codex import Codex
from .model import Agent, Quota, Result, Status

COLLECTORS = [Claude(), Codex(), Antigravity()]

__all__ = ["COLLECTORS", "Agent", "Quota", "Result", "Status"]
