#!/usr/bin/env python3
"""Vendor project-local footprint variants into 03_src/lib/shitty_kitty.pretty.

- TerminalBlock_3.5-2P_NoSilk: the std Phoenix PT-1,5-2-3.5-H 1x02 with ALL
  silkscreen graphics stripped. Rationale: the stock silk (body outline +
  entry marks) overhangs the board edge at our edge-flush placement and
  collides with the plain-words channel labels (P10); our generated labels
  replace it. Vendoring (not runtime edits) avoids lib_footprint_mismatch
  parity noise (kicad-pcb skill). Textual transform — pcbnew.FootprintSave
  proved a silent no-op here (KiCad 10.0.4).
- ESP32-S3-WROOM-1: the std RF_Module footprint minus (a) the 17 x 0.2mm EP
  thermal via-holes (below the JLC 2-layer standard 0.3mm drill floor; the
  stitcher adds legal 0.6/0.3 EPAD vias instead) and (b) all silkscreen (the
  stock outline crosses the board edge at our antenna-overhang placement).

Run: python3 03_src/make_lib.py
"""
from pathlib import Path

HERE = Path(__file__).parent
LIB = HERE / "lib" / "shitty_kitty.pretty"
LIB.mkdir(parents=True, exist_ok=True)
SRC = Path("/usr/share/kicad/footprints/TerminalBlock_Phoenix.pretty/"
           "TerminalBlock_Phoenix_PT-1,5-2-3.5-H_1x02_P3.50mm_Horizontal.kicad_mod")
s = SRC.read_text()


def children(text):
    """Split the body of the top-level (footprint ...) into balanced chunks."""
    i = text.index("(", 1)  # skip the opening (footprint
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
name_old = 'TerminalBlock_Phoenix_PT-1,5-2-3.5-H_1x02_P3.50mm_Horizontal'
body = head + "\n  ".join(kept) + tail
body = body.replace(f'"{name_old}"', '"TerminalBlock_3.5-2P_NoSilk"', 1)
(LIB / "TerminalBlock_3.5-2P_NoSilk.kicad_mod").write_text(body)
print(f"vendored TerminalBlock_3.5-2P_NoSilk ({killed} silk items stripped)")

# ---- WROOM variant
SRC2 = Path("/usr/share/kicad/footprints/RF_Module.pretty/ESP32-S3-WROOM-1.kicad_mod")
head, chunks, tail = children(SRC2.read_text())
kept, k_silk, k_hole = [], 0, 0
for ch in chunks:
    kind = ch[1:].split(None, 1)[0]
    if kind.startswith("fp_") and '"F.SilkS"' in ch and "(property" not in ch:
        k_silk += 1
        continue
    if kind == "pad" and "(drill 0.2)" in ch:
        k_hole += 1
        continue
    kept.append(ch)
assert k_hole >= 10, f"expected ~17 EP micro-holes, found {k_hole}"
assert k_silk >= 2, f"expected silk items, found {k_silk}"
body2 = head + "\n  ".join(kept) + tail
body2 = body2.replace('"ESP32-S3-WROOM-1"', '"ESP32-S3-WROOM-1"', 1)
(LIB / "ESP32-S3-WROOM-1.kicad_mod").write_text(body2)
print(f"vendored ESP32-S3-WROOM-1 ({k_hole} EP micro-holes + {k_silk} silk items stripped)")
