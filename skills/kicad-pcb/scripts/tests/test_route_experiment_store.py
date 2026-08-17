#!/usr/bin/env python3
"""Tests for terminal route-experiment retention."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from route_experiment_store import prune_report, record, verify  # noqa: E402


class RouteExperimentStoreTest(unittest.TestCase):
    def test_one_accepted_pointer_and_relocatable_objects(self):
        root = Path(tempfile.mkdtemp(prefix="route-store-"))
        candidate = root / "candidate.kicad_pcb"
        receipt = root / "receipt.json"
        candidate.write_text("copper")
        receipt.write_text("{}")
        store = root / "store"
        record(store, "c1", "ACCEPTED", "r0", [candidate], receipt)
        with self.assertRaises(ValueError):
            record(store, "c2", "ACCEPTED", "r0", [candidate], receipt)
        moved = root / "moved"
        shutil.move(store, moved)
        self.assertTrue(verify(moved, "c1")[0])

    def test_terminal_state_cannot_be_rewritten(self):
        root = Path(tempfile.mkdtemp(prefix="route-store-"))
        artifact = root / "finding.json"
        artifact.write_text("finding")
        store = root / "store"
        record(store, "bad1", "REJECTED", "r0", [artifact])
        with self.assertRaises(ValueError):
            record(store, "bad1", "INCOMPLETE", "r0", [artifact])

    def test_prune_never_lists_referenced_object(self):
        root = Path(tempfile.mkdtemp(prefix="route-store-"))
        artifact = root / "finding.json"
        artifact.write_text("finding")
        store = root / "store"
        record(store, "bad1", "REJECTED", "r0", [artifact])
        report = prune_report(store)
        self.assertEqual(report["unreferenced"], [])


if __name__ == "__main__":
    unittest.main()
