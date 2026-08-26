#!/usr/bin/env python3
"""RX2CTL/1 reference host utility for Pluto RX2 8-way v4."""

from __future__ import annotations

import argparse
import json
import time


DEFAULTS = {
    "sample_rate_req": 30_000_000,
    "ordinary_clean": 8192,
    "reference_clean": 4096,
    "blank": 128,
}


def parse_response(line: str) -> dict[str, object]:
    fields = line.strip().split()
    if not fields:
        raise RuntimeError("empty device response")
    if fields[0] == "ERR":
        raise RuntimeError(" ".join(fields[1:]))
    if fields[0] != "OK":
        raise RuntimeError(f"bad response prefix: {fields[0]}")
    result: dict[str, object] = {}
    for field in fields[1:]:
        if "=" not in field:
            continue
        key, value = field.split("=", 1)
        if value.isdigit():
            result[key] = int(value)
        else:
            try:
                result[key] = float(value)
            except ValueError:
                result[key] = value
    return result


class SimBackend:
    def __init__(self) -> None:
        self.running = False
        self.muted = False
        self.state = 1
        self.frame = 0
        self.transitions = 0
        self.config = dict(DEFAULTS)

    def transact(self, command: str) -> str:
        fields = command.split()
        if command == "INFO?":
            return ("OK product=pluto-rx2-8way-v4 protocol=RX2CTL/1 "
                    "mcu=RP2040-Zero transport=USB-CDC")
        if fields[:1] == ["SELECT"] and len(fields) == 2:
            state = int(fields[1])
            if state not in range(1, 9):
                return "ERR BAD_STATE expected=1..8"
            self.running, self.muted, self.state = False, False, state
        elif command == "OFF":
            self.running, self.muted = False, True
        elif command == "RUN":
            self.running, self.muted, self.state = True, False, 1
        elif command == "STOP":
            self.running = False
        elif command == "ZERO_COUNTERS":
            self.frame = self.transitions = 0
        elif fields[:1] == ["CONFIG"] and len(fields) == 5:
            rate, ordinary, reference, blank = map(int, fields[1:])
            ordinary_total = ordinary + blank
            reference_total = reference + blank
            frame_total = 7 * ordinary_total + reference_total
            if (min(ordinary, reference, blank) < 0 or
                    rate < 2000 or rate > 50_000_000 or
                    ordinary_total <= 4 or reference_total <= 4 or
                    ordinary_total >= (1 << 28) or
                    reference_total >= (1 << 28) or
                    frame_total > 0xFFFFFFFF):
                return "ERR BAD_CONFIG"
            self.running = False
            self.config.update(sample_rate_req=rate, ordinary_clean=ordinary,
                               reference_clean=reference, blank=blank)
        elif command != "STATUS?":
            return "ERR BAD_COMMAND"
        frame_samples = (7 * (self.config["ordinary_clean"] + self.config["blank"]) +
                         self.config["reference_clean"] + self.config["blank"])
        return (f"OK running={int(self.running)} muted={int(self.muted)} "
                f"state={0 if self.muted else self.state} frame={self.frame} "
                f"transitions={self.transitions} sample_rate_req={self.config['sample_rate_req']} "
                f"sample_rate_actual={float(self.config['sample_rate_req']):.3f} "
                f"blank={self.config['blank']} ordinary_clean={self.config['ordinary_clean']} "
                f"reference_clean={self.config['reference_clean']} frame_samples={frame_samples} "
                "sync=FREE_RUNNING")


class SerialBackend:
    def __init__(self, port: str, baud: int, timeout: float) -> None:
        try:
            import serial
        except ImportError as exc:
            raise RuntimeError("real hardware access requires pyserial") from exc
        self.device = serial.Serial(port, baudrate=baud, timeout=timeout)
        time.sleep(0.1)
        self.device.reset_input_buffer()

    def transact(self, command: str) -> str:
        self.device.write((command + "\n").encode("ascii"))
        response = self.device.readline().decode("ascii", errors="strict").strip()
        if not response:
            raise RuntimeError("device response timed out")
        return response


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="control Pluto RX2 8-way v4")
    p.add_argument("--port", help="USB CDC serial device")
    p.add_argument("--baud", type=int, default=115200)
    p.add_argument("--timeout", type=float, default=1.0)
    p.add_argument("--simulate", action="store_true")
    sub = p.add_subparsers(dest="action", required=True)
    for name in ("info", "status", "off", "run", "stop", "zero-counters"):
        sub.add_parser(name)
    q = sub.add_parser("select")
    q.add_argument("state", type=int, choices=range(1, 9))
    q = sub.add_parser("config")
    q.add_argument("--sample-rate", type=int, default=30_000_000)
    q.add_argument("--ordinary-clean", type=int, default=8192)
    q.add_argument("--reference-clean", type=int, default=4096)
    q.add_argument("--blank", type=int, default=128)
    return p


def command_for(args: argparse.Namespace) -> str:
    if args.action == "info":
        return "INFO?"
    if args.action == "status":
        return "STATUS?"
    if args.action == "select":
        return f"SELECT {args.state}"
    if args.action == "zero-counters":
        return "ZERO_COUNTERS"
    if args.action == "config":
        return (f"CONFIG {args.sample_rate} {args.ordinary_clean} "
                f"{args.reference_clean} {args.blank}")
    return args.action.upper()


def run(args: argparse.Namespace) -> dict[str, object]:
    if args.simulate:
        backend = SimBackend()
    else:
        if not args.port:
            raise RuntimeError("--port is required for real hardware")
        backend = SerialBackend(args.port, args.baud, args.timeout)
    return parse_response(backend.transact(command_for(args)))


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        print(json.dumps(run(args), indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"rx2ctl: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
