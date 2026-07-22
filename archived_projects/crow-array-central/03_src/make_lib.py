#!/usr/bin/env python3
"""Vendor project-local footprints into 03_src/lib/cac.pretty.

- TQFP-128_14x14mm_P0.4mm_EP4.7mm: the XU316-1024-TQ128 land pattern. The
  stock KiCad Package_QFP:TQFP-128_14x14mm_P0.4mm has the 128 peripheral
  pads correct (MS-026 AEE, pin 1 top-left, CCW) but NO exposed paddle.
  The XU316 part.yaml (Fig 22 p41 / §14.3-14.4 p32) mandates an EP =
  pin 129 = VSS, D2/E2 4.40/4.70/5.00mm, soldered to GND with a 4x4 grid
  of thermal vias. We copy the stock pads 1-128 verbatim and ADD pad 129:
  a 4.7x4.7mm SMD center pad (F.Cu/Paste/Mask) plus a 4x4 array of
  same-net (pad "129") through-hole thermal vias (0.3 drill / 0.6 pad),
  so the paddle stitches to the In1 GND plane and R-THERM passes at gen
  time (no post-hoc via injection needed under the QFP).

Run: python3 03_src/make_lib.py
"""
from pathlib import Path

HERE = Path(__file__).parent
LIB = HERE / "lib" / "cac.pretty"
LIB.mkdir(parents=True, exist_ok=True)

STOCK = Path("/usr/share/kicad/footprints/Package_QFP.pretty/"
             "TQFP-128_14x14mm_P0.4mm.kicad_mod")
NEW_NAME = "TQFP-128_14x14mm_P0.4mm_EP4.7mm"

s = STOCK.read_text()
assert '(pad "128"' in s and '(pad "129"' not in s, "unexpected stock TQFP-128"

# rename the footprint
s = s.replace('(footprint "TQFP-128_14x14mm_P0.4mm"',
              f'(footprint "{NEW_NAME}"', 1)
s = s.replace('(property "Value" "TQFP-128_14x14mm_P0.4mm"',
              f'(property "Value" "{NEW_NAME}"', 1)

# ---- build the EP + thermal via block, injected before the final ')' ----
EP = 4.7               # exposed paddle side (D2/E2 nominal)
ep_pad = (f'\t(pad "129" smd rect (at 0 0) (size {EP} {EP})\n'
          f'\t\t(layers "F.Cu" "F.Paste" "F.Mask"))\n')
# 4x4 thermal via grid inside the paddle (§14.4 p32), pitch ~1.1mm
vias = []
coords = [-1.65, -0.55, 0.55, 1.65]
for vx in coords:
    for vy in coords:
        vias.append(
            f'\t(pad "129" thru_hole circle (at {vx} {vy}) (size 0.6 0.6)'
            f' (drill 0.3) (layers "*.Cu" "*.Mask"))\n')
# paste relief so the paddle does not float on a solder ball: 4 windows
paste = []
for px in (-1.1, 1.1):
    for py in (-1.1, 1.1):
        paste.append(
            f'\t(pad "129" smd rect (at {px} {py}) (size 1.6 1.6)'
            f' (layers "F.Paste"))\n')
block = ep_pad + "".join(vias)

# insert before the last top-level ')'
idx = s.rstrip().rfind(")")
s = s[:idx] + block + s[idx:]

(LIB / f"{NEW_NAME}.kicad_mod").write_text(s)
print(f"vendored {NEW_NAME}: pads 1-128 (stock) + EP pad 129 (4.7mm) "
      f"+ {len(vias)} thermal vias (4x4 grid)")
