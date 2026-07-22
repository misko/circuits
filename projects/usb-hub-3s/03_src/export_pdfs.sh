#!/bin/bash
# PDF exports for review + release. Schematic PDF = tscircuit's OWN render
# (ADR-0002 Phase A) - NOT a KiCad re-render of the machine sheet.
set -euo pipefail
cd "$(dirname "$0")/.."
B=04_kicad/usb_hub_3s.kicad_pcb
OUT=06_build/pdf
mkdir -p "$OUT"
cp 03_tscircuit/build/schematic.pdf "$OUT/schematic.pdf"
kicad-cli pcb export pdf --layers F.Cu,In1.Cu,In2.Cu,B.Cu,Edge.Cuts \
    --mode-multipage -o "$OUT/pcb_layers.pdf" "$B"
kicad-cli pcb export pdf --layers F.SilkS,F.Fab,F.Mask,Edge.Cuts \
    -o "$OUT/assembly_top.pdf" "$B"
kicad-cli pcb export pdf --layers B.SilkS,B.Fab,B.Mask,Edge.Cuts \
    -o "$OUT/assembly_bottom.pdf" "$B"
# PNGs for visual verification of the PDFs' content
mkdir -p 06_build/render
kicad-cli pcb render --side top    -o 06_build/render/board_top.png    "$B"
kicad-cli pcb render --side bottom -o 06_build/render/board_bottom.png "$B"
echo "pdfs -> $OUT ; renders -> 06_build/render"
