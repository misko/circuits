import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "host"))

import phubctl


class HostToolTests(unittest.TestCase):
    def test_simulated_status_keeps_os_fact_unknown(self):
        args = phubctl.parser().parse_args(["--simulate", "status", "2"])
        result = phubctl.run(args)
        self.assertEqual(result["port"], 2)
        self.assertEqual(result["attach_enumeration"], "unknown")

    def test_simulated_data_connect_uses_logical_connected_state(self):
        args = phubctl.parser().parse_args(
            ["--simulate", "data-connect", "3"])
        result = phubctl.run(args)
        self.assertTrue(result["data_commanded"])
        self.assertTrue(result["data_enabled"])

    def test_real_mode_requires_explicit_assigned_identity(self):
        args = phubctl.parser().parse_args(["status", "1"])
        with self.assertRaisesRegex(RuntimeError, "--vid and --pid"):
            phubctl.run(args)


if __name__ == "__main__":
    unittest.main()
