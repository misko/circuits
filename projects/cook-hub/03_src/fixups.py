#!/usr/bin/env python3
"""Deterministic engineered rescues that the generic stitch ring cannot
reach (U7 pocket, post D-FIX footprint swap): named pour-bond via + stub
per pad, every element exact-collide green-checked at run time; hard error
if a site is no longer valid (so a route change surfaces loudly instead of
shipping an open). Runs after stitch_and_fill in rebuild_all."""
import math
import os
import sys
from pathlib import Path

_sk = [p for p in (Path(__file__).resolve().parents[3] / "skills" / "kicad-pcb" / "scripts",
                   Path(os.path.expanduser("~/.claude/skills/kicad-pcb/scripts"))) if p.is_dir()]
sys.path.insert(0, str(_sk[0]))
import pcbnew  # noqa: E402
from pcb_toolkit import Toolkit  # noqa: E402

HERE = Path(__file__).parent
PCB = str(HERE.parent / "04_kicad" / "cook_hub.kicad_pcb")
b = pcbnew.LoadBoard(PCB)
tk = Toolkit(b, 0.15)
MM = pcbnew.ToMM

# (ref, pad, via_x, via_y, stub_w): sites probed green 2026-07-19 on the
# v1.0 chain (In2 3V3 pour coverage + via_site_ok + stub corridor).
FIXUPS = [
    ("U7", "3", 63.80, 110.33, 0.3),
    ("R21", "2", 67.96, 114.03, 0.3),   # 69.03,114.93 tripped hole_to_hole
]

# dangling-trunk re-terminations: (net, loose_x, loose_y, ref, pad) — extend
# the frayed trunk end onto the named pad (rounding left it 0.05-0.3mm shy).
EXTENDS = [
    ("3V3", 60.70, 122.00, "C15", "1"),
]

pours = {}
for z in b.Zones():
    if z.IsOnLayer(pcbnew.In2_Cu):
        pours.setdefault(z.GetNetname(), z)

changed = False
fail = []
for ref, pn, vx, vy, w in FIXUPS:
    fp = b.FindFootprintByReference(ref)
    p = next(pp for pp in fp.Pads() if pp.GetNumber() == pn)
    px, py = MM(p.GetPosition().x), MM(p.GetPosition().y)
    net = p.GetNet()
    # already served?
    served = any(t.GetClass() == "PCB_TRACK" and t.GetNetCode() == p.GetNetCode()
                 and any(abs(MM(e.x) - px) < 0.4 and abs(MM(e.y) - py) < 0.4
                         for e in (t.GetStart(), t.GetEnd()))
                 for t in b.GetTracks())
    if served:
        print(f"fixup {ref}.{pn}: already served")
        continue
    z = pours.get(net.GetNetname())
    ps = z.GetFilledPolysList(pcbnew.In2_Cu) if z else None
    if ps is None or not ps.Contains(pcbnew.VECTOR2I_MM(round(vx, 2), round(vy, 2))):
        fail.append(f"{ref}.{pn}: site ({vx},{vy}) not on {net.GetNetname()} In2 fill")
        continue
    if not tk.via_site_ok(vx, vy, net.GetNetCode(), size=0.6, drill=0.3):
        fail.append(f"{ref}.{pn}: via site blocked at ({vx},{vy})")
        continue
    lay = p.GetLayer() if p.GetLayer() in (pcbnew.F_Cu, pcbnew.B_Cu) else pcbnew.F_Cu
    if tk.collides(px, py, vx, vy, w, net.GetNetCode(), lay) is not None:
        fail.append(f"{ref}.{pn}: stub corridor blocked")
        continue
    tk.add_via(vx, vy, net, size=0.6, drill=0.3)
    tk.add_seg(px, py, vx, vy, net, lay, w)
    changed = True
    print(f"fixup {ref}.{pn}: via ({vx},{vy}) + stub OK")

for net_name, lx, ly, ref, pn in EXTENDS:
    fp = b.FindFootprintByReference(ref)
    p = next(pp for pp in fp.Pads() if pp.GetNumber() == pn)
    px, py = MM(p.GetPosition().x), MM(p.GetPosition().y)
    tgt = None
    for t in b.GetTracks():
        if t.GetClass() != "PCB_TRACK" or t.GetNetname() != net_name:
            continue
        for e_get, e_set in ((t.GetStart, t.SetStart), (t.GetEnd, t.SetEnd)):
            e = e_get()
            if abs(MM(e.x) - lx) < 0.12 and abs(MM(e.y) - ly) < 0.12:
                tgt = (t, e_set, MM(t.GetWidth()))
    if tgt is None:
        print(f"extend {ref}.{pn}: loose end not found (already fixed?)")
        continue
    t, setter, w = tgt
    if tk.collides(lx, ly, px, py, w, p.GetNetCode(),
                   t.GetLayer()) is not None:
        fail.append(f"extend {ref}.{pn}: corridor blocked")
        continue
    setter(pcbnew.VECTOR2I_MM(px, py))
    changed = True
    print(f"extend {ref}.{pn}: trunk end ({lx},{ly}) -> pad ({px:.2f},{py:.2f})")

if fail:
    print("FIXUP FAILURES:\n  " + "\n  ".join(fail))
    sys.exit(1)
if changed:
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    b.Save(PCB)
print("fixups done")
