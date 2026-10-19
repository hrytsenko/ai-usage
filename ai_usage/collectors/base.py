"""The pattern every collector follows: detect the agent, fetch its quota data, and parse it."""

from abc import ABC, abstractmethod

from .model import Agent, Failure, Quota, Usage


def error_line(e):
    """Return the first line of the exception's message, or its type name if the message is empty."""
    text = str(e).strip()
    return text.splitlines()[0] if text else type(e).__name__


class Collector(ABC):
    """Subclasses set NAME and implement detect, fetch and parse; collect runs them in order."""

    NAME = ""

    @abstractmethod
    def detect(self) -> Agent:
        """Return the agent with its status (ABSENT, INSTALLED, LOGGED_IN or LOGGED_OUT) and whether it's usable."""

    @abstractmethod
    def fetch(self):
        """Ask the CLI for quota data and return its raw response."""

    @abstractmethod
    def parse(self, raw) -> tuple[Quota | None, Quota | None]:
        """Turn the raw response into (session, week) quotas, raising if neither is found."""

    def collect(self) -> Usage | Failure:
        """Run detect, fetch and parse, stopping early if the agent isn't usable; a step that raises makes a Failure."""
        step = "detect"
        try:
            agent = self.detect()
            if not agent.usable:
                return Usage(agent)
            step = "fetch"
            raw = self.fetch()
            step = "parse"
            session, week = self.parse(raw)
        except Exception as e:  # noqa: BLE001 - whatever a step raises becomes the agent's Failure
            return Failure(self.NAME, f"{step}: {error_line(e)}")
        return Usage(agent, session, week)
