#!/usr/bin/env python3
"""v1.1 post-stitch geometry fixes (runs AFTER stitch, BEFORE final generate_rules).
Reproducible, verified (pcb_toolkit exact-collide). Every added via is checked for
copper clearance AND true hole-to-hole spacing vs every existing drill (vias + PTH
pads), so it never stacks on a connector pad or another via.
  1. EP thermal via arrays: >=4x GND vias under U2/U11/U13 EPs (canon R6).
  2. VBAT_F F.Cu<->B.Cu stitch vias (input-trunk copper doubling) — in-copper both layers.
  3. via-drill floor 0.3mm (escape-A* toolkit default is 0.2 -> STANDARD fail).
  4. track-width nm-rounding floor (KRT emits 0.1998 for a 0.2 rule).
  5. GND fill-island bonding — only islands NOT already bonded by a same-net via or PTH pad.
  6. v1.6 USB-C delivery-corner via density (F2 pads, PMID pour, J5 VBUS pairs).
  (7. PowerPAK EP paste window-pane moved to a VENDORED footprint — see the note below.)
"""
import sys, math
sys.path.insert(0, '/home/mouse9911/gits/circuits/skills/kicad-pcb/scripts')
import pcbnew
from pcb_toolkit import Toolkit
BOARD='04_kicad/usb_hub_3s_v2.kicad_pcb'
VS,VD=0.45,0.3
H2H=0.5           # STANDARD hole-to-hole floor
NEWR=VD/2.0       # new via drill radius

def load():
    b=pcbnew.LoadBoard(BOARD); return b, Toolkit(b,0.15)

def holes(b):
    """(x,y,drill_radius) for every drilled feature (vias + PTH/NPTH pads)."""
    out=[]
    for t in b.GetTracks():
        if t.GetClass()=='PCB_VIA':
            p=t.GetPosition(); out.append((p.x/1e6,p.y/1e6,t.GetDrill()/2e6))
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetDrillSize().x>0:
                pos=p.GetPosition(); out.append((pos.x/1e6,pos.y/1e6,p.GetDrillSize().x/2e6))
    return out

def h2h_ok(x,y,hs):
    for hx,hy,hr in hs:
        if math.hypot(x-hx,y-hy) < H2H + NEWR + hr - 1e-6:
            return False
    return True

b,tk=load()
GND=b.FindNet("GND"); VBATF=b.FindNet("VBAT_F")
for z in b.Zones(): z.UnFill()   # via_site_ok sees pads/tracks only; pours void around new vias on refill
hs=holes(b)

# ---- 1. EP thermal via arrays (v1.2: U13 eFuse GONE -> only the two LM5116 EPs) ----
for ref,cx,cy in [("U2",60,38),("U11",60,76)]:
    n=0
    for dx in (-0.85,0.85):
        for dy in (-2.1,0.0,2.1):
            x,y=round(cx+dx,3),round(cy+dy,3)
            if not h2h_ok(x,y,hs): continue
            if tk.via_site_ok(x,y,GND.GetNetCode(),size=VS,drill=VD):
                tk.add_via(x,y,GND,size=VS,drill=VD); hs.append((x,y,NEWR)); n+=1
    print(f"  EP {ref}: +{n} thermal vias")

# ---- 2. VBAT_F F<->B stitch vias ----
# Board is UNFILLED here: an unbonded B.Cu VBAT_F pour would be pruned at fill
# (isolated island) before we can via it. Check the zone OUTLINE via its real
# LayerSet (GetLayerName mislabels a B.Cu zone as F.Cu). The via bonds F<->B; the
# DRC refill then keeps the B.Cu pour (now connected).
def in_vbatf(x,y):
    pt=pcbnew.VECTOR2I(int(x*1e6),int(y*1e6)); layers=set()
    for z in b.Zones():
        if z.GetNetCode()!=VBATF.GetNetCode(): continue
        if z.Outline().Collide(pt):
            for l in z.GetLayerSet().Seq(): layers.add(b.GetLayerName(l))
    return ("F.Cu" in layers) and ("B.Cu" in layers)
