#!/usr/bin/env python3
"""Tests for staged manufacturing-readiness composition."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import manufacturing_readiness as mr  # noqa: E402


class ManufacturingReadinessTest(unittest.TestCase):
    def test_selection_precedes_jlc_prelayout_receipt(self):
        """Part/value freeze must be reachable before a JLC request exists."""
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            circuit = project / "03_tscircuit/build/circuit.json"
            circuit.parent.mkdir(parents=True)
            circuit.write_text(json.dumps([]), encoding="utf-8")
            assembly = project / "03_src/rules/assembly.yaml"
            assembly.parent.mkdir(parents=True)
            assembly.write_text("build_quantity: 5\n", encoding="utf-8")
            (project / "02_parts").mkdir()

            with patch.object(mr, "_run", return_value={
                    "status": "PASS", "detail": "test", "output": ""}), \
                 patch.object(mr, "_pcba_check") as pcba_check:
                result = mr.grade(project, phase="selection")

            self.assertEqual(result["verdict"], "ACCEPTED")
            self.assertEqual(result["coverage"], {"passing": 2, "total": 2})
            self.assertNotIn("jlc_pcba_availability", result["checks"])
            self.assertNotIn("procurement_exposure", result["checks"])
            pcba_check.assert_not_called()


if __name__ == "__main__":
    unittest.main()
