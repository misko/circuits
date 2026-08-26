#!/bin/bash
# Rebuild routed-board review evidence from the exact canonical PCB.
set -euo pipefail

cd "$(dirname "$0")/.."

BOARD="04_kicad/usb_hub_3s_v4.kicad_pcb"
OUT="${1:-06_build/routed_review}"
mkdir -p "$OUT"

# Several `kicad-cli` parse failures print usage and still exit zero.  Remove
# every expected target first and require a new non-empty file after its
# producer, so a stale review artifact can never masquerade as fresh output.
require_output() {
    local path="$1"
    [ -s "$path" ] \
        || { echo "EXPORT FAILED: producer did not create non-empty $path" >&2; exit 1; }
}
rm -f \
    "$OUT/top_copper.svg" "$OUT/bottom_copper.svg" \
    "$OUT/top_copper.png" "$OUT/bottom_copper.png" \
    "$OUT/top_3d.png" "$OUT/bottom_3d.png" "$OUT/iso_3d.png" \
    "$OUT/pcb_layers.pdf" "$OUT/assembly.pdf"

timeout 60s kicad-cli pcb export svg --mode-single --page-size-mode 2 \
    --exclude-drawing-sheet --fit-page-to-board --check-zones \
    -l F.Cu,Edge.Cuts -o "$OUT/top_copper.svg" "$BOARD"
require_output "$OUT/top_copper.svg"
timeout 60s kicad-cli pcb export svg --mode-single --page-size-mode 2 \
    --exclude-drawing-sheet --fit-page-to-board --check-zones --mirror \
    -l B.Cu,Edge.Cuts -o "$OUT/bottom_copper.svg" "$BOARD"
require_output "$OUT/bottom_copper.svg"
rsvg-convert -w 2400 -o "$OUT/top_copper.png" "$OUT/top_copper.svg"
require_output "$OUT/top_copper.png"
rsvg-convert -w 2400 -o "$OUT/bottom_copper.png" "$OUT/bottom_copper.svg"
require_output "$OUT/bottom_copper.png"

timeout 90s kicad-cli pcb render --side top --quality high \
    --background opaque --floor -w 2400 -h 1600 \
    -o "$OUT/top_3d.png" "$BOARD"
require_output "$OUT/top_3d.png"
timeout 90s kicad-cli pcb render --side bottom --quality high \
    --background opaque --floor -w 2400 -h 1600 \
    -o "$OUT/bottom_3d.png" "$BOARD"
require_output "$OUT/bottom_3d.png"
timeout 90s kicad-cli pcb render --side top --quality high \
    --background opaque --floor --perspective --rotate 35,0,-35 \
    -w 2400 -h 1600 -o "$OUT/iso_3d.png" "$BOARD"
require_output "$OUT/iso_3d.png"

timeout 60s kicad-cli pcb export pdf --mode-multipage \
    -l F.Cu,In1.Cu,In2.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts \
    --include-border-title --scale 0 --check-zones \
    -o "$OUT/pcb_layers.pdf" "$BOARD"
require_output "$OUT/pcb_layers.pdf"
timeout 60s kicad-cli pcb export pdf --mode-multipage \
    -l F.Silkscreen,B.Silkscreen,F.Fab,B.Fab,F.Courtyard,B.Courtyard,Edge.Cuts \
    --include-border-title --scale 0 --check-zones \
    -o "$OUT/assembly.pdf" "$BOARD"
require_output "$OUT/assembly.pdf"

sha256sum "$BOARD" "$OUT"/*
echo "Routed evidence complete: $OUT"
