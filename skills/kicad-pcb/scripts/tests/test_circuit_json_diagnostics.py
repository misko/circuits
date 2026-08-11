#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "circuit_json_diagnostics.py"
SPEC = importlib.util.spec_from_file_location("circuit_json_diagnostics", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class CircuitJsonDiagnosticsTest(unittest.TestCase):
    def write(self, value) -> Path:
        directory = Path(tempfile.mkdtemp(prefix="tsx-diag-test-"))
        path = directory / "circuit.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def test_warnings_are_reported_but_not_errors(self):
        errors, warnings, scanned = MODULE.grade(self.write([
            {"type": "source_part_not_found_warning", "message": "advisory"},
            {"type": "source_component"},
        ]))
        self.assertEqual(errors, [])
        self.assertEqual(warnings["source_part_not_found_warning"], 1)
        self.assertEqual(scanned, 2)

    def test_embedded_error_is_a_failure_candidate(self):
        errors, warnings, scanned = MODULE.grade(self.write([
            {"type": "pcb_port_clearance_error", "message": "pads overlap"},
            {"type": "source_unnamed_trace_warning"},
        ]))
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["type"], "pcb_port_clearance_error")
        self.assertEqual(warnings["source_unnamed_trace_warning"], 1)
        self.assertEqual(scanned, 2)

    def test_non_list_root_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "root must be a list"):
            MODULE.grade(self.write({"type": "source_component"}))


if __name__ == "__main__":
    unittest.main()
