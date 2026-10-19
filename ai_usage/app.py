"""Show session and weekly quotas for the Claude Code, Codex and Antigravity (agy) CLIs.

Checks each agent and reads quotas only from those that are installed and logged in.

Usage:
    ai-usage           # table
    ai-usage --json    # structured output
"""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor

from . import __version__
from .collectors import COLLECTORS, Failure
from .reporters import JsonReporter, TableReporter


def main():
    parser = argparse.ArgumentParser(prog="ai-usage", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", action="store_true", help="print structured JSON")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args()

    # Windows consoles may default to a legacy codepage that can't print the bar characters.
    sys.stdout.reconfigure(encoding="utf-8")

    with ThreadPoolExecutor(len(COLLECTORS)) as pool:
        usages = list(pool.map(lambda c: c.collect(), COLLECTORS))

    reporter = JsonReporter() if args.json else TableReporter.for_stdout()
    reporter.report(usages)

    failed = any(isinstance(u, Failure) for u in usages)
    sys.exit(1 if failed else 0)
