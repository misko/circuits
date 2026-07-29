#!/usr/bin/env /usr/bin/python3
"""v1.1 deterministic stub emitter (see seed_stubs.yaml header).

Same discipline as add_via_farms.py: fixed geometry, collision REFUSAL
against copper of any other net (pads and tracks, both outer layers,
0.13mm clearance), idempotent. DRC remains the judge.
"""
import sys, math
from pathlib import Path
import yaml
import pcbnew

ROOT = Path(__file__).resolve().parent.parent
CFG = yaml.safe_load(open(ROOT / "03_src/seed_stubs.yaml"))
BOARD = ROOT / "04_kicad/usb_hub_3s.kicad_pcb"
CLR = 0.13

b = pcbnew.LoadBoard(str(BOARD))
nets = b.GetNetsByName()
mm = pcbnew.FromMM
LAYER = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu}

def seg_conflicts(x1, y1, x2, y2, w, lid, netcode):
    """Any foreign pad/track within w/2+CLR of the segment on its layer?"""
    hull = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(x1, y1), pcbnew.VECTOR2I(x2, y2), mm(w))
    margin = mm(CLR)
    hits = []
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetCode() == netcode:
                continue
            if not pad.IsOnLayer(lid):
                continue
            if pad.GetEffectiveShape(lid).Collide(hull, margin):
                hits.append(f"pad {fp.GetReference()}.{pad.GetPadName()} [{pad.GetNetname()}]")
    for t in b.GetTracks():
        if t.GetNetCode() == netcode:
            continue
        if t.Type() == pcbnew.PCB_VIA_T or t.IsOnLayer(lid):
            if t.GetEffectiveShape(lid).Collide(hull, margin):
                hits.append(f"{'via' if t.Type()==pcbnew.PCB_VIA_T else 'track'} [{t.GetNetname()}]")
    return hits

added = refused = 0
for stub in CFG["stubs"]:
    ni = nets.find(stub["net"])
    if ni == nets.end():
        sys.exit(f"seed_stubs: net {stub['net']!r} not on board")
    netcode = ni.value()[1].GetNetCode()
    plan = []
    ok = True
    for seg in stub["segments"]:
        lid = LAYER[seg["layer"]]
        w = float(seg["width"])
        pts = seg["pts"]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            x1, y1, x2, y2 = mm(ax), mm(ay), mm(bx), mm(by)
            hits = seg_conflicts(x1, y1, x2, y2, w, lid, netcode)
            if hits:
                print(f"  REFUSED {stub['net']} seg ({ax},{ay})->({bx},{by}) {seg['layer']}: " + "; ".join(hits[:4]))
                ok = False
            plan.append(("seg", x1, y1, x2, y2, w, lid))
    for (vx, vy) in stub.get("vias", []):
        plan.append(("via", mm(vx), mm(vy)))
    if not ok:
        refused += 1
        continue
    for item in plan:
        if item[0] == "seg":
            _, x1, y1, x2, y2, w, lid = item
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(pcbnew.VECTOR2I(x1, y1)); t.SetEnd(pcbnew.VECTOR2I(x2, y2))
            t.SetWidth(mm(w)); t.SetLayer(lid); t.SetNetCode(netcode)
            b.Add(t); added += 1
        else:
            _, x, y = item
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(pcbnew.VECTOR2I(x, y))
            v.SetWidth(mm(float(CFG["via"]["size"]))); v.SetDrill(mm(float(CFG["via"]["drill"])))
            v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            v.SetNetCode(netcode)
            b.Add(v); added += 1
pcbnew.SaveBoard(str(BOARD), b)
print(f"seed_stubs: +{added} items, {refused} stub-groups refused")
sys.exit(1 if refused else 0)
