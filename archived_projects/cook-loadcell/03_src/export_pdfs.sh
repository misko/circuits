#!/bin/bash
# PDF documentation set for a release: schematic + layered PCB + assembly.
# Per project rule every PDF is also rendered to PNG for visual verification.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="$PWD/06_build/pdf"
mkdir -p "$OUT"
rm -f "$OUT"/*.pdf "$OUT"/*.png

kicad-cli sch export pdf -o "$OUT/schematic.pdf" 04_kicad/cook_loadcell.kicad_sch >/dev/null

kicad-cli pcb export pdf --mode-multipage \
    -l F.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask \
    --cl Edge.Cuts --include-border-title \
    -o "$OUT/pcb_layers.pdf" 04_kicad/cook_loadcell.kicad_pcb >/dev/null

kicad-cli pcb export pdf --mode-single \
    -l F.Fab,F.Silkscreen,Edge.Cuts --sketch-pads-on-fab-layers \
    --include-border-title --black-and-white \
    -o "$OUT/assembly_top.pdf" 04_kicad/cook_loadcell.kicad_pcb >/dev/null

for f in "$OUT"/*.pdf; do
    pdftoppm -png -r 100 "$f" "${f%.pdf}" >/dev/null 2>&1 || true
done
ls "$OUT" | tail -6
