#!/usr/bin/env python3
"""Focused tests for pre-route owner and corridor decisions."""
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from route_ownership_preflight import audit_config  # noqa: E402


def base_cfg():
    return {
        "prep": {"waves": {"groups": {"pwr": ["P5V"],
                                         "xtal": ["XTAL1", "XTAL2"],
                                         "sig": ["SCL"]}}},
        "route": {
            "common": {"layers": ["F.Cu", "B.Cu"]},
            "waves": [
                {"name": "xtal", "group": "xtal", "layers": ["F.Cu"]},
                {"name": "sig", "group": "sig"},
                {"name": "pwr", "group": "pwr"},
            ],
        },
    }


NETS = {"classes": {"POWER": {"nets": ["P5V"],
                                "routing": "pour_or_wide_track"}}}
PAD_COUNTS = {"P5V": 22, "XTAL1": 2, "XTAL2": 2, "SCL": 2}
BOARD_NETS = set(PAD_COUNTS)


class RouteOwnershipPreflightTest(unittest.TestCase):
    def test_many_pad_power_without_owner_fails(self):
        result = audit_config(base_cfg(), pad_counts=PAD_COUNTS,
                              board_nets=BOARD_NETS, nets_cfg=NETS)
        self.assertEqual(result["verdict"], "FAIL")
        self.assertIn("O-PWR", {row["code"] for row in result["findings"]})

    def test_deterministic_owner_cannot_also_be_generic_wave(self):
        cfg = base_cfg()
        cfg["route"]["ownership"] = {"nets": {"P5V": {
            "topology": "wide_trunk", "owner": "prep.seed_stubs",
            "why": "reviewed 3 A trunk",
        }}}
        result = audit_config(cfg, pad_counts=PAD_COUNTS,
                              board_nets=BOARD_NETS, nets_cfg=NETS)
        self.assertIn("O-DOUBLE", {row["code"] for row in result["findings"]})

    def test_owned_power_excluded_from_wave_passes(self):
        cfg = base_cfg()
        cfg["route"]["waves"] = cfg["route"]["waves"][:2]
        cfg["route"]["ownership"] = {"nets": {"P5V": {
            "topology": "wide_trunk", "owner": "prep.seed_stubs",
            "why": "reviewed 3 A trunk",
        }}}
        result = audit_config(cfg, pad_counts=PAD_COUNTS,
                              board_nets=BOARD_NETS, nets_cfg=NETS)
        self.assertEqual(result["verdict"], "PASS")

    def test_constrained_corridor_must_claim_first(self):
        cfg = base_cfg()
        cfg["route"]["waves"][:2] = list(reversed(cfg["route"]["waves"][:2]))
        cfg["route"]["ownership"] = {
            "corridors": {"hub_top": {
                "claim_order": ["sig", "xtal"],
                "why": "shared hub top escape",
            }}
        }
        result = audit_config(cfg, pad_counts={"SCL": 2, "XTAL1": 2,
                                               "XTAL2": 2},
                              board_nets={"SCL", "XTAL1", "XTAL2"},
                              nets_cfg={})
        self.assertIn("O-FLEX", {row["code"] for row in result["findings"]})


if __name__ == "__main__":
    unittest.main()
