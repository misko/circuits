#!/usr/bin/env python3
"""Focused compatibility tests for shared route-transaction acceptance."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from route_acceptance_core import (  # noqa: E402
    admit,
    classify_native_drc_result,
    derive_required_checks,
    objective_vector,
    pareto_relation,
)


def report(*, violations=None, unconnected=None, parity=None):
    return {
        "$schema": "https://schemas.kicad.org/drc.v1.json",
        "source": "synthetic.kicad_pcb",
        "date": "2026-08-24T12:00:00Z",
        "kicad_version": "9.0",
        "violations": list(violations or []),
        "unconnected_items": list(unconnected or []),
        "schematic_parity": list(parity or []),
    }


class NativeDrcClassificationTest(unittest.TestCase):
    def test_tool_error_with_empty_report_is_incomplete(self):
        with tempfile.TemporaryDirectory(prefix="route-core-") as temporary:
            path = Path(temporary) / "drc.json"
            path.write_bytes(b"")
            result = classify_native_drc_result(
                returncode=2, report_path=path, profile="final")
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertIn("DRC_ABNORMAL_EXIT", result["reasons"])
        self.assertIn("DRC_REPORT_EMPTY", result["reasons"])

    def test_stale_json_is_incomplete(self):
        with tempfile.TemporaryDirectory(prefix="route-core-") as temporary:
            path = Path(temporary) / "drc.json"
            path.write_text(json.dumps(report()), encoding="utf-8")
            old = time.time_ns() - 10_000_000_000
            os.utime(path, ns=(old, old))
            result = classify_native_drc_result(
                returncode=0, report_path=path, profile="final",
                started_at_ns=time.time_ns())
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertIn("DRC_REPORT_STALE", result["reasons"])

    def test_wave_accepts_invariant_preexisting_unrelated_open(self):
        open_item = {"type": "unconnected_items", "description": "AUX.1 to AUX.2"}
        baseline = report(unconnected=[open_item])
        current = report(unconnected=[{**open_item, "uuid": "deadbeef"}])
        result = classify_native_drc_result(
            returncode=0, report=current, profile="wave", baseline=baseline)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["counts"]["unconnected"], 1)

    def test_final_requires_absolute_zero_zero_zero(self):
        native = classify_native_drc_result(
            returncode=0, report=report(), profile="final")
        native["subject"] = {"path": "synthetic.kicad_pcb", "size": 1,
                             "sha256": "0" * 64}
        receipt = admit("final", {"native_drc": native})
        self.assertEqual(native["status"], "PASS")
        self.assertEqual(native["counts"], {
            "violations": 0, "unconnected": 0, "schematic_parity": 0})
        self.assertEqual(receipt["verdict"], "ACCEPTED")

        forged = {**native, "status": "PASS",
                  "counts": {"violations": 0, "unconnected": 1,
                             "schematic_parity": 0}}
        rejected = admit("final", {"native_drc": forged})
        self.assertEqual(rejected["verdict"], "REJECTED")

    def test_final_cannot_opt_out_or_forge_native_evidence(self):
        missing = admit("final", {"_meta": {"required_checks": []}})
        self.assertEqual(missing["verdict"], "INCOMPLETE")
        forged = admit("final", {
            "_meta": {"required_checks": ["native_drc"]},
            "native_drc": {"status": "PASS", "counts": {
                "violations": 0, "unconnected": 0, "schematic_parity": 0}},
        })
        self.assertEqual(forged["verdict"], "INCOMPLETE")

    def test_nonzero_counts_only_wave_baseline_is_incomplete(self):
        current = report(violations=[{"type": "clearance", "description": "new"}])
        result = classify_native_drc_result(
            returncode=0, report=current, profile="wave",
            baseline={"counts": {"violations": 1, "unconnected": 0,
                                 "schematic_parity": 0}})
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertIn("DRC_BASELINE_SEMANTICS_MISSING", result["reasons"])


class TransactionPolicyTest(unittest.TestCase):
    def test_empty_objective_is_incomplete(self):
        vector = objective_vector({})
        self.assertFalse(vector["complete"])
        self.assertEqual(
            pareto_relation(vector, vector)["relation"], "INCOMPLETE")

    def test_required_checks_follow_touched_semantics(self):
        checks = derive_required_checks(
            "wave", {"requested_nets": ["VBUS"], "endpoints": ["J1.1"],
                     "power_nets": ["VBUS"]})
        self.assertIn("endpoint_layer_closure", checks)
        self.assertIn("power_graph_delta", checks)
        self.assertIn("connectivity_regression", checks)
        self.assertIn("objective_pareto", checks)

    def test_pareto_improvement_and_non_improvement(self):
        previous = {"drc_violations": 2, "requested_opens": 2,
                    "via_count": 4}
        improved = {"drc_violations": 1, "requested_opens": 1,
                    "via_count": 4}
        relation = pareto_relation(previous, improved)
        self.assertEqual(relation["relation"], "IMPROVEMENT")
        self.assertTrue(relation["is_improvement"])

        tradeoff = {"drc_violations": 1, "requested_opens": 3,
                    "via_count": 4}
        relation = pareto_relation(previous, tradeoff)
        self.assertEqual(relation["relation"], "TRADEOFF")
        self.assertFalse(relation["is_improvement"])

        old_checks = {
            "native_drc": {"status": "PASS", "counts": {
                "violations": 2, "unconnected": 2, "schematic_parity": 0}},
            "connectivity_regression": {"status": "PASS", "counts": {
                "requested_opens_after": 2}},
        }
        new_checks = {
            "native_drc": {"status": "PASS", "counts": {
                "violations": 1, "unconnected": 1, "schematic_parity": 0}},
            "connectivity_regression": {"status": "PASS", "counts": {
                "requested_opens_after": 1}},
        }
        relation = pareto_relation(objective_vector(old_checks),
                                   objective_vector(new_checks))
        self.assertEqual(relation["relation"], "IMPROVEMENT")


if __name__ == "__main__":
    unittest.main()
