"""JSON reporter."""

import json

from ..collectors import Failure


class JsonReporter:
    """Reports usages as JSON."""

    FAILED = "error"  # the status reported for a Failure

    def report(self, usages):
        """Report usages as JSON."""
        out = {}
        for u in usages:
            if isinstance(u, Failure):
                out[u.name] = {"status": self.FAILED, "error": u.reason}
                continue
            entry = {"status": u.agent.status}
            if u.agent.usable:
                entry.update(session=self._quota(u.session), week=self._quota(u.week))
            out[u.agent.name] = entry
        print(json.dumps(out, indent=2, ensure_ascii=False))

    @staticmethod
    def _quota(quota):
        if quota is None:
            return None
        return {"left": quota.left, "reset": quota.reset.isoformat() if quota.reset else None}
