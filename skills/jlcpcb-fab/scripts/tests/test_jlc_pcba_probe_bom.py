#!/usr/bin/env python3
"""Regression tests for request-derived public-catalog probe BOMs."""
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "jlc_pcba_availability.py"
SPEC = importlib.util.spec_from_file_location("jlc_pcba_availability", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class ProbeBomTest(unittest.TestCase):
    def test_probe_is_exact_projection_of_request(self):
        request = {
            "rows": [
                {"requested_lcsc": "C100", "designators": ["U1", "U2"]},
                {"requested_lcsc": "C200", "designators": ["R1"]},
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "probe.csv"
            MOD.write_catalog_probe_bom(path, request)
            with path.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
        self.assertEqual(["C100", "C200"], [row["LCSC"] for row in rows])
        self.assertEqual("U1,U2", rows[0]["Designator"])

    def test_invalid_request_row_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "probe.csv"
            with self.assertRaises(ValueError):
                MOD.write_catalog_probe_bom(
                    path, {"rows": [{"requested_lcsc": "TPS25980",
                                      "designators": ["U1"]}]})


if __name__ == "__main__":
    unittest.main()
