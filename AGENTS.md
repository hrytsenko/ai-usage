# Agent guidelines

## Workflow

1. Write code for the Python version in `requires-python`, using its features.
2. Check that the code passes `uv run ruff check` and `uv run python -m unittest`.
3. When a change touches the package, bump the minor version in `ai_usage/__init__.py`. Bump once per commit: if the version already differs from the last commit, leave it.

## Decisions

### Shared model

`model.py` holds the types that collectors and reporters share. It describes agents and their usage, not how a collector gets them.

### Independent collectors

Collectors must be independent. When different agents report status or quotas the same way, treat it as a coincidence and don't share code between their collectors. Generic helpers for running a CLI, as in `collectors/cli.py`, are fine to share. Taking the same steps, detect then fetch, is a convenience, not an obligation: a collector may change its steps.

### Independent reporters

Reporters must be independent. When different formats present usages the same way, such as the `error` status for a failure, treat it as a coincidence and don't share code between their reporters. Reporters report every usage they're given; choosing which ones to report, such as hiding absent agents, belongs to the app.

### Realistic CLI output in collector tests

Collector tests must use realistic CLI output. Start from a real capture and keep only what the collector reads or must skip. Trim personal data such as account IDs. When a CLI changes its format, start from a new capture rather than editing the old one.
