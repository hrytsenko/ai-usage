# Agent guidelines

- Use the features of the Python version in `requires-python`.
- Code must pass `uv run ruff check` and `uv run python -m unittest`.
- Keep collectors independent. When agents report status or quotas the same way, that's a coincidence, so don't extract shared code to remove the duplication.
