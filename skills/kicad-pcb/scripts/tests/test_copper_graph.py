#!/usr/bin/env python3
"""Synthetic-fixture tests for canonical copper graph transactions."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from copper_graph import (  # noqa: E402
    canonical_copper_inventory,
    diff_copper,
    endpoint_layer_closure,
    filled_zone_components,
    power_graph_delta,
    requested_net_regressions,
)


def track(net, start, end, layer="F.Cu", **extra):
    return {"kind": "track", "net": net, "layer": layer,
            "start": start, "end": end, "width": 0.2, **extra}


class CopperInventoryTest(unittest.TestCase):
    def test_uuid_and_serialization_do_not_change_inventory(self):
        left = [track("SCL", [0, 0], [1, 0], uuid="left", order=1)]
        right = [track("SCL", [1, 0], [0, 0], uuid="right", order=99)]
        self.assertEqual(canonical_copper_inventory(left)["signature"],
                         canonical_copper_inventory(right)["signature"])
        self.assertFalse(diff_copper(left, right)["changed"])

    def test_arc_curvature_is_semantic(self):
        left = [{"kind": "arc", "net": "RF", "layer": "F.Cu",
                 "start": [0, 0], "mid": [1, 1], "end": [2, 0],
                 "width": 0.2}]
        right = [{"kind": "arc", "net": "RF", "layer": "F.Cu",
                  "start": [0, 0], "mid": [1, -1], "end": [2, 0],
                  "width": 0.2}]
        delta = diff_copper(left, right)
        self.assertTrue(delta["changed"])

    def test_unowned_net_mutation_is_rejected(self):
        before = [track("SCL", [0, 0], [1, 0])]
        after = before + [track("SDA", [0, 1], [1, 1])]
        delta = diff_copper(
            before, after, touched={"nets": ["SDA"], "actor": "control_wave"},
            ownership={"SDA": "critical_wave"})
        self.assertEqual(delta["status"], "FAIL")
        self.assertEqual(delta["counts"]["unowned_mutations"], 1)
        self.assertEqual(delta["findings"][0]["type"], "UNOWNED_MUTATION")


class ConnectivityTest(unittest.TestCase):
    def test_requested_opens_increase_is_rejected_but_unrelated_opens_are_ignored(self):
        before = {"connectivity": {
            "REQ": {"components": [["U1.1", "U2.1"]]},
            "AUX": {"components": [["J1.1"], ["J2.1"]]},
        }}
        after = {"connectivity": {
            "REQ": {"components": [["U1.1"], ["U2.1"]]},
            "AUX": {"components": [["J1.1"], ["J2.1"]]},
        }}
        result = requested_net_regressions(before, after, ["REQ"])
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["counts"]["requested_opens_before"], 0)
        self.assertEqual(result["counts"]["requested_opens_after"], 1)
        self.assertTrue(any(row["type"] == "REQUESTED_OPENS_INCREASED"
                            for row in result["findings"]))

    def test_smd_endpoint_copper_on_wrong_layer_fails(self):
        board = {"items": [
            {"kind": "pad", "net": "DATA", "ref": "U1", "pad": "1",
             "at": [0, 0], "layers": ["F.Cu"], "through_hole": False},
            track("DATA", [0, 0], [1, 0], layer="B.Cu"),
        ]}
        result = endpoint_layer_closure(board, nets=["DATA"])
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["findings"][0]["type"], "ENDPOINT_WRONG_LAYER")
        self.assertEqual(result["findings"][0]["expected_layers"], ["F.Cu"])
        self.assertEqual(result["findings"][0]["observed_layers"], ["B.Cu"])


class PowerGraphTest(unittest.TestCase):
    def test_absent_requested_power_zone_is_incomplete(self):
        result = filled_zone_components({"zones": []}, ["VBUS"])
        self.assertFalse(result["evidence_complete"])
        self.assertEqual(result["incomplete_nets"], ["VBUS"])

    def test_power_zone_split_is_semantic_not_uuid_based(self):
        before = {"zones": [{
            "net": "VBUS", "layer": "F.Cu", "uuid": "old",
            "components": [{
                "polygon": [[0, 0], [4, 0], [4, 2], [0, 2]],
                "terminals": ["J1.1", "U1.1"],
            }],
        }]}
        after = {"zones": [{
            "net": "VBUS", "layer": "F.Cu", "uuid": "new",
            "components": [
                {"polygon": [[0, 0], [1.5, 0], [1.5, 2], [0, 2]],
                 "terminals": ["J1.1"]},
                {"polygon": [[2.5, 0], [4, 0], [4, 2], [2.5, 2]],
                 "terminals": ["U1.1"]},
            ],
        }]}
        self.assertEqual(filled_zone_components(before)["counts"]["components"], 1)
        self.assertEqual(filled_zone_components(after)["counts"]["components"], 2)
        result = power_graph_delta(before, after, power_nets=["VBUS"])
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["counts"]["splits"], 1)
        self.assertTrue(any(row["type"] == "POWER_ZONE_SPLIT"
                            for row in result["findings"]))


if __name__ == "__main__":
    unittest.main()
