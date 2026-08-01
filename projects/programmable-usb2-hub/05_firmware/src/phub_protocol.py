"""Hardware-independent PHUB v1 record codec and status model."""

from __future__ import annotations

from dataclasses import dataclass
import binascii
from enum import IntEnum
import struct

REPORT_SIZE = 64
MAGIC = b"PH"
VERSION = (1, 0)


class Opcode(IntEnum):
    GET_INFO = 0x01
    GET_PORT = 0x10
    SET_POWER = 0x11
    POWER_CYCLE = 0x12
    SET_DATA = 0x13
    CLEAR_FAULT = 0x14
    GET_ALL = 0x20
    SET_SAFE_DEFAULTS = 0x30


class ProtocolError(ValueError):
    pass


@dataclass(frozen=True)
class PortStatus:
    port: int
    power_commanded: bool
    power_enabled: bool
    vbus_present: bool
    overcurrent: bool
    fault_latched: bool
    data_commanded: bool
    data_enabled: bool
    vbus_mv: int
    current_ma: int
    fault_count: int
    last_transition_ms: int


def _crc(payload: bytes) -> int:
    return binascii.crc32(payload) & 0xFFFFFFFF


def encode_command(opcode: int, sequence: int, port: int = 0,
                   payload: bytes = b"") -> bytes:
    if not 0 <= port <= 4:
        raise ProtocolError("port must be 0..4")
    if len(payload) > 52:
        raise ProtocolError("payload exceeds 52 bytes")
    report = bytearray(REPORT_SIZE)
    report[:8] = bytes((*MAGIC, *VERSION, opcode & 0xFF,
                        sequence & 0xFF, port, 0))
    report[8:8 + len(payload)] = payload
    struct.pack_into("<I", report, 60, _crc(report[:60]))
    return bytes(report)


def validate_report(report: bytes) -> None:
    if len(report) != REPORT_SIZE:
        raise ProtocolError(f"expected {REPORT_SIZE} bytes")
    if report[:2] != MAGIC or tuple(report[2:4]) != VERSION:
        raise ProtocolError("bad magic or protocol version")
    expected = struct.unpack_from("<I", report, 60)[0]
    if _crc(report[:60]) != expected:
        raise ProtocolError("CRC mismatch")


def decode_port_status(report: bytes) -> PortStatus:
    validate_report(report)
    port = report[6]
    if not 1 <= port <= 4:
        raise ProtocolError("PORT_STATUS contains invalid port")
    return PortStatus(
        port=port,
        power_commanded=bool(report[8]),
        power_enabled=bool(report[9]),
        vbus_present=bool(report[10]),
        overcurrent=bool(report[11]),
        fault_latched=bool(report[12]),
        data_commanded=bool(report[13]),
        data_enabled=bool(report[14]),
        vbus_mv=struct.unpack_from("<H", report, 16)[0],
        current_ma=struct.unpack_from("<H", report, 18)[0],
        fault_count=struct.unpack_from("<I", report, 20)[0],
        last_transition_ms=struct.unpack_from("<I", report, 24)[0],
    )
