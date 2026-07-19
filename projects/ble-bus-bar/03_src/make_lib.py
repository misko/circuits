#!/usr/bin/env python3
"""Emit 03_src/lib/bbar.pretty/ project footprints (deterministic text):

- FuseHolder_Keystone_3557-2 : ATO blade holder, 4 THT pins (2 per clip),
  pattern from Keystone M65 p.41 mounting detail (02_parts/3557-2):
  clip pairs 13.5mm apart along the BLADE axis (we orient blades N-S),
  3.4mm within a pair (E-W); holes dia 1.6mm -> drill 1.7, pad 3.2.
  Body 7.4 x 19.8mm (E-W x N-S here). Pad 1 = south pair (trunk side),
  pad 2 = north pair (VF side).
- R_Shunt_WSLP2726 : 2726 shunt, pads 2.69 x 5.71mm at +-2.465mm from
  center along N-S (datasheet 30179 solder-pad table; rotated so current
  flows N-S). Pad 1 = south (VF), pad 2 = north (VP).
- Lug_M5 / Lug_M4 : bolted ring-lug studs — single plated hole
  (5.3/4.3mm drill) with a fat annulus (13/11mm) on both layers
  (ADR-0005). THT pad both sides = the layer-bonding joint.

No FootprintLoad/Save (SWIG traps) — plain s-expr text, KiCad 7+ format.
Run: python3 03_src/make_lib.py
"""
from pathlib import Path

HERE = Path(__file__).parent
LIB = HERE / "lib" / "bbar.pretty"
LIB.mkdir(parents=True, exist_ok=True)


def header(name, descr):
    return (f'(footprint "{name}" (version 20221018) (generator make_lib)\n'
            f'  (layer "F.Cu") (descr "{descr}") (attr through_hole)\n')


def tht_pad(num, x, y, size, drill, shape="circle"):
    return (f'  (pad "{num}" thru_hole {shape} (at {x:.3f} {y:.3f}) '
            f'(size {size:.2f} {size:.2f}) (drill {drill:.2f}) '
            f'(layers "*.Cu" "*.Mask") (remove_unused_layers no))\n')


def smd_pad(num, x, y, w, h):
    return (f'  (pad "{num}" smd rect (at {x:.3f} {y:.3f}) '
            f'(size {w:.2f} {h:.2f}) (layers "F.Cu" "F.Paste" "F.Mask"))\n')


def silk_rect(x0, y0, x1, y1, layer="F.SilkS", w=0.15):
    out = ""
    for (ax, ay, bx, by) in [(x0, y0, x1, y0), (x1, y0, x1, y1),
                             (x1, y1, x0, y1), (x0, y1, x0, y0)]:
        out += (f'  (fp_line (start {ax:.2f} {ay:.2f}) (end {bx:.2f} {by:.2f})'
                f' (stroke (width {w}) (type solid)) (layer "{layer}"))\n')
    return out


def texts(name):
    return (
        f'  (property "Reference" "REF**" (at 0 0 0) (layer "F.SilkS") (uuid "00000000-0000-0000-0000-00000000000a")'
        f' (effects (font (size 1 1) (thickness 0.15))))\n'
        f'  (property "Value" "{name}" (at 0 0 0) (layer "F.Fab") (uuid "00000000-0000-0000-0000-00000000000b")'
        f' (effects (font (size 1 1) (thickness 0.15))))\n')


# ---------------------------------------------------------------- 3557-2
# blades N-S: pin pairs at y=-6.75 (pad 2, VF/north) and y=+6.75 (pad 1,
# trunk/south); within-pair pins at x=+-1.7.
f = header("FuseHolder_Keystone_3557-2",
           "Keystone 3557-2 ATO/ATC blade fuse holder, 30A UL, M65 p.41")
f += texts("3557-2")
for x in (-1.7, 1.7):
    f += tht_pad("2", x, -6.75, 3.2, 1.7)
    f += tht_pad("1", x, 6.75, 3.2, 1.7)
f += silk_rect(-3.9, -10.1, 3.9, 10.1)
f += silk_rect(-3.7, -9.9, 3.7, 9.9, layer="F.Fab", w=0.1)
f += (f'  (fp_text user "F" (at 0 8.6 0) (layer "F.Fab")'
      f' (effects (font (size 0.8 0.8) (thickness 0.12))))\n')
