#!/usr/bin/env python3
"""Reference PHUB v1 command-line utility.

PyUSB is imported only for real hardware.  `--simulate` exercises the exact
record codec and safety state machine without installing any package.
"""

from __future__ import annotations

import argparse
import binascii
import json
from pathlib import Path
import struct
import sys
import time

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from phub_protocol import (Opcode, REPORT_SIZE, decode_port_status,
                           encode_command, validate_report)
from phub_state import HubController


def _status_report(status, opcode: int, sequence: int) -> bytes:
    report = bytearray(encode_command(opcode, sequence, status.port))
    report[8:15] = bytes((status.power_commanded, status.power_enabled,
                           status.vbus_present, status.overcurrent,
                           status.fault_latched, status.data_commanded,
                           status.data_enabled))
    struct.pack_into("<HHII", report, 16, status.vbus_mv, status.current_ma,
                     status.fault_count, status.last_transition_ms)
    struct.pack_into("<I", report, 60,
                     binascii.crc32(report[:60]) & 0xFFFFFFFF)
    return bytes(report)


class SimBackend:
    def __init__(self):
        self.hub = HubController()
        self.started = time.monotonic()

    def transact(self, request: bytes) -> bytes:
        validate_report(request)
        opcode, seq, number = request[4], request[5], request[6]
        now = int((time.monotonic() - self.started) * 1000)
        port = self.hub.port(number)
        if opcode == Opcode.SET_POWER:
            port.set_power(bool(request[8]), now)
        elif opcode == Opcode.POWER_CYCLE:
            port.power_cycle(struct.unpack_from("<I", request, 8)[0], now)
        elif opcode == Opcode.SET_DATA:
            port.set_data(bool(request[8]), now)
        elif opcode == Opcode.CLEAR_FAULT:
            port.clear_fault(now)
        elif opcode != Opcode.GET_PORT:
            raise RuntimeError(f"simulator does not implement opcode 0x{opcode:02x}")
        port.sample(fault_active=False,
                    vbus_mv=5100 if port.outputs.power_en else 0,
                    current_ma=0, now_ms=now)
        return _status_report(port.status(), opcode | 0x80, seq)

    def topology(self, port: int) -> str:
        return "unknown"


class PyUsbBackend:
    def __init__(self, vid: int, pid: int, timeout_ms: int):
        try:
            import usb.core
            import usb.util
        except ImportError as exc:
            raise RuntimeError("real hardware access requires the pyusb package") from exc
        self.usb_core = usb.core
        self.usb_util = usb.util
        self.timeout_ms = timeout_ms
        self.dev = usb.core.find(idVendor=vid, idProduct=pid)
        if self.dev is None:
            raise RuntimeError(f"PHUB device {vid:04x}:{pid:04x} not found")
        self.dev.set_configuration()
        cfg = self.dev.get_active_configuration()
        candidates = [intf for intf in cfg
                      if intf.bInterfaceClass == 0xFF]
        if not candidates:
            raise RuntimeError("device has no vendor-specific management interface")
        self.intf = candidates[0]
        eps = list(self.intf)
        self.ep_out = next((ep for ep in eps if
                            usb.util.endpoint_direction(ep.bEndpointAddress) ==
                            usb.util.ENDPOINT_OUT), None)
        self.ep_in = next((ep for ep in eps if
                           usb.util.endpoint_direction(ep.bEndpointAddress) ==
                           usb.util.ENDPOINT_IN), None)
        if self.ep_out is None or self.ep_in is None:
            raise RuntimeError("management interface lacks interrupt IN/OUT endpoints")

    def transact(self, request: bytes) -> bytes:
        self.ep_out.write(request, timeout=self.timeout_ms)
        response = bytes(self.ep_in.read(REPORT_SIZE, timeout=self.timeout_ms))
        validate_report(response)
        if response[5] != request[5]:
            raise RuntimeError("response sequence does not match request")
        if response[7] != 0:
            raise RuntimeError(f"device returned result {response[7]}")
        return response

    def topology(self, port: int) -> str:
        # The management device is fixed on internal hub port 5. PyUSB exposes
        # the physical path for platforms whose backend supports it. Presence
        # of a child proves enumeration; absence does not prove disconnection.
        path = tuple(getattr(self.dev, "port_numbers", ()) or ())
        if len(path) < 1 or path[-1] != 5:
            return "unknown"
        target = path[:-1] + (port,)
        for dev in self.usb_core.find(find_all=True) or ():
            if getattr(dev, "bus", None) != getattr(self.dev, "bus", None):
                continue
            child_path = tuple(getattr(dev, "port_numbers", ()) or ())
            if child_path[:len(target)] == target:
                return "enumerated"
        return "unknown"


def _number(text: str) -> int:
    return int(text, 0)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="control a programmable USB hub")
    p.add_argument("--vid", type=_number, help="assigned USB vendor ID")
    p.add_argument("--pid", type=_number, help="assigned USB product ID")
    p.add_argument("--timeout-ms", type=int, default=1000)
    p.add_argument("--simulate", action="store_true")
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("status", "power-on", "power-off", "data-connect",
                 "data-disconnect", "clear-fault"):
        q = sub.add_parser(name)
        q.add_argument("port", type=int, choices=range(1, 5))
    q = sub.add_parser("power-cycle")
    q.add_argument("port", type=int, choices=range(1, 5))
    q.add_argument("--off-ms", type=int, default=500)
    return p


def run(args) -> dict:
    if args.simulate:
        backend = SimBackend()
    else:
        if args.vid is None or args.pid is None:
            raise RuntimeError("--vid and --pid are required for real hardware")
        backend = PyUsbBackend(args.vid, args.pid, args.timeout_ms)
    seq = 1
    payload = b""
    opcode = Opcode.GET_PORT
    if args.command == "power-on":
        opcode, payload = Opcode.SET_POWER, b"\x01"
    elif args.command == "power-off":
        opcode, payload = Opcode.SET_POWER, b"\x00"
    elif args.command == "power-cycle":
        opcode, payload = Opcode.POWER_CYCLE, struct.pack("<I", args.off_ms)
    elif args.command == "data-connect":
        opcode, payload = Opcode.SET_DATA, b"\x01"
    elif args.command == "data-disconnect":
        opcode, payload = Opcode.SET_DATA, b"\x00"
    elif args.command == "clear-fault":
        opcode = Opcode.CLEAR_FAULT
    response = backend.transact(encode_command(opcode, seq, args.port, payload))
    status = decode_port_status(response)
    result = dict(status.__dict__)
    result["attach_enumeration"] = backend.topology(args.port)
    return result


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        print(json.dumps(run(args), indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"phubctl: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