vb=0
for x,y in [(43.0,57.5),(41.0,60.5),(38.5,62.5),(35.3,64.6),(35.3,67.4),(45.5,60.8),(40.0,58.0)]:
    if not h2h_ok(x,y,hs): continue
    if not in_vbatf(x,y): continue
    if tk.via_site_ok(x,y,VBATF.GetNetCode(),size=VS,drill=VD):
        tk.add_via(x,y,VBATF,size=VS,drill=VD); hs.append((x,y,NEWR)); vb+=1
print(f"  VBAT_F: +{vb} F<->B stitch vias (in-copper verified)")

# ---- 3. via-drill floor 0.3 (no GetWidth on vias) ----
dfix=0
for t in b.GetTracks():
    if t.GetClass()=='PCB_VIA' and 0 < t.GetDrill()/1e6 < 0.2999:
        t.SetDrill(pcbnew.FromMM(0.3)); dfix+=1
print(f"  via-drill floor 0.3: {dfix}")

# ---- 4. track-width nm-rounding floor ----
wfix=0
for t in b.GetTracks():
    if t.GetClass()=='PCB_TRACK':
        w=t.GetWidth()/1e6; nice=round(w,1)
        if nice>w and (nice-w)<0.01: t.SetWidth(pcbnew.FromMM(nice)); wfix+=1
print(f"  track-width round-up: {wfix}")
b.Save(BOARD)

# ---- 5. GND fill-island bonding: only islands with NO same-net via AND NO same-net PTH pad ----
b,tk=load(); GND=b.FindNet("GND")
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
hs=holes(b)
gvias=[(x,y) for x,y,r in [(t.GetPosition().x/1e6,t.GetPosition().y/1e6,0) for t in b.GetTracks() if t.GetClass()=='PCB_VIA' and t.GetNetCode()==GND.GetNetCode()]]
gpads=[(p.GetPosition().x/1e6,p.GetPosition().y/1e6) for fp in b.GetFootprints() for p in fp.Pads()
       if p.GetDrillSize().x>0 and p.GetNetCode()==GND.GetNetCode()]
gnd_added=0
for z in b.Zones():
    if z.GetNetCode()!=GND.GetNetCode() or z.GetLayerName() not in ("F.Cu","B.Cu"): continue
    for lid in z.GetLayerSet().CuStack():
        poly=z.GetFilledPolysList(lid)
        for i in range(poly.OutlineCount()):
            sp=pcbnew.SHAPE_POLY_SET(); sp.AddOutline(poly.Outline(i))
            bb=sp.BBox(); area=(bb.GetWidth()/1e6)*(bb.GetHeight()/1e6)
            if area<1.5: continue
            inside=lambda px,py: sp.Collide(pcbnew.VECTOR2I(int(px*1e6),int(py*1e6)))
            if any(inside(px,py) for px,py in gvias): continue      # via bonds it
            if any(inside(px,py) for px,py in gpads): continue      # PTH pad barrel bonds it
            cxx,cyy=(bb.GetLeft()+bb.GetRight())/2e6,(bb.GetTop()+bb.GetBottom())/2e6
            done=False
            for r in (0,0.4,0.8,1.2):
                for a in range(0,360,30):
                    x=round(cxx+r*math.cos(math.radians(a)),2); y=round(cyy+r*math.sin(math.radians(a)),2)
                    if not inside(x,y) or not h2h_ok(x,y,hs): continue
                    if tk.via_site_ok(x,y,GND.GetNetCode(),size=VS,drill=VD):
                        tk.add_via(x,y,GND,size=VS,drill=VD); hs.append((x,y,NEWR)); gnd_added+=1; done=True
                        print(f"  GND island {z.GetLayerName()} ({round(cxx,1)},{round(cyy,1)}) a={round(area,1)} -> bonded @({x},{y})"); break
                if done: break
