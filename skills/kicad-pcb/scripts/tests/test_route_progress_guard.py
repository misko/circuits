#!/usr/bin/env python3
"""Focused unit tests for semantic routing exploration bounds."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from route_progress_guard import observe  # noqa: E402
from route_and_stitch_generic import (  # noqa: E402
    RouteConfigError, _target_board,
)


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
    def test_transaction_target_is_explicit_and_legacy_default_is_preserved(self):
        root = Path(tempfile.mkdtemp(prefix="route-target-"))
        cfg = {"_root": root, "project": {"board": "04_kicad/live.kicad_pcb"}}
        self.assertEqual(_target_board(cfg),
                         (root / "04_kicad/live.kicad_pcb").resolve())
        self.assertEqual(
            _target_board(cfg, "06_build/route/attempt/board.kicad_pcb"),
            (root / "06_build/route/attempt/board.kicad_pcb").resolve())

        cfg["project"]["build_dir"] = "out/candidates"
        self.assertEqual(
            _target_board(cfg, "out/candidates/attempt.kicad_pcb"),
            (root / "out/candidates/attempt.kicad_pcb").resolve())
        with self.assertRaises(RouteConfigError):
            _target_board(cfg, "06_build/route/attempt.kicad_pcb")

    def test_transaction_target_rejects_absolute_and_parent_escape(self):
        root = Path(tempfile.mkdtemp(prefix="route-target-"))
        cfg = {"_root": root, "project": {"board": "live.kicad_pcb"}}
        with self.assertRaises(RouteConfigError):
            _target_board(cfg, root / "attempt.kicad_pcb")
        with self.assertRaises(RouteConfigError):
            _target_board(cfg, "../escape.kicad_pcb")
        with self.assertRaises(RouteConfigError):
            _target_board(cfg, "04_kicad/live.kicad_pcb")

    def test_transaction_target_rejects_symlink_and_intermediate_symlink(self):
        root = Path(tempfile.mkdtemp(prefix="route-target-"))
        outside = Path(tempfile.mkdtemp(prefix="route-target-outside-"))
        cfg = {"_root": root, "project": {"board": "live.kicad_pcb"}}
        build = root / "06_build/route"
        build.mkdir(parents=True)
        (outside / "board.kicad_pcb").write_text("outside")
        (build / "linked-board.kicad_pcb").symlink_to(
            outside / "board.kicad_pcb")
        (build / "linked-dir").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(RouteConfigError):
            _target_board(cfg, "06_build/route/linked-board.kicad_pcb")
        with self.assertRaises(RouteConfigError):
            _target_board(cfg, "06_build/route/linked-dir/board.kicad_pcb")

    def test_transaction_target_rejects_build_tree_containing_live_board(self):
        root = Path(tempfile.mkdtemp(prefix="route-target-"))
        for build_dir in (".", "04_kicad"):
            cfg = {"_root": root, "project": {
                "board": "04_kicad/live.kicad_pcb",
                "build_dir": build_dir,
            }}
            with self.assertRaises(RouteConfigError):
                _target_board(cfg, "04_kicad/attempt.kicad_pcb")

    def test_transaction_target_rejects_hardlink_to_live_board(self):
        root = Path(tempfile.mkdtemp(prefix="route-target-"))
        live = root / "04_kicad/live.kicad_pcb"
        live.parent.mkdir(parents=True)
        live.write_text("live")
        target = root / "06_build/route/attempt/board.kicad_pcb"
        target.parent.mkdir(parents=True)
        target.hardlink_to(live)
        cfg = {"_root": root, "project": {
            "board": "04_kicad/live.kicad_pcb",
            "build_dir": "06_build/route",
        }}
        with self.assertRaises(RouteConfigError):
            _target_board(cfg, "06_build/route/attempt/board.kicad_pcb")

    def test_transaction_target_rejects_hardlink_to_any_source_file(self):
        root = Path(tempfile.mkdtemp(prefix="route-target-"))
        source = root / "03_src/rules.yaml"
        source.parent.mkdir(parents=True)
        source.write_text("authority: source\n")
        target = root / "06_build/route/attempt/board.kicad_pcb"
        target.parent.mkdir(parents=True)
        target.hardlink_to(source)
        cfg = {"_root": root, "project": {
            "board": "04_kicad/live.kicad_pcb",
            "build_dir": "06_build/route",
        }}
        with self.assertRaises(RouteConfigError):
            _target_board(cfg, "06_build/route/attempt/board.kicad_pcb")
        self.assertEqual(source.read_text(), "authority: source\n")

    def test_transaction_target_rejects_fifo(self):
        root = Path(tempfile.mkdtemp(prefix="route-target-"))
        target = root / "06_build/route/attempt/board.kicad_pcb"
        target.parent.mkdir(parents=True)
        os.mkfifo(target)
        cfg = {"_root": root, "project": {
            "board": "04_kicad/live.kicad_pcb",
            "build_dir": "06_build/route",
        }}
        with self.assertRaises(RouteConfigError):
            _target_board(cfg, "06_build/route/attempt/board.kicad_pcb")

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
