"""Codex: parsing the `account/rateLimits/read` result from `codex app-server`."""

import json
import unittest

from ai_usage.collectors.codex import Codex

# The real app-server reply to the rate-limit request (pretty-printed; account id masked).
# Each bucket has a 5-hour (300 min) and a weekly (10080 min) window, with resets as Unix timestamps;
# "rateLimits" repeats the "codex" bucket for older clients.
REPLY = """\
{
  "id": 2,
  "result": {
    "ordinaryUsageAllowed": true,
    "rateLimits": {
      "limitId": "codex",
      "limitName": null,
      "normalModelSlug": null,
      "primary": {
        "usedPercent": 0,
        "windowDurationMins": 300,
        "resetsAt": 1791313418
      },
      "secondary": {
        "usedPercent": 2,
        "windowDurationMins": 10080,
        "resetsAt": 1791619490
      },
      "credits": {
        "hasCredits": false,
        "unlimited": false,
        "balance": "0"
      },
      "individualLimit": null,
      "spendControlReached": false,
      "planType": "plus",
      "rateLimitReachedType": null
    },
    "rateLimitsByLimitId": {
      "codex": {
        "limitId": "codex",
        "limitName": null,
        "normalModelSlug": null,
        "primary": {
          "usedPercent": 0,
          "windowDurationMins": 300,
          "resetsAt": 1791313418
        },
        "secondary": {
          "usedPercent": 2,
          "windowDurationMins": 10080,
          "resetsAt": 1791619490
        },
        "credits": {
          "hasCredits": false,
          "unlimited": false,
          "balance": "0"
        },
        "individualLimit": null,
        "spendControlReached": false,
        "planType": "plus",
        "rateLimitReachedType": null
      }
    },
    "rateLimitResetCredits": {
      "availableCount": 2,
      "credits": null
    },
    "accountId": "00000000-0000-0000-0000-000000000000",
    "rateLimitUpsell": null
  }
}"""

class ParseTest(unittest.TestCase):
    def test_reads_session_and_week(self):
        # Codex.fetch returns the reply's "result".
        session, week = Codex().parse(json.loads(REPLY)["result"])

        self.assertEqual(session.left, 100)  # usedPercent 0
        self.assertEqual(session.reset.isoformat(), "2026-10-06T19:03:38+00:00")  # resetsAt 1791313418
        self.assertEqual(week.left, 98)  # usedPercent 2
        self.assertEqual(week.reset.isoformat(), "2026-10-10T08:04:50+00:00")  # resetsAt 1791619490


if __name__ == "__main__":
    unittest.main()