print(f"  GND island bonds: +{gnd_added}")
b.Save(BOARD)

# ---- 6. v1.6 USB-C DELIVERY-CORNER via density ----------------------------
# MEASURED on sealed v1.5: PMID carried the whole 5 A with TWO vias between its
# F.Cu and B.Cu pours; F2 (0.775 W at 5 A) had ZERO vias on either pad (nearest
# 1.830 / 0.955 mm away); and no J5 VBUS contact pair had a same-net via nearer
# than 1.429 mm. None of that is a hard ampacity failure -- Q6.S -> F2.1 -> J5 is
# a continuous F.Cu path, so the vias only carry B.Cu's PARALLEL share -- but it
# means the second copper layer under this corner was decorative, and it is why
# the RL-2 mesh solve read 4.914 mOhm across PMID alone.
# Sites are DERIVED FROM PAD GEOMETRY on the live board, not hardcoded: a
# hardcoded list silently stops being in the pad the first time placement moves.
b, tk = load()
for z in b.Zones():
    z.UnFill()
hs = holes(b)

def pad_of(ref, num):
    fp = b.FindFootprintByReference(ref)
    if not fp:
        return None
    for p in fp.Pads():
        if p.GetNumber() == num:
            return p
    return None

def in_zone_both(x, y, net):
    """Is (x,y) inside a same-net zone OUTLINE on BOTH F.Cu and B.Cu?

    THIS GUARD IS NOT OPTIONAL. via_site_ok checks CLEARANCE -- it answers "may a
    via go here", not "is there anything here to connect to" -- and the board is
    deliberately UNFILLED at this point so that pours void around the new vias on
    refill. Without this, three VBUSC vias landed in the pour-free CC/data column
    at x118.2-122.3 and came back as 3 via_dangling + 3 unconnected: vias bonding
    nothing to nothing. Same test fix 2 already applies to VBAT_F."""
    pt = pcbnew.VECTOR2I(int(x * 1e6), int(y * 1e6))
    layers = set()
    for z in b.Zones():
        if z.GetNetCode() != net.GetNetCode():
            continue
        if z.Outline().Collide(pt):
            for l in z.GetLayerSet().Seq():
                layers.add(b.GetLayerName(l))
    return ("F.Cu" in layers) and ("B.Cu" in layers)

def place(net, sites, want, label, require_pour=True):
    n = 0
    for x, y in sites:
        if n >= want:
            break
        x, y = round(x, 3), round(y, 3)
        if not h2h_ok(x, y, hs):
            continue
        if require_pour and not in_zone_both(x, y, net):
            continue
        if tk.via_site_ok(x, y, net.GetNetCode(), size=VS, drill=VD):
            tk.add_via(x, y, net, size=VS, drill=VD)
            hs.append((x, y, NEWR))
            n += 1
    print(f"  {label}: +{n} via(s) (wanted {want})")
    return n

PMIDN, VBUSCN = b.FindNet("PMID"), b.FindNet("VBUSC")

# (a) F2 pad thermal/current vias — a column inside each pad, inset from its edge
for num, net, lbl in (("1", PMIDN, "F2.1 (PMID)"), ("2", VBUSCN, "F2.2 (VBUSC)")):
    p = pad_of("F2", num)
    if p is None:
        print(f"  F2.{num}: pad not found — SKIPPED")
        continue
    px, py = p.GetPosition().x / 1e6, p.GetPosition().y / 1e6
    ph = p.GetSize().y / 1e6
    span = ph / 2.0 - (VS / 2.0 + 0.30)          # keep the annulus off the pad edge
    place(net, [(px, py + f * span) for f in (-1.0, -0.34, 0.34, 1.0)], 4, lbl,
          require_pour=False)   # inside the pad itself: the pad IS the copper

