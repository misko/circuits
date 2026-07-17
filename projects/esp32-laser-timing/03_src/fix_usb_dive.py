#!/usr/bin/env python3
"""Surgical post-import fix: KRT's multi-point tap phase always joins the
USB_DP pad pair (J1 A6+B6, interleaved with DM at 0.5mm pitch) with a
0.3/0.2 micro-via ON pad A6 — below the JLC 2-layer standard drill floor
(P10: default 2-layer rules). No legal via fits inside the pad column, so
this script relocates the dive into the corridor route_prep reserves on
User.2 (x 58.85-59.65, y 65.85-66.65):
  pad A6 -> F stub east -> 0.45/0.3 via -> B.Cu diagonal -> the existing
  0.45 via at the west path. Every added item is collide-checked; exits 1
  loudly if the router topology changed and the fix no longer applies."""
import os, sys, math
from pathlib import Path
_sk = [p for p in (Path(__file__).resolve().parents[3] / "skills" / "kicad-pcb" / "scripts",
                   Path(os.path.expanduser("~/.claude/skills/kicad-pcb/scripts"))) if p.is_dir()]
sys.path.insert(0, str(_sk[0]))
import pcbnew
from pcb_toolkit import Toolkit

PCB = str(Path(__file__).parent.parent / "04_kicad" / "esp32_laser_timing.kicad_pcb")
b = pcbnew.LoadBoard(PCB)

# locate the offending micro via (sub-0.44, on the USB_DP net, at a J1 pad)
j1 = b.FindFootprintByReference("J1")
pads = {p.GetNumber(): p for p in j1.Pads()}
micro = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"
         and t.GetNetname() in ("USB_DP", "USB_DM")
         and t.GetWidth() < pcbnew.FromMM(0.44)]
if not micro:
    print("fix_usb_dive: no micro via - nothing to do")
    sys.exit(0)
if len(micro) != 1:
    sys.exit(f"fix_usb_dive: expected 1 micro via, found {len(micro)} - re-derive the fix")
v2 = micro[0]
net = v2.GetNetCode()
netinfo = v2.GetNet()
vx, vy = v2.GetPosition().x / 1e6, v2.GetPosition().y / 1e6

# the B.Cu jog attached to it (endpoint within 0.1mm of the via)
jog = None
for t in b.GetTracks():
    if t.GetClass() == "PCB_TRACK" and t.GetNetCode() == net and t.GetLayer() == pcbnew.B_Cu:
        for e in (t.GetStart(), t.GetEnd()):
            if math.hypot(e.x / 1e6 - vx, e.y / 1e6 - vy) < 0.12:
                jog = t
if jog is None:
    sys.exit("fix_usb_dive: no B.Cu jog at the micro via - topology changed, re-derive")
far = jog.GetStart() if math.hypot(jog.GetEnd().x / 1e6 - vx, jog.GetEnd().y / 1e6 - vy) < 0.12 \
    else jog.GetEnd()
fx, fy = far.x / 1e6, far.y / 1e6  # the far anchor (the legal 0.45 via site)

b.Remove(v2)
b.Remove(jog)
tk = Toolkit(b, 0.127)

DIVE = (59.15, 66.25)
if abs(vy - DIVE[1]) > 0.6:
    sys.exit(f"fix_usb_dive: micro via at y={vy}, corridor at y={DIVE[1]} - re-derive")
ok = True
if tk.collides(vx, vy, DIVE[0], DIVE[1], 0.2, net, pcbnew.F_Cu):
    ok = False
if ok and not tk.via_site_ok(DIVE[0], DIVE[1], net, size=0.45, drill=0.3):
    ok = False
if ok and tk.collides(DIVE[0], DIVE[1], fx, fy, 0.2, net, pcbnew.B_Cu):
    ok = False
if not ok:
    sys.exit("fix_usb_dive: corridor blocked - keepout failed, re-derive")
tk.add_seg(vx, vy, DIVE[0], DIVE[1], netinfo, pcbnew.F_Cu, 0.2)
tk.add_via(DIVE[0], DIVE[1], netinfo, size=0.45, drill=0.3)
tk.add_seg(DIVE[0], DIVE[1], fx, fy, netinfo, pcbnew.B_Cu, 0.2)
b.Save(PCB)
print(f"fix_usb_dive: relocated dive pad({vx},{vy}) -> via{DIVE} -> B({fx},{fy})")
