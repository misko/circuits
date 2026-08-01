import struct
import unittest

from phub_protocol import (
    REPORT_SIZE,
    ProtocolError,
    decode_port_status,
    encode_command,
)


class ProtocolTests(unittest.TestCase):
    def test_command_has_crc_and_fixed_size(self):
        report = encode_command(0x11, 7, 2, b"\x01")
        self.assertEqual(len(report), REPORT_SIZE)
        self.assertEqual(report[:8], b"PH\x01\x00\x11\x07\x02\x00")

    def test_port_status_keeps_command_and_measurement_distinct(self):
        report = bytearray(encode_command(0x90, 8, 3))
        report[8:15] = bytes([1, 1, 0, 1, 1, 0, 0])
        struct.pack_into("<HHII", report, 16, 4100, 3250, 9, 123456)
        import binascii
        struct.pack_into("<I", report, 60,
                         binascii.crc32(report[:60]) & 0xFFFFFFFF)
        status = decode_port_status(bytes(report))
        self.assertTrue(status.power_commanded)
        self.assertFalse(status.vbus_present)
        self.assertTrue(status.overcurrent)
        self.assertFalse(status.data_commanded)
        self.assertEqual(status.current_ma, 3250)

    def test_corruption_is_rejected(self):
        report = bytearray(encode_command(1, 1))
        report[20] ^= 0x80
        with self.assertRaisesRegex(ProtocolError, "CRC"):
            decode_port_status(bytes(report))


if __name__ == "__main__":
    unittest.main()
