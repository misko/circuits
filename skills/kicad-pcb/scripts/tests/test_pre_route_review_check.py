#!/usr/bin/env python3
"""Regression tests for stable, electrically exact PR-REVIEW netlist hashes."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "pre_route_review_check.py"
SPEC = importlib.util.spec_from_file_location("pre_route_review_check", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def netlist(date: str, tstamp: str, net: str = "VBUS") -> str:
    return f'''(export
  (version "E")
  (design
    (source "board.kicad_sch")
    (date "{date}")
    (sheet (title_block (date "2026-08-01"))))
  (components
    (comp (ref "U1")
      (value "IC")
      (footprint "Package:QFN")
      (tstamps "{tstamp}")))
  (nets
    (net (code "1") (name "{net}")
      (node (ref "U1") (pin "1") (pinfunction "VIN")))))
'''


class NetlistDigestTest(unittest.TestCase):
    def digest(self, content: str) -> str:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "board.net"
            path.write_text(content)
            return MODULE.netlist_digest(path)

    def test_export_clock_and_instance_uuid_are_ignored(self) -> None:
        first = self.digest(netlist(
            "2026-08-01T01:02:03", "11111111-1111-1111-1111-111111111111"))
        second = self.digest(netlist(
            "2026-08-02T09:08:07", "22222222-2222-2222-2222-222222222222"))
        self.assertEqual(first, second)

    def test_electrical_change_invalidates_review(self) -> None:
        first = self.digest(netlist(
            "2026-08-01T01:02:03", "11111111-1111-1111-1111-111111111111", "VBUS"))
        changed = self.digest(netlist(
            "2026-08-02T09:08:07", "22222222-2222-2222-2222-222222222222", "GND"))
        self.assertNotEqual(first, changed)


if __name__ == "__main__":
    unittest.main()
