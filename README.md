# ai-usage

Shows how much of the session (5-hour) and weekly quotas is left for Claude Code, Codex and Antigravity, in one table.

It reads the quotas only through each agent's own CLI, and skips agents that aren't installed or logged in:

| Agent       | Command                       |
|-------------|-------------------------------|
| Claude Code | `claude -p "/usage"`          |
| Codex       | `codex app-server` (JSON-RPC) |
| Antigravity | `agy -p "/usage"`             |

## Install

With [uv](https://docs.astral.sh/uv/):

```sh
uv tool install git+https://github.com/hrytsenko/ai-usage  # install
uv tool upgrade ai-usage                                   # update
uv tool uninstall ai-usage                                 # remove
```

## Run

```sh
ai-usage            # table
ai-usage --json     # JSON
ai-usage --version
```

## Develop

```sh
uv run ruff check          # lint
uv run python -m unittest  # test
uv run python -m ai_usage  # run
```

The tests parse real outputs captured from each CLI, so they also show what each one prints.

## Output

```
AGENT        STATUS     WINDOW   QUOTA                 LEFT  LEVEL   RESET
Claude Code  logged in  session  ██████████████▋░░░░░   73%  high    Tue Oct 06 19:50 (in 2h 59m)
                        week     ██▍░░░░░░░░░░░░░░░░░   12%  low     Fri Oct 09 16:50 (in 2d 23h)
Codex        logged in  session  ██████░░░░░░░░░░░░░░   30%  medium  Tue Oct 06 17:50 (in 0h 59m)
                        week     ███████████████████▋   98%  high    Sat Oct 10 11:04 (in 3d 18h)
Antigravity  absent
```

STATUS is `absent`, `installed` (when login can't be checked), `logged in`, `logged out` or `error` (with the failed step and reason).
LEVEL is `high` from 40% left (green), `medium` from 15% (yellow), `low` above 0% and `exhausted` at 0% (both red).
