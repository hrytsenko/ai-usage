"""Quota collectors, one per agent CLI.

Each is a `base.Collector` that implements detect, fetch and parse; `collect()` runs them and returns a `Usage`,
or a `Failure` if any of them went wrong.
"""

from .agy import Antigravity
from .claude import Claude
from .codex import Codex
from .model import Agent, Failure, Level, Quota, Status, Usage

COLLECTORS = [Claude(), Codex(), Antigravity()]

__all__ = ["COLLECTORS", "Agent", "Failure", "Level", "Quota", "Status", "Usage"]
