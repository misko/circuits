#!/usr/bin/env python3
"""check_port_nets.py — the net-merge gate (P0 class, red-team 2026-07-23).

Two checks, both against the EXPORTED NETLIST (the artifact the board is
actually generated from), catching the failure class where schematic wire
geometry silently merges two nets at `kicad-cli sch export netlist` (observed:
a vertical P5VA_4 wire passed exactly through the AUDIO4M wires' junction at
(280.67,147.955) -> the netlist merged both nets under the name AUDIO4M ->
port 4's +5V-audio pins landed on the ch4 balanced-minus into the ADC, and
every downstream gate (ERC 0, DRC 0/0, count_parity 194==194) stayed green
because they are all self-consistent with the merged netlist):

1. LABEL SURVIVAL (generic): every global_label name in the committed
   converter schematic must exist as a net name in the exported netlist.
   A label swallowed by a geometric merge disappears from the netlist while
   remaining in the schematic text — exactly this class, any net.

2. PORT PIN MAP (brief G2/G14, specific): all 8 RJ45 ports pin-for-pin:
   J pins 1,2 -> AUDIO<n>P/M; 3 -> PLUS5V_BEEP; 6 -> BEEP_RETURN;
   4,7 -> P5VA_<n>; 5,8 -> GND; 9-12 unconnected.

Usage: check_port_nets.py <netlist.net> <converter.kicad_sch>
Exit 0 = both pass; nonzero + findings otherwise.
"""
import re
import sys


def main():
    net_path, sch_path = sys.argv[1], sys.argv[2]
    nl = re.sub(r"\s+", " ", open(net_path).read())
    nets = re.findall(
        r'\(net \(code "[^"]*"\) \(name "([^"]+)"\)(.*?)(?=\(net \(code|\Z)', nl)
    netnames = {n for n, _ in nets}
    pad2net = {}
    for name, body in nets:
        for r, p in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', body):
            pad2net[(r, p)] = name

    bad = []

    # 1. label survival
    sch = open(sch_path).read()
    labels = set(re.findall(r'\(global_label "([^"]+)"', sch))
    lost = sorted(l for l in labels if l not in netnames)
    for l in lost:
        bad.append(f"LABEL-LOST: schematic global_label {l!r} is not a net in "
                   f"the netlist (geometric merge/swallow at export?)")

    # 2. port pin map
    ports = ["J3", "J4", "J5", "J6", "J7", "J8", "J9", "J10"]
    for i, J in enumerate(ports, 1):
        exp = {"1": f"AUDIO{i}P", "2": f"AUDIO{i}M", "3": "PLUS5V_BEEP",
               "6": "BEEP_RETURN", "4": f"P5VA_{i}", "7": f"P5VA_{i}",
               "5": "GND", "8": "GND"}
        for pin, want in exp.items():
            got = pad2net.get((J, pin))
            if got != want:
                bad.append(f"PORT-PIN: {J}.{pin} = {got!r}, want {want!r}")
        for pin in ("9", "10", "11", "12"):
            got = pad2net.get((J, pin), "")
            if got and not got.startswith("unconnected-"):
                bad.append(f"PORT-PIN: {J}.{pin} = {got!r}, want unconnected")

    if bad:
        print(f"check_port_nets: FAIL ({len(bad)} findings)")
        for m in bad:
            print("  " + m)
        return 1
    print(f"check_port_nets: PASS — {len(labels)} labels all survive to the "
          f"netlist; 8 ports pin-for-pin per the brief")
    return 0


if __name__ == "__main__":
    sys.exit(main())
