#!/usr/bin/env python3
"""Synthetic-fixture tests for canonical copper graph transactions."""
from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from copper_graph import (  # noqa: E402
    canonical_copper_inventory,
    connectivity_signature,
    diff_copper,
    endpoint_layer_closure,
    filled_zone_components,
    power_graph_delta,
    requested_net_regressions,
    source_owned_copper_equivalence,
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

    def test_collinear_split_is_equivalent_but_deletion_is_not(self):
        whole = [track("CLK", [0, 0], [2, 0])]
        split = [track("CLK", [0, 0], [1, 0]),
                 track("CLK", [1, 0], [2, 0])]
        self.assertFalse(diff_copper(whole, split)["changed"])
        self.assertEqual(
            source_owned_copper_equivalence(whole, split)["status"], "PASS")

        deleted = split[:1]
        self.assertTrue(diff_copper(whole, deleted)["changed"])
        evidence = source_owned_copper_equivalence(whole, deleted)
        self.assertEqual(evidence["status"], "FAIL")
        self.assertEqual(evidence["counts"]["missing"], 1)

    def test_pcbnew_via_width_is_queried_on_an_explicit_layer(self):
        width_layers = []

        class Layers:
            def Seq(self):
                return [0, 31]

        class Point:
            x, y = 1_000_000, 2_000_000

        class Via:
            def GetNetname(self): return "GND"
            def GetLayerSet(self): return Layers()
            def TopLayer(self): return 0
            def BottomLayer(self): return 31
            def GetPosition(self): return Point()
            def GetWidth(self, layer):
                width_layers.append(layer)
                return 600_000
            def GetDrillValue(self): return 300_000

        class Arc:
            pass

        class Board:
            def GetTracks(self): return [Via()]
            def GetFootprints(self): return []
            def Zones(self): return []
            def GetLayerName(self, layer):
                return {0: "F.Cu", 31: "B.Cu"}[layer]

        fake = types.SimpleNamespace(PCB_VIA=Via, PCB_ARC=Arc)
        with mock.patch.dict(sys.modules, {"pcbnew": fake}):
            inventory = canonical_copper_inventory(Board())
        self.assertEqual(inventory["counts"]["by_kind"]["via"], 1)
        self.assertEqual(width_layers, [0])

    def test_pcbnew_via_width_falls_back_for_kicad_7(self):
        width_calls = []

        class Layers:
            def Seq(self): return [0, 31]

        class Point:
            x, y = 1_000_000, 2_000_000

        class Via:
            def GetNetname(self): return "GND"
            def GetLayerSet(self): return Layers()
            def TopLayer(self): return 0
            def BottomLayer(self): return 31
            def GetPosition(self): return Point()
            def GetWidth(self, *args):
                width_calls.append(args)
                if args:
                    raise TypeError("KiCad 7 has no layer overload")
                return 600_000
            def GetDrillValue(self): return 300_000

        class Arc:
            pass

        class Board:
            def GetTracks(self): return [Via()]
            def GetFootprints(self): return []
            def Zones(self): return []
            def GetLayerName(self, layer):
                return {0: "F.Cu", 31: "B.Cu"}[layer]

        fake = types.SimpleNamespace(PCB_VIA=Via, PCB_ARC=Arc)
        with mock.patch.dict(sys.modules, {"pcbnew": fake}):
            inventory = canonical_copper_inventory(Board())
        self.assertEqual(inventory["counts"]["by_kind"]["via"], 1)
        self.assertEqual(width_calls, [(0,), ()])

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
    def test_collinear_normalization_does_not_erase_a_branch_node(self):
        board = {"items": [
            {"kind": "pad", "net": "CLK", "ref": "U1", "pad": "1",
             "at": [0, 0], "layer": "F.Cu"},
            {"kind": "pad", "net": "CLK", "ref": "U2", "pad": "1",
             "at": [2, 0], "layer": "F.Cu"},
            {"kind": "pad", "net": "CLK", "ref": "U3", "pad": "1",
             "at": [1, 1], "layer": "F.Cu"},
            track("CLK", [0, 0], [1, 0]),
            track("CLK", [1, 0], [2, 0]),
            track("CLK", [1, 0], [1, 1]),
        ]}
        result = connectivity_signature(board, ["CLK"])
        self.assertEqual(result["nets"]["CLK"]["components"],
                         [["U1.1", "U2.1", "U3.1"]])

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
