"""The pattern every collector follows: detect the agent, fetch its quota data, parse it."""

from abc import ABC, abstractmethod

from .model import Agent, Quota, Result, Status


def error_line(e):
    """Return the first line of the exception's message, or its type name if the message is empty."""
    text = str(e).strip()
    return text.splitlines()[0] if text else type(e).__name__


class Collector(ABC):
    """Subclasses set NAME and implement detect, fetch and parse; collect runs them in order."""

    NAME = ""

    @abstractmethod
    def detect(self) -> Status:
        """Return ABSENT, INSTALLED, LOGGED_IN or LOGGED_OUT."""

    @abstractmethod
    def fetch(self):
        """Ask the CLI for quota data and return its raw response."""

    @abstractmethod
    def parse(self, raw) -> tuple[Quota | None, Quota | None]:
        """Turn the raw response into (session, week) quotas, raising if neither is found."""

    def collect(self) -> Result:
        """Run detect, fetch and parse, stopping early if the agent isn't usable or a step raises."""
        try:
            status = self.detect()
        except Exception as e:
            return self._failed("detect", e)
        if not status.usable:
            return Result(Agent(self.NAME, status))

        try:
            raw = self.fetch()
        except Exception as e:
            return self._failed("fetch", e)

        try:
            session, week = self.parse(raw)
        except Exception as e:
            return self._failed("parse", e)
        return Result(Agent(self.NAME, status), session, week)

    def _failed(self, step, e):
        return Result(Agent(self.NAME, Status.ERROR, error=f"{step}: {error_line(e)}"))