# courtyard
f += silk_rect(-4.2, -10.4, 4.2, 10.4, layer="F.CrtYd", w=0.05)
f += ")\n"
(LIB / "FuseHolder_Keystone_3557-2.kicad_mod").write_text(f)

# ------------------------------------------------------------- WSLP2726
f = header("R_Shunt_WSLP2726", "Vishay WSLP2726 shunt, doc 30179 pads 2.69x5.71 sp 4.93")
f = f.replace("(attr through_hole)", "(attr smd)")
f += texts("WSLP2726")
f += smd_pad("1", 0, 2.465, 5.71, 2.69)    # south = VF (current in)
f += smd_pad("2", 0, -2.465, 5.71, 2.69)   # north = VP (current out)
f += silk_rect(-3.45, -3.45, 3.45, 3.45, layer="F.Fab", w=0.1)
for y in (-4.15, 4.15):
    f += (f'  (fp_line (start -3.5 {y}) (end 3.5 {y})'
          f' (stroke (width 0.15) (type solid)) (layer "F.SilkS"))\n')
f += silk_rect(-3.7, -4.4, 3.7, 4.4, layer="F.CrtYd", w=0.05)
f += ")\n"
(LIB / "R_Shunt_WSLP2726.kicad_mod").write_text(f)

# ------------------------------------------------------------------ lugs
for name, drill, annulus, label in [("Lug_M5", 5.3, 13.0, "M5"),
                                    ("Lug_M4", 4.3, 11.0, "M4")]:
    f = header(name, f"bolted ring-lug stud, {label}, plated both sides (ADR-0005)")
    f += texts(name)
    f += tht_pad("1", 0, 0, annulus, drill)
    # NO silk circle: it would sit on the annulus (mask-clipped) or on
    # neighbors; the functional labels carry the human story (P5). The
    # courtyard is the BOLT-HEAD footprint (smaller than the annulus —
    # the copper ring may underlap neighbor courtyards, the hardware does not).
    r = annulus / 2
    f += (f'  (fp_circle (center 0 0) (end {r:.2f} 0)'
          f' (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab"))\n')
    f += (f'  (fp_circle (center 0 0) (end {r - 0.05:.2f} 0)'
          f' (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))\n')
    f += ")\n"
    (LIB / f"{name}.kicad_mod").write_text(f)

# --------------------------------------------------- M4 plated mount
# ADR-0007: plated barrel + O9.0 washer land both sides, NET-FREE
# (chassis potential — 0.8mm local clearance keeps 24V copper away),
# courtyard O10 for the DIN125 washer envelope.
f = header("Mount_M4_Plated", "M4 plated mounting hole, O9 washer land, net-free (ADR-0007)")
f += texts("Mount_M4")
f += ('  (pad "1" thru_hole circle (at 0 0) (size 9.00 9.00) (drill 4.30)\n'
      '   (layers "*.Cu" "*.Mask") (remove_unused_layers no) (clearance 0.8))\n')
f += (f'  (fp_circle (center 0 0) (end 4.5 0)'
      f' (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab"))\n')
f += (f'  (fp_circle (center 0 0) (end 5.0 0)'
      f' (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))\n')
f += ")\n"
(LIB / "Mount_M4_Plated.kicad_mod").write_text(f)

# ------------------------------------------- vendored ESP32 module variant
# The std RF_Module footprint's EP thermal vias drill 0.2mm — below the JLC
# 2-layer standard 0.3mm floor. Vendored copy with 0.3mm drills (pad ring
# 0.6 -> annular 0.15, still legal). Vendoring (not runtime edit) keeps
# lib_footprint_mismatch parity clean (kicad-pcb skill 2026-07-16 batch).
std = Path("/usr/share/kicad/footprints/RF_Module.pretty/ESP32-C3-WROOM-02.kicad_mod")
txt = std.read_text()
n02 = txt.count("(drill 0.2)")
assert n02 >= 9, f"expected >=9 EP vias with drill 0.2, found {n02}"
txt = txt.replace("(drill 0.2)", "(drill 0.3)")
txt = txt.replace('(footprint "ESP32-C3-WROOM-02"', '(footprint "ESP32-C3-WROOM-02_D03"')
(LIB / "ESP32-C3-WROOM-02_D03.kicad_mod").write_text(txt)

print(f"bbar.pretty: {len(list(LIB.glob('*.kicad_mod')))} footprints written")
