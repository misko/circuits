#!/usr/bin/env python3
"""Regression tests for component-specific P-ADJ keep-short partners."""
from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path


if "pcbnew" not in sys.modules:
    pcbnew = types.ModuleType("pcbnew")
    pcbnew.ToMM = lambda value: value
    sys.modules["pcbnew"] = pcbnew

SCRIPT = Path(__file__).resolve().parents[1] / "policy_audit.py"
SPEC = importlib.util.spec_from_file_location("policy_audit", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class KeepShortPartnerRefsTest(unittest.TestCase):
    def test_absent_partner_refs_preserves_legacy_behavior(self):
        self.assertIsNone(MODULE.keep_short_partner_refs(None))

    def test_refdes_list_is_closed_and_trimmed(self):
        self.assertEqual(
            MODULE.keep_short_partner_refs([" C1 ", "L3"]), {"C1", "L3"})

    def test_scalar_or_empty_partner_refs_is_rejected(self):
        for value in ("L3", [], [""]):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    MODULE.keep_short_partner_refs(value)


if __name__ == "__main__":
    unittest.main()
