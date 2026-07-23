#!/usr/bin/env python3
"""tie_efuse_ep.py — board-side EP GND tie for U_EFUSE (P1-A, 2026-07-23).

The converter emits U_EFUSE pin 9 (EP) = GND into the netlist (from the part.yaml
`tie: GND` annotation), so generate_board gives PAD "9" the GND net. But the
KiCad WSON-8-1EP footprint also carries TWO UNNAMED (`""`) SMD sub-pads inside the
EP outline — they have no pad number, so no netlist node reaches them and they
stay net-less. Net-less foreign copper blocks every GND thermal via in the EP
(via_site_ok refuses). This step assigns those unnamed EP sub-pads to GND so the
whole exposed pad is one GND island and power_stitch can drop the thermal vias.

Unnamed pads are NOT parity-checked (no pad name to match a schematic pin), so this
has ZERO schematic-parity impact — verified: the pad-9 tie alone already resolves
parity via the converter; these sub-pads add nothing to the netlist comparison.
Idempotent. Runs AFTER generate_board, BEFORE the KRT import/stitch chain.

Usage: /usr/bin/python3 tie_efuse_ep.py <project-root>   (cwd default)
"""
import sys
from pathlib import Path
import pcbnew


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    root = Path(argv[0]) if argv else Path(".")
    pcbs = list((root / "04_kicad").glob("*.kicad_pcb"))
    pcbs = [p for p in pcbs if not p.name.endswith(".failed")]
    if len(pcbs) != 1:
        sys.exit(f"tie_efuse_ep: expected exactly one 04_kicad/*.kicad_pcb, found {len(pcbs)}")
    board_p = pcbs[0]
    b = pcbnew.LoadBoard(str(board_p))
    fp = b.FindFootprintByReference("U_EFUSE")
    if fp is None:
        print("tie_efuse_ep: no U_EFUSE on board — no-op")
        return 0
    gnd = b.FindNet("GND")
    if gnd is None:
        sys.exit("tie_efuse_ep: board has no GND net")
    # EP outline centre (footprint-relative pad 9 sits at the body centre)
    ep = next((p for p in fp.Pads() if p.GetNumber() == "9"), None)
    if ep is None:
        print("tie_efuse_ep: U_EFUSE has no pad '9' (EP) — netlist EP tie missing; no-op")
        return 0
    ex, ey = ep.GetPosition().x, ep.GetPosition().y
    ew, eh = ep.GetSizeX(), ep.GetSizeY()
    tied = 0
    for p in fp.Pads():
        if p.GetNumber():                       # numbered pads keep their netlist net
            continue
        dx, dy = abs(p.GetPosition().x - ex), abs(p.GetPosition().y - ey)
        if dx <= ew and dy <= eh and p.GetNetname() != "GND":   # inside the EP, net-less
            p.SetNet(gnd)
            tied += 1
    if tied:
        b.Save(str(board_p))
    print(f"tie_efuse_ep: tied {tied} unnamed EP sub-pad(s) of U_EFUSE -> GND "
          f"(EP pad 9 net = {ep.GetNetname()!r})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
