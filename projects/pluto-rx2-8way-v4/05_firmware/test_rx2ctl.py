import argparse
import sys
from pathlib import Path
import unittest

HOST = Path(__file__).resolve().parent / "host"
TARGET_MAIN = Path(__file__).resolve().parent / "target" / "main.c"
sys.path.insert(0, str(HOST))

import rx2ctl


class ResponseTests(unittest.TestCase):
    def test_status_types(self):
        status = rx2ctl.parse_response(
            "OK running=1 state=8 sample_rate_actual=29997600.125 sync=FREE_RUNNING"
        )
        self.assertEqual(status["running"], 1)
        self.assertEqual(status["state"], 8)
        self.assertAlmostEqual(status["sample_rate_actual"], 29997600.125)
        self.assertEqual(status["sync"], "FREE_RUNNING")

    def test_error_is_not_status(self):
        with self.assertRaisesRegex(RuntimeError, "BAD_STATE"):
            rx2ctl.parse_response("ERR BAD_STATE expected=1..8")


class SimulatorTests(unittest.TestCase):
    def test_default_frame_is_exactly_eight_frames_per_buffer(self):
        backend = rx2ctl.SimBackend()
        status = rx2ctl.parse_response(backend.transact("STATUS?"))
        self.assertEqual(status["frame_samples"], 62464)
        self.assertEqual(8 * status["frame_samples"], 499712)

    def test_manual_select_and_all_off(self):
        backend = rx2ctl.SimBackend()
        self.assertEqual(rx2ctl.parse_response(backend.transact("SELECT 8"))["state"], 8)
        self.assertEqual(rx2ctl.parse_response(backend.transact("STOP"))["state"], 8)
        off = rx2ctl.parse_response(backend.transact("OFF"))
        self.assertEqual(off["muted"], 1)
        self.assertEqual(off["state"], 0)

    def test_run_is_reported_free_running(self):
        backend = rx2ctl.SimBackend()
        status = rx2ctl.parse_response(backend.transact("RUN"))
        self.assertEqual(status["running"], 1)
        self.assertEqual(status["sync"], "FREE_RUNNING")

    def test_bad_config_is_rejected(self):
        backend = rx2ctl.SimBackend()
        with self.assertRaisesRegex(RuntimeError, "BAD_CONFIG"):
            rx2ctl.parse_response(backend.transact("CONFIG 30000000 1 1 0"))
        with self.assertRaisesRegex(RuntimeError, "BAD_CONFIG"):
            rx2ctl.parse_response(
                backend.transact("CONFIG 30000000 268435456 4096 128")
            )


class HardwareShellTests(unittest.TestCase):
    def test_dma_ring_wraps_the_incrementing_schedule_read_address(self):
        source = TARGET_MAIN.read_text()
        self.assertIn("channel_config_set_read_increment(&config, true)", source)
        self.assertIn("channel_config_set_write_increment(&config, false)", source)
        self.assertIn("channel_config_set_ring(&config, false, 5u)", source)
        self.assertNotIn("channel_config_set_ring(&config, true, 5u)", source)


if __name__ == "__main__":
    unittest.main()
