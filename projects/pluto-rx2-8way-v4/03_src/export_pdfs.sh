#!/bin/bash
# Export the human-readable PCB PDF set from the current routed board.
set -euo pipefail
cd "$(dirname "$0")/.."

BOARD=pluto_rx2_8way_v4
OUT=06_build/fab/pdf
mkdir -p "$OUT"

kicad-cli pcb export pdf --mode-multipage \
    -l F.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,F.Paste,B.Paste \
    --cl Edge.Cuts --include-border-title --scale 0 \
    -o "$OUT/pcb_layers.pdf" "04_kicad/$BOARD.kicad_pcb"

/usr/bin/python3 03_src/assembly_drawing.py \
    "04_kicad/$BOARD.kicad_pcb" "$OUT/assembly.pdf"
/usr/bin/python3 03_src/check_assembly_pdf.py "$OUT/assembly.pdf"

cp 03_tscircuit/build/schematic.pdf "$OUT/schematic.pdf"
echo "PDF export complete: $OUT"
