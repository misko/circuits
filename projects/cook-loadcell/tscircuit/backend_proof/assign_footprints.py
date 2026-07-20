#!/usr/bin/env python3
"""Phase-3 adapter #2 — assign KiCad footprint FPIDs to the exported netlist.

The TSX authoring layer expresses each part's footprint as a tscircuit
footprinter TOKEN (`0603`, `soic16_p1.27mm`, `pinrow3_p2.5mm`, ...) plus pad
GEOMETRY. The Phase-2 converter kicad_sch reached node-for-node netlist PARITY
on CONNECTIVITY (refdes / pad / net) but left the KiCad `Footprint` field
EMPTY — the parity gate never inspects footprint assignment. generate_board.py,
however, LOADS named KiCad footprints BY FPID (`lib:name`) to place them, so a
netlist with no `(footprint ...)` fails its hard "no footprint" error (correct
behaviour, contracts.md rule 1).

This bridge maps each tscircuit token to its KiCad FPID and injects
`(footprint "lib:name")` into the netlist. It is the exact role schwriter2's
generate_schematic.py `sym_fp`/`ref_fp` play; here the tokens are READ FROM the
authored .tsx, so the footprint identity is TSX-derived, not lifted from the
sealed board. `0603`/`0805` resolve per part CLASS (R vs C) — the same
tscircuit token names different KiCad libraries for a resistor vs a capacitor.

Usage: assign_footprints.py TSX_SRC IN.net OUT.net
"""
import re
import sys

TOKEN_FP = {
    ("R", "0603"): "Resistor_SMD:R_0603_1608Metric",
    ("C", "0603"): "Capacitor_SMD:C_0603_1608Metric",
    ("C", "0805"): "Capacitor_SMD:C_0805_2012Metric",
    ("*", "soic16_p1.27mm"): "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
    ("*", "sot23"): "Package_TO_SOT_SMD:SOT-23",
    ("*", "sod323"): "Diode_SMD:D_SOD-323",
    ("*", "pinrow3_p2.5mm"): "Connector_JST:JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical",
    ("*", "pinrow5_p2.5mm"): "Connector_JST:JST_XH_B5B-XH-A_1x05_P2.50mm_Vertical",
    ("*", "pinrow3"): "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
    ("*", "solderjumper2_bridged12"): "Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm",
    ("*", "testpoint_pad"): "TestPoint:TestPoint_Pad_D1.5mm",
}


def token_for(tsx):
    """refdes -> tscircuit footprint token, parsed from the authored TSX."""
    out = {}
    for m in re.finditer(r'name="([^"]+)"[^>]*?footprint="([^"]+)"', tsx, re.S):
        out[m.group(1)] = m.group(2)
    for m in re.finditer(r'footprint="([^"]+)"[^>]*?name="([^"]+)"', tsx, re.S):
        out.setdefault(m.group(2), m.group(1))
    for m in re.finditer(r'<testpoint\s+name="([^"]+)"[^>]*?footprintVariant="pad"',
                         tsx, re.S):
        out[m.group(1)] = "testpoint_pad"
    return out


def fpid_for(ref, token):
    cls = ref[0] if ref[0] in "RC" else "*"
    for key in ((cls, token), ("*", token)):
        if key in TOKEN_FP:
            return TOKEN_FP[key]
    sys.exit(f"assign_footprints: no KiCad FPID for {ref} token '{token}'")


def main():
    tsx_path, src, dst = sys.argv[1], sys.argv[2], sys.argv[3]
    tok = token_for(open(tsx_path).read())
    s = open(src).read()
    n = 0

    def repl(m):
        nonlocal n
        ref = m.group(1)
        if ref not in tok:
            sys.exit(f"assign_footprints: no TSX footprint token for {ref}")
        n += 1
        return m.group(0) + f'\n\t\t\t(footprint "{fpid_for(ref, tok[ref])}")'

    s = re.sub(r'\(ref "([^"]+)"\)\s*\n\s*\(value "[^"]*"\)', repl, s)
    if n == 0:
        sys.exit("assign_footprints: injected 0 footprints (netlist format drift?)")
    open(dst, "w").write(s)
    print(f"assigned {n} footprints from TSX tokens")


if __name__ == "__main__":
    main()
