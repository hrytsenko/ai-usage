"""Reporters of the collected usages, one per output format.

Each has `report(usages)`, which reports a list of `Usage` and `Failure` to stdout.
"""

from .json import JsonReporter
from .table import TableReporter

__all__ = ["JsonReporter", "TableReporter"]
