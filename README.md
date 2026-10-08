# ai-usage

Shows how much of the session (5-hour) and weekly quotas is left for Claude Code, Codex and Antigravity, in one table.

It reads the quotas only through each agent's own CLI, and skips agents that aren't installed or logged in:

| Agent       | Command                       |
|-------------|-------------------------------|
| Claude Code | `claude -p "/usage"`          |
| Codex       | `codex app-server` (JSON-RPC) |
| Antigravity | `agy -p "/usage"`             |

## Install

With [uv](https://docs.astral.sh/uv/) (`winget install astral-sh.uv`), which also fetches Python 3.11+ if it's missing:

```sh
uv tool install git+https://github.com/hrytsenko/ai-usage          # latest
uv tool install git+https://github.com/hrytsenko/ai-usage@v0.1.0   # a release tag
```

This puts `ai-usage.exe` in `%USERPROFILE%\.local\bin`; run `uv tool update-shell` once if that folder isn't on your `PATH`.

```sh
uv tool upgrade ai-usage     # update
uv tool uninstall ai-usage   # remove
```

`pipx install git+https://github.com/hrytsenko/ai-usage` and `pipx upgrade ai-usage` work the same way.

## Run

```sh
ai-usage            # table
ai-usage --json     # JSON
ai-usage --version
```

## Develop

```sh
uv tool install --editable .   # ai-usage runs this checkout, so edits apply without reinstalling
python -m ai_usage             # or run it without installing
python -m unittest             # tests
```

To release, bump `__version__` in [ai_usage/\_\_init\_\_.py](ai_usage/__init__.py), commit, and tag it (`git tag v0.2.0 && git push --tags`).

The tests in [tests/](tests/) parse real outputs captured from each CLI, so they also show what each one prints.

## Output

```
AGENT        STATUS     WINDOW   QUOTA                 LEFT  LEVEL   RESET
Claude Code  logged in  session  ██████████████▋░░░░░   73%  high    Tue Oct 06 19:50 (in 2h 59m)
                        week     ██▍░░░░░░░░░░░░░░░░░   12%  low     Fri Oct 09 16:50 (in 2d 23h)
Codex        logged in  session  ██████░░░░░░░░░░░░░░   30%  medium  Tue Oct 06 17:50 (in 0h 59m)
                        week     ███████████████████▋   98%  high    Sat Oct 10 11:04 (in 3d 18h)
Antigravity  absent
```

STATUS is `absent`, `installed` (login can't be checked), `logged in`, `logged out` or `error` (with the failed step and reason).
LEVEL is `high` from 40% left (green), `medium` from 15% (yellow), `low` above 0% and `exhausted` at 0% (both red).
