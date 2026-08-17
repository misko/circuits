#!/usr/bin/env python3
"""Tests for staged first-power authorization."""
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from first_article_check import check  # noqa: E402


CARD = {
    "stages": [{"name": "regulator-only", "installed": ["F1", "U2", "U11"],
                "exposed_pads": ["U2"]}],
    "rails": [{
        "name": "5VA",
        "resistance": {"probe": "C17", "min_ohm": 1000, "max_ohm": 2500},
        "voltage": {"probe": "C17", "min_v": 5.0, "max_v": 5.3},
        "no_load_current": {"probe": "bench_supply", "max_a": 0.03},
        "supply": {"probe": "bench_supply", "min_v": 9.5, "max_v": 12.2,
                   "max_current_limit_a": 0.05},
    }],
}


def good_record():
    return {
        "stage": "regulator-only", "installed": ["F1", "U2", "U11"],
        "assembly_confirmations": {"U2.exposed_pad": True},
        "measurements": {"5VA": {
            "resistance": {"value": 1500, "unit": "ohm", "probe": "C17"},
            "voltage": {"value": 5.17, "unit": "V", "probe": "C17"},
            "no_load_current": {"value": 0.017, "unit": "A", "probe": "bench_supply"},
            "supply_voltage": {"value": 10.0, "unit": "V", "probe": "bench_supply"},
            "current_limit": {"value": 0.05, "unit": "A"},
        }},
    }


class FirstArticleCheckTest(unittest.TestCase):
    def test_complete_staged_record_authorizes(self):
        self.assertEqual(check(CARD, good_record())["verdict"], "AUTHORIZED")

    def test_unsoldered_exposed_pad_holds(self):
        record = good_record()
        record["assembly_confirmations"] = {}
        result = check(CARD, record)
        self.assertEqual(result["verdict"], "HOLD")
        self.assertIn("FA-EP", {row["code"] for row in result["findings"]})

    def test_population_or_abnormal_resistance_holds(self):
        record = good_record()
        record["installed"].remove("U11")
        record["measurements"]["5VA"]["resistance"]["value"] = 35
        codes = {row["code"] for row in check(CARD, record)["findings"]}
        self.assertTrue({"FA-POP", "FA-ABORT"}.issubset(codes))


if __name__ == "__main__":
    unittest.main()
