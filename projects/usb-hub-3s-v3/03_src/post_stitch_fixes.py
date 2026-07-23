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

# ---- 1. EP thermal via arrays ----
for ref,cx,cy in [("U2",60,38),("U11",60,76),("U13",113,92)]:
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
print("post_stitch_fixes: done")
