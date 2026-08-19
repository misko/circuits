#!/usr/bin/env python3
"""Regression tests for hidden PCB supplier-field identity drift."""
import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "bom_source_check.py"
SPEC = importlib.util.spec_from_file_location("bom_source_check", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class BoardIdentityTest(unittest.TestCase):
    def test_matching_value_and_hidden_field_pass(self):
        records = {"U1": {"value": "C100", "lcsc_fields": ["C100"]}}
        self.assertEqual([], MOD.board_identity_findings(records, {"U1": "C100"}))

    def test_wrong_hidden_field_fails_even_when_value_matches(self):
        records = {"U1": {"value": "C100", "lcsc_fields": ["C999"]}}
        findings = MOD.board_identity_findings(records, {"U1": "C100"})
        self.assertEqual(1, len(findings))
        self.assertIn("PCB-LCSC-MISMATCH U1", findings[0])

    def test_wrong_value_and_missing_footprint_fail(self):
        records = {"U1": {"value": "C999", "lcsc_fields": []}}
        findings = MOD.board_identity_findings(
            records, {"U1": "C100", "U2": "C200"})
        self.assertTrue(any("PCB-VALUE-MISMATCH U1" in x for x in findings))
        self.assertTrue(any("PCB-MISSING U2" in x for x in findings))

    def test_uncoded_source_is_out_of_scope(self):
        self.assertEqual([], MOD.board_identity_findings({}, {"F1": ""}))


if __name__ == "__main__":
    unittest.main()
