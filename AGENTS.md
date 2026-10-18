# Agent guidelines

- Code must use the features of the Python version in `requires-python`.
- Code must pass `uv run ruff check` and `uv run python -m unittest`.
- Collectors must be independent. When different agents report status or quotas the same way, treat it as a coincidence and don't share code between their collectors.
- Collector tests must use realistic CLI output. Start from a real capture and keep only what the collector reads or must skip. Trim personal data such as account IDs. When a CLI changes its format, start from a new capture rather than editing the old one.
