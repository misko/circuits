#!/usr/bin/env python3
"""Netlist parity gate: the exported KiCad netlist must match the design
table node-for-node (03_src contract; schematic-generation.md)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_schematic import build  # noqa: E402
from schwriter import verify_netlist_parity  # noqa: E402

PROJ = Path(__file__).resolve().parent.parent
NET = PROJ / "06_build" / "netlists" / "xt60-usb-supply.net"

print("NETLIST PARITY:", verify_netlist_parity(NET, build()))
