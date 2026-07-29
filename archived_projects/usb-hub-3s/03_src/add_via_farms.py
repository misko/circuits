#!/usr/bin/env /usr/bin/python3
"""v1.1 via program (X22/X23): declared via farms + thermal arrays.

Runs between `taps` and `stitch` (rebuild_all step [8b]): loads the project
board, adds each configured via with its net, skips sites that already have
a via within 0.25mm (idempotent re-runs), refuses sites that collide with
copper of ANOTHER net on F/B (measured against pads and tracks, 0.2mm
clearance) so a KRT track can never be silently shorted. Fill (stitch)
bonds the barrels to the zones afterwards; the DRC gate remains the judge.
"""
import sys, math
from pathlib import Path
import yaml
import pcbnew

ROOT = Path(__file__).resolve().parent.parent
CFG = yaml.safe_load(open(ROOT / "03_src/via_farms.yaml"))
BOARD = ROOT / "04_kicad/usb_hub_3s.kicad_pcb"

b = pcbnew.LoadBoard(str(BOARD))
nets = b.GetNetsByName()
mm = pcbnew.FromMM
tomm = pcbnew.ToMM
size = float(CFG["via"]["size"]); drill = float(CFG["via"]["drill"])

existing = [(t.GetPosition().x, t.GetPosition().y) for t in b.GetTracks()
            if t.Type() == pcbnew.PCB_VIA_T]

def clear_of_foreign_copper(x, y, netcode):
    """No pad/track of another net within (size/2 + 0.2) on outer layers."""
    r = mm(size / 2 + 0.2)
    p = pcbnew.VECTOR2I(int(x), int(y))
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetCode() == netcode:
                continue
            if pad.HitTest(p, r):
                return False
    for t in b.GetTracks():
        if t.GetNetCode() == netcode or t.Type() == pcbnew.PCB_VIA_T:
            continue
        if t.HitTest(p, r):
            return False
    return True

added = skipped = refused = 0
for farm in CFG["farms"]:
    netname = farm["net"]
    ni = nets.find(netname)
    if ni == nets.end():
        sys.exit(f"via_farms: net {netname!r} not on board")
    netcode = ni.value()[1].GetNetCode()
    for (xm, ym) in farm["points"]:
        x, y = mm(xm), mm(ym)
        if any(math.hypot(x - ex, y - ey) < mm(0.25) for ex, ey in existing):
            skipped += 1
            continue
        if not clear_of_foreign_copper(x, y, netcode):
            print(f"  REFUSED {netname} via at ({xm},{ym}): foreign copper in range")
            refused += 1
            continue
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(x, y))
        v.SetWidth(mm(size)); v.SetDrill(mm(drill))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNetCode(netcode)
        b.Add(v)
        existing.append((x, y))
        added += 1
pcbnew.SaveBoard(str(BOARD), b)
print(f"via_farms: +{added} vias ({size}/{drill}), {skipped} already present, {refused} refused")
if refused:
    sys.exit(1)
