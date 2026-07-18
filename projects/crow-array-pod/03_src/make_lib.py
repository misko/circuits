#!/usr/bin/env python3
"""Vendor project-local footprints into 03_src/lib/pod.pretty.

- CMT-8504: built from the datasheet's Recommended PCB Layout (page 2,
  rev 2024-09-11): four 2.5x2.5mm corner pads, centers at (±3.5, ±3.5)
  (outer span 9.5, inner 4.5). Pad 1 = POLARITY(+) top-left, pad 2 =
  POLARITY(-) bottom-left, pads 3/4 = the right-column DUMMY pads
  (mechanical only). Silk "+" beside pad 1; body outline 8.5x8.5.
- TerminalBlock_3.5-8P_NoSilk: std Phoenix PT-1,5-8-3.5-H with ALL silk
  stripped (our generated plain-word labels + pin numbers replace it, and
  the stock outline would collide with them). Textual transform per the
  esp32-laser-timing precedent (FootprintSave is a silent no-op on 10.0.4).

Run: python3 03_src/make_lib.py
"""
from pathlib import Path

HERE = Path(__file__).parent
LIB = HERE / "lib" / "pod.pretty"
LIB.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- CMT-8504
pads = [
    ("1", -3.5, -3.5),   # POLARITY (+) top-left
    ("2", -3.5, 3.5),    # POLARITY (-) bottom-left
    ("3", 3.5, 3.5),     # DUMMY bottom-right (numbering matches JLC C22359707 CAD)
    ("4", 3.5, -3.5),    # DUMMY top-right
]
pad_s = "\n".join(
    f'  (pad "{n}" smd rect (at {x} {y}) (size 2.5 2.5) (layers "F.Cu" "F.Paste" "F.Mask"))'
    for n, x, y in pads)
body = 4.25
fp = f'''(footprint "CMT-8504"
  (version 20221018) (generator make_lib)
  (layer "F.Cu")
  (descr "Same Sky CMT-8504-100-SMT-TR magnetic transducer, land pattern from datasheet p.2 recommended layout")
  (attr smd)
  (property "Reference" "BZ" (at 0 -6.2 0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))
  (property "Value" "CMT-8504" (at 0 6.2 0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))
  (fp_line (start -{body} -{body}) (end {body} -{body}) (stroke (width 0.12) (type solid)) (layer "F.Fab"))
  (fp_line (start {body} -{body}) (end {body} {body}) (stroke (width 0.12) (type solid)) (layer "F.Fab"))
  (fp_line (start {body} {body}) (end -{body} {body}) (stroke (width 0.12) (type solid)) (layer "F.Fab"))
  (fp_line (start -{body} {body}) (end -{body} -{body}) (stroke (width 0.12) (type solid)) (layer "F.Fab"))
  (fp_circle (center 0 0) (end 1.0 0) (stroke (width 0.12) (type solid)) (fill none) (layer "F.Fab"))
  (fp_line (start -5.3 -1.6) (end -5.3 -2.6) (stroke (width 0.15) (type solid)) (layer "F.SilkS"))
  (fp_line (start -5.8 -2.1) (end -4.8 -2.1) (stroke (width 0.15) (type solid)) (layer "F.SilkS"))
  (fp_line (start -2.0 -4.5) (end 2.0 -4.5) (stroke (width 0.15) (type solid)) (layer "F.SilkS"))
  (fp_line (start -2.0 4.5) (end 2.0 4.5) (stroke (width 0.15) (type solid)) (layer "F.SilkS"))
  (fp_rect (start -4.85 -4.85) (end 4.85 4.85) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))
{pad_s}
)
'''
(LIB / "CMT-8504.kicad_mod").write_text(fp)
print("vendored CMT-8504 (4 pads, + mark on silk near pad 1)")

# ------------------------------------------------- terminal, silk stripped
SRC = Path("/usr/share/kicad/footprints/TerminalBlock_Phoenix.pretty/"
           "TerminalBlock_Phoenix_PT-1,5-8-3.5-H_1x08_P3.50mm_Horizontal.kicad_mod")
s = SRC.read_text()


def children(text):
    i = text.index("(", 1)
    head = text[:i]
    out, depth, start = [], 0, i
    for j in range(i, len(text)):
        c = text[j]
        if c == "(":
            if depth == 0:
                start = j
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                out.append(text[start:j + 1])
            elif depth < 0:
                return head, out, text[j:]
    raise ValueError("unbalanced")


head, chunks, tail = children(s)
kept, killed = [], 0
for ch in chunks:
    kind = ch[1:].split(None, 1)[0]
    if kind.startswith("fp_") and '"F.SilkS"' in ch and "(property" not in ch:
        killed += 1
        continue
    kept.append(ch)
assert killed >= 3, f"expected to strip silk graphics, killed only {killed}"
name_old = 'TerminalBlock_Phoenix_PT-1,5-8-3.5-H_1x08_P3.50mm_Horizontal'
body2 = head + "\n  ".join(kept) + tail
body2 = body2.replace(f'"{name_old}"', '"TerminalBlock_3.5-8P_NoSilk"', 1)
(LIB / "TerminalBlock_3.5-8P_NoSilk.kicad_mod").write_text(body2)
print(f"vendored TerminalBlock_3.5-8P_NoSilk ({killed} silk items stripped)")