# (b) PMID pour F<->B bonding — a grid over the PMID island, skipping pad sites
place(PMIDN, [(x, y) for x in (106.6, 108.0, 109.4, 110.8)
              for y in (88.6, 90.0, 91.4, 92.8)], 6, "PMID pour F<->B")

# (c) J5 VBUS contact pairs — march north from each B-row VBUS pad into the pour
for a_pad, b_pad, lbl in (("A4", "B4", "J5 west VBUS pair"),
                          ("A9", "B9", "J5 east VBUS pair")):
    p = pad_of("J5", b_pad) or pad_of("J5", a_pad)
    if p is None:
        print(f"  {lbl}: pad not found — SKIPPED")
        continue
    px, py = p.GetPosition().x / 1e6, p.GetPosition().y / 1e6
    sites = [(px + dx, py - dy) for dy in (1.6, 2.2, 2.8, 3.4, 4.0, 4.6, 5.2, 5.8, 6.4)
             for dx in (0.0, -0.9, 0.9, -1.8, 1.8, -2.7, 2.7)]
    place(VBUSCN, sites, 3, lbl)

# REFILL BEFORE THE LAST SAVE. THIS IS THE v1.6 REGRESSION.
#
# Section 6 was added in v1.6 and copied the `UnFill()` idiom from sections
# 1-5 — which is correct, `via_site_ok` must see pads/tracks without pour in
# the way — but it never restored the fill. Section 5 refills (line ~98) and
# then saves; section 6 unfilled, placed vias, and saved. It is the LAST save
# in this file, so the board hit disk with 51 zones and ZERO filled_polygon.
#
# v1.6, v1.7 and v1.8 all shipped that way: 44287.91 mm2 of missing copper,
# G36 region count 0 on F_Cu/In1_Cu/In2_Cu/B_Cu, every gate green — because
# `kicad-cli pcb drc --refill-zones` REFILLS IN MEMORY and returns 0/0/0 on a
# board whose saved file has no fill, and nothing had ever read the gerbers.
#
# The generic guard is `route_and_stitch_generic.verify_saved_fill()`, but that
# runs inside the stitch driver and THIS SCRIPT RUNS AFTER IT — so rebuild_all.sh
# now calls `route_and_stitch_generic.py verify-fill` after the last board write.
# Canon M-SHIP/M-WIDTH, ADR-0004.
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(BOARD)
print(f"refilled {sum(1 for z in b.Zones() if not z.GetIsRuleArea())} pour "
      f"zone(s) before the final save")

# ---- 7. PowerPAK EP paste window-pane -> MOVED OUT OF THIS FILE ------------
# It was implemented here first, per-instance, so each aperture could be shrunk
# around whatever vias actually landed in that FET's drain pad. That produced
# valid geometry (50.7-65.0% across the six) and SIX lib_footprint_mismatch DRC
# violations, because a per-instance footprint edit is by definition a board that
# no longer matches its library.
# It now lives where it belongs: a VENDORED footprint,
# 03_src/lib/Package_SO.pretty/PowerPAK_SO-8_Single.kicad_mod, carrying a fixed
# 2x2 array at 65% AREA. Board and library then agree, the geometry is identical
# on all six devices, and it is regenerable from 03_src like everything else.
# The via question resolves itself: the in-pad vias on Q2/Q4 are VIN pad_rescue
# drops to the In2 plane -- i.e. they are how the drain reaches its plane, not
# strays -- and every one of them is TENTED on both faces (measured), so paste
# sits on mask, not on an open barrel. The 65% ratio is not invented here: it is
# exactly what KiCad's own HTSSOP-20-1EP_4.4x6.5mm_..._Mask2.75x3.43mm uses for
# this same package family (4 x 1.11 x 1.38 = 6.127 mm2 over 2.75 x 3.43 =
# 9.4325 mm2 = 65.0%), which is an authority outside this repo (canon M1).
print("post_stitch_fixes: done")
