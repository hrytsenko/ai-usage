# Agent guidelines

- Use the features of the Python version in `requires-python`.
- Code must pass `uv run ruff check` and `uv run python -m unittest`.
- Keep collectors independent. When agents report status or quotas the same way, treat it as a coincidence and don't extract shared code to remove the duplication.
- Test collectors against real CLI output, copied verbatim. Mask only personal data such as account IDs. When a CLI changes its format, capture new output rather than editing the old one.
