#!/usr/bin/env python3
"""Focused regressions for deterministic functional-cell placement checks."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import placement_cell_checks as checks  # noqa: E402


def pad(x: float, y: float, *, net: str = "", size=(1.0, 1.0), **facts):
    return {"at": [x, y], "size_mm": list(size), "net": net, **facts}


def part(mpn: str, **pads):
    return {"mpn": mpn, "pads": pads}


class PlacementCellChecksTest(unittest.TestCase):
    def test_wrong_regulator_orientation_fails_signed_functional_vector(self):
        contract = {
            "schema": 1,
            "selected_parts": {
                "U_REG": {
                    "mpn": "TPSM63606SRDLR",
                    "pad_roles": {"vin": "1", "vout": "2"},
                }
            },
            "cells": [{
                "id": "bank-a",
                "functional_vectors": [{
                    "id": "vin-to-vout-axis",
                    "from": {"ref": "U_REG", "role": "vin"},
                    "to": {"ref": "U_REG", "role": "vout"},
                    "expected_direction": [1, 0],
                    "min_projection_mm": 0.5,
                }],
            }],
        }
        # Exact pad identity is intact, but the placed body is rotated so its
        # functional axis points west rather than east.
        snapshot = {"parts": {
            "U_REG": part("TPSM63606SRDLR",
                          **{"1": pad(2, 0, net="VIN"),
                             "2": pad(0, 0, net="VOUT")}),
        }}

        report = checks.evaluate_placement_cells(contract, snapshot)

        self.assertEqual(report["status"], checks.FAIL)
        vector = report["checks"]["functional_vectors"]
        self.assertEqual(vector["status"], checks.FAIL)
        self.assertEqual((vector["graded"], vector["total"]), (1, 1))
        self.assertIn("orientation is reversed", "\n".join(vector["findings"]))
        self.assertEqual(report["checks"]["selected_part_pad_roles"]["status"],
                         checks.PASS)

    def test_selected_part_roles_are_bound_to_exact_mpn(self):
        contract = {
            "selected_parts": {
                "U1": {"mpn": "EXACT-A", "pad_roles": {
                    "input": {"pads": ["1"], "net": "VIN"},
                }},
            },
        }
        snapshot = {"parts": {"U1": part(
            "LOOKALIKE-B", **{"1": pad(0, 0, net="VIN")})}}

        result = checks.check_selected_part_pad_roles(contract, snapshot)

        self.assertEqual(result["status"], checks.FAIL)
        self.assertEqual((result["graded"], result["total"]), (2, 2))
        self.assertIn("exact MPN", "\n".join(result["findings"]))

    def test_expected_mpn_cannot_serve_as_observed_identity(self):
        contract = {"selected_parts": {
            "U1": {"mpn": "EXACT-A", "pad_roles": {"input": "1"}},
        }}
        snapshot = {"parts": {"U1": {"mpn": "", "pads": {
            "1": pad(0, 0, net="VIN")}}}}
        result = checks.check_selected_part_pad_roles(contract, snapshot)
        self.assertEqual(result["status"], checks.INCOMPLETE)
        self.assertIn("cannot serve as its own measurement",
                      "\n".join(result["findings"]))

    def test_crossed_ordered_local_paths_fail_before_routing(self):
        contract = {"cells": [{
            "id": "bootstrap",
            "local_paths": [
                {"id": "bst", "ordered": ["U1.1", "R1.1"]},
                {"id": "sw", "ordered": ["U1.2", "R1.2"]},
            ],
        }]}
        snapshot = {"parts": {
            "U1": part("REG", **{"1": pad(0, 0), "2": pad(0, 2)}),
            "R1": part("RES", **{"1": pad(2, 2), "2": pad(2, 0)}),
        }}

        result = checks.check_local_paths(contract, snapshot)

        self.assertEqual(result["status"], checks.FAIL)
        self.assertEqual((result["graded"], result["total"]), (2, 2))
        self.assertIn("cross", "\n".join(result["findings"]))

    def test_simultaneous_reservations_reject_one_layer_overlap(self):
        contract = {"cells": [{
            "id": "port-1",
            "reservations": [
                {"id": "power", "commodity": "2a-power", "layer": "F.Cu",
                 "bbox": [0, 0, 4, 2]},
                {"id": "control", "commodity": "enable", "layer": "F.Cu",
                 "bbox": [3, 1, 5, 3]},
                {"id": "usb", "commodity": "usb-reference", "layer": "In1.Cu",
                 "bbox": [0, 0, 5, 3]},
            ],
        }]}

        result = checks.check_reservations(contract, {"parts": {}})

        self.assertEqual(result["status"], checks.FAIL)
        self.assertEqual((result["graded"], result["total"]), (3, 3))
        self.assertIn("simultaneous reservations", "\n".join(result["findings"]))

    def test_impossible_stack_aware_resistance_lower_bound_fails(self):
        contract = {
            "stackup": {
                "layers": {"In2.Cu": {"copper_thickness_um": 15.2}},
                "temperature_c": 85,
                "reference_temperature_c": 20,
                "copper_tempco_per_c": 0.00393,
            },
            "cells": [{
                "id": "power-bank",
                "hot_paths": [{
                    "id": "protected-trunk",
                    "pcb_mohm_allocation": 1.0,
                    "segments": [{
                        "length_mm": 100,
                        "max_width_mm": 0.1,
                        "allowed_layers": ["In2.Cu"],
                    }],
                }],
            }],
        }

        result = checks.check_hot_path_lower_bounds(contract, {"parts": {}})

        self.assertEqual(result["status"], checks.FAIL)
        self.assertEqual((result["graded"], result["total"]), (1, 1))
        row = result["items"][0]
        self.assertGreater(row["lower_bound_mohm"], row["pcb_mohm_allocation"])
        self.assertIn("consumes/exceeds", "\n".join(result["findings"]))

    def test_boxed_pad_without_escape_decision_fails_census(self):
        snapshot = {"parts": {
            "U_GATE": part("SN74LVC1G00DCKR", **{
                "2": pad(0, 0, constrained=True,
                         escape_aperture_mm=0.18, route_envelope_mm=0.45),
            }),
        }}

        result = checks.check_constrained_pad_escapes({}, snapshot)

        self.assertEqual(result["status"], checks.FAIL)
        self.assertEqual((result["graded"], result["total"]), (1, 1))
        self.assertIn("no explicit escape decision", "\n".join(result["findings"]))

    def test_legal_exact_dogbone_passes(self):
        contract = {"cells": [{
            "id": "gate-3",
            "constrained_pads": ["U_GATE.2"],
            "escape_decisions": [{
                "pad": "U_GATE.2",
                "kind": "dogbone",
                "path": [[0, 0], [1.0, 0]],
                "via_at": [1.0, 0],
                "via_diameter_mm": 0.45,
                "via_drill_mm": 0.20,
                "trace_width_mm": 0.20,
                "clearance_mm": 0.16,
                "required_clearance_mm": 0.15,
                "layers": ["F.Cu"],
            }],
        }]}
        snapshot = {"parts": {
            "U_GATE": part("SN74LVC1G00DCKR", **{
                "2": pad(0, 0, size=(0.6, 0.8), constrained=True),
            }),
        }, "obstacles": []}

        result = checks.check_constrained_pad_escapes(contract, snapshot)

        self.assertEqual(result["status"], checks.PASS)
        self.assertEqual((result["graded"], result["total"]), (1, 1))
        self.assertEqual(result["items"][0]["kind"], "dogbone")

    def test_selected_critical_ground_with_no_egress_fails(self):
        contract = {"selected_parts": {
            "C_IN": {"mpn": "CAP-10UF", "pad_roles": {
                "positive": "1",
                "bypass_ground": {"pads": ["2"], "critical_ground": True},
            }},
        }}
        snapshot = {"parts": {"C_IN": part(
            "CAP-10UF", **{"1": pad(0, 0, net="VIN"),
                           "2": pad(1, 0, net="GND")})}}

        result = checks.check_critical_ground_egress(contract, snapshot)

        self.assertEqual(result["status"], checks.FAIL)
        self.assertEqual((result["graded"], result["total"]), (1, 1))
        self.assertIn("no local egress", "\n".join(result["findings"]))

    def test_pilot_replica_obstacle_and_structural_mismatch_fail(self):
        contract = {
            "cells": [
                {"id": "pilot", "members": ["U1"],
                 "structure": {"escape": "dogbone"}},
                {"id": "port-2", "members": ["U2"],
                 "structure": {"escape": "via_in_pad"}},
            ],
            "replicas": [{
                "id": "pilot-to-port-2",
                "pilot": "pilot",
                "replica": "port-2",
                "ref_map": {"U1": "U2"},
                "transform": {"translate": [10, 0]},
                "tolerance_mm": 0.01,
            }],
        }
        snapshot = {
            "parts": {
                "U1": part("SWITCH-A", **{"1": pad(0, 0), "2": pad(1, 0)}),
                # A functional lookalike cannot satisfy exact equivalence.
                "U2": part("SWITCH-B", **{"1": pad(10, 0), "2": pad(11, 0)}),
            },
            "obstacles": [
                {"id": "pilot-crystal", "cell": "pilot", "kind": "body",
                 "layer": "F.Cu", "bbox": [1, 1, 2, 2]},
                # Transform should produce [11,1,12,2]; this is wider.
                {"id": "replica-crystal", "cell": "port-2", "kind": "body",
                 "layer": "F.Cu", "bbox": [11, 1, 13, 2]},
            ],
        }

        result = checks.check_pilot_replica_equivalence(contract, snapshot)

        self.assertEqual(result["status"], checks.FAIL)
        findings = "\n".join(result["findings"])
        self.assertIn("exact-MPN mismatch", findings)
        self.assertIn("semantic structure mismatch", findings)
        self.assertIn("obstacle mismatch", findings)

    def test_malformed_applicable_contract_is_incomplete_not_exception(self):
        contract = {"cells": [{"id": "bad", "functional_vectors": {
            "from": "U1.1", "to": "U1.2",
        }}]}

        report = checks.evaluate_placement_cells(contract, {"parts": {}})

        self.assertEqual(report["status"], checks.INCOMPLETE)
        self.assertEqual(report["checks"]["functional_vectors"]["status"],
                         checks.INCOMPLETE)
        self.assertGreaterEqual(report["total"], 1)

    def test_simple_board_is_explicit_na_with_zero_denominator(self):
        report = checks.evaluate_placement_cells(
            {"schema": 1}, {"parts": {"J1": part("HDR", **{
                "1": pad(0, 0, net="SIG"),
            })}})

        self.assertEqual(report["status"], checks.NA)
        self.assertEqual(report["applicability"], "NOT_APPLICABLE")
        self.assertEqual((report["graded"], report["total"]), (0, 0))
        self.assertTrue(all(row["status"] == checks.NA
                            for row in report["checks"].values()))
        # The mapping is durable/deterministic and contains no accidental
        # non-JSON geometry objects.
        self.assertEqual(json.loads(json.dumps(report, sort_keys=True)), report)


if __name__ == "__main__":
    unittest.main()
