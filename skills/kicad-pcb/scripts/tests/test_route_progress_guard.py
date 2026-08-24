#!/usr/bin/env python3
"""Focused unit tests for semantic routing exploration bounds."""
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from route_progress_guard import observe  # noqa: E402


def observation(unresolved, *, x=1.0, finding="clearance", frontier="hub_top",
                requested=2, queued=2):
    return {
        "subject": "r0sha:wave-control",
        "unresolved": unresolved,
        "hard_findings": [{"type": finding, "x_mm": x, "y_mm": x + 1,
                           "owner": frontier, "nets": ["SCL", "SDA"]}],
        "frontier": [{"owner": frontier, "x_mm": x}],
        "operations": {"requested": requested, "queued": queued},
    }


class RouteProgressGuardTest(unittest.TestCase):
    def test_coordinate_only_variation_stagnates(self):
        state, first = observe(observation(["SCL"], x=1.0))
        state, second = observe(observation(["SCL"], x=84.0), state)
        self.assertEqual(first["decision"], "NOVEL_PROGRESS")
        self.assertEqual(second["decision"], "STAGNATED")
        self.assertEqual(first["signature"], second["signature"])

    def test_reducing_opens_is_progress(self):
        state, _ = observe(observation(["SCL", "SDA"]))
        _, result = observe(observation(["SCL"], frontier="east"), state)
        self.assertEqual(result["decision"], "NOVEL_PROGRESS")

    def test_new_semantic_finding_gets_bounded_diagnostic_attempt(self):
        state, _ = observe(observation(["SCL"], finding="clearance"))
        _, result = observe(observation(["SCL"], finding="via_in_pad"), state)
        self.assertEqual(result["decision"], "NOVEL_PROGRESS")

    def test_operation_amplification_stops(self):
        state, _ = observe(observation(["SCL"], queued=2))
        _, result = observe(observation(["SCL"], frontier="east",
                                        requested=2, queued=20), state)
        self.assertEqual(result["decision"], "STAGNATED")

    def test_empty_problem_is_complete(self):
        _, result = observe({"subject": "x", "unresolved": [],
                             "hard_findings": [], "frontier": []})
        self.assertEqual(result["decision"], "COMPLETE")

    def test_two_nonimproving_objectives_force_backtrack(self):
        first_obs = observation(["SCL"])
        first_obs["objective"] = {"requested_opens": 1, "drc_violations": 0}
        state, _ = observe(first_obs)
        second_obs = observation(["SCL"], frontier="east")
        second_obs["objective"] = {"requested_opens": 1, "drc_violations": 0}
        state, second = observe(second_obs, state)
        self.assertEqual(second["decision"], "CONTINUE_DIAGNOSTIC")
        third_obs = observation(["SCL"], frontier="north")
        third_obs["objective"] = {"requested_opens": 1, "drc_violations": 0}
        _, third = observe(third_obs, state)
        self.assertEqual(third["decision"], "STAGNATED")
        self.assertTrue(third["stop"])
        self.assertIn("backtrack", third)

    def test_incomplete_first_objective_stops_without_seeding_baseline(self):
        first = observation(["SCL"])
        first["objective"] = {}
        state, result = observe(first)
        self.assertEqual(result["decision"], "STAGNATED")
        self.assertTrue(result["stop"])
        self.assertEqual(
            result["objective_relation"]["relation"], "INCOMPLETE")
        self.assertEqual(state["last_objective"], {})

    def test_empty_route_cannot_hide_incomplete_objective(self):
        _, result = observe({
            "subject": "x", "unresolved": [], "hard_findings": [],
            "frontier": [], "objective": {}})
        self.assertEqual(result["decision"], "STAGNATED")
        self.assertTrue(result["stop"])


if __name__ == "__main__":
    unittest.main()
