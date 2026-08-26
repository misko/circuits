import unittest

from phub_protocol import ProtocolError
from phub_state import HubController, PortController


class StateTests(unittest.TestCase):
    def test_reset_state_is_power_off_and_data_physically_disconnected(self):
        port = PortController(1)
        self.assertFalse(port.outputs.power_en)
        self.assertTrue(port.outputs.data_oe_n)
        self.assertFalse(port.status().data_enabled)

    def test_active_low_data_control_reports_connected_state(self):
        port = PortController(2)
        port.set_data(True, 10)
        self.assertFalse(port.outputs.data_oe_n)
        self.assertTrue(port.status().data_enabled)
        port.set_data(False, 20)
        self.assertTrue(port.outputs.data_oe_n)

    def test_fault_latches_and_immediately_removes_power(self):
        port = PortController(3)
        port.set_power(True, 1)
        port.sample(fault_active=True, vbus_mv=5000, current_ma=3795, now_ms=2)
        self.assertFalse(port.outputs.power_en)
        self.assertTrue(port.fault_latched)
        self.assertEqual(port.fault_count, 1)
        with self.assertRaises(ProtocolError):
            port.set_power(True, 3)
        with self.assertRaises(ProtocolError):
            port.clear_fault(3)
        port.sample(fault_active=False, vbus_mv=0, current_ma=0, now_ms=4)
        port.clear_fault(5)
        port.set_power(True, 6)
        self.assertTrue(port.outputs.power_en)

    def test_power_cycle_clamps_duration_and_preserves_data(self):
        port = PortController(4)
        port.set_data(True, 1)
        port.set_power(True, 1)
        self.assertEqual(port.power_cycle(1, 10), 50)
        self.assertFalse(port.outputs.power_en)
        self.assertFalse(port.outputs.data_oe_n)
        port.sample(fault_active=False, vbus_mv=0, current_ma=0, now_ms=59)
        self.assertFalse(port.outputs.power_en)
        port.sample(fault_active=False, vbus_mv=5000, current_ma=100, now_ms=60)
        self.assertTrue(port.outputs.power_en)

    def test_vbus_presence_has_hysteresis(self):
        port = PortController(1)
        port.sample(fault_active=False, vbus_mv=4499, current_ma=0, now_ms=1)
        self.assertFalse(port.vbus_present)
        port.sample(fault_active=False, vbus_mv=4500, current_ma=0, now_ms=2)
        self.assertTrue(port.vbus_present)
        port.sample(fault_active=False, vbus_mv=4201, current_ma=0, now_ms=3)
        self.assertTrue(port.vbus_present)
        port.sample(fault_active=False, vbus_mv=4200, current_ma=0, now_ms=4)
        self.assertFalse(port.vbus_present)

    def test_masks_apply_independently(self):
        hub = HubController()
        hub.safe_defaults(power_mask=0b0101, data_mask=0b1010, now_ms=7)
        self.assertTrue(hub.port(1).outputs.power_en)
        self.assertFalse(hub.port(1).status().data_enabled)
        self.assertFalse(hub.port(2).outputs.power_en)
        self.assertTrue(hub.port(2).status().data_enabled)


if __name__ == "__main__":
    unittest.main()
