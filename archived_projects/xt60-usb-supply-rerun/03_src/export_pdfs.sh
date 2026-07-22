#!/bin/bash
# Release PDF set + PNG verification renders (jlcpcb-fab skill release list)
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=06_build/pdf
mkdir -p $OUT 06_build/renders

kicad-cli sch export pdf -o $OUT/schematic.pdf 04_kicad/xt60-usb-supply.kicad_sch

kicad-cli pcb export pdf --mode-multipage \
  -l F.Cu,In1.Cu,In2.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask \
  --cl Edge.Cuts -o $OUT/layers.pdf 04_kicad/xt60-usb-supply.kicad_pcb

kicad-cli pcb export pdf --mode-single \
  -l F.Fab,F.Silkscreen,Edge.Cuts --sketch-pads-on-fab-layers \
  -o $OUT/assembly.pdf 04_kicad/xt60-usb-supply.kicad_pcb

# PNG verification renders
kicad-cli sch export svg -o 06_build/renders/sch 04_kicad/xt60-usb-supply.kicad_sch
for f in 06_build/renders/sch/*.svg; do
  rsvg-convert -w 4000 "$f" -o "${f%.svg}.png"
done
for L in F.Cu,F.SilkS,F.Fab In1.Cu In2.Cu B.Cu,B.SilkS; do
  name=$(echo $L | tr ',.' '__')
  kicad-cli pcb export svg -o 06_build/renders/$name.svg -l "$L,Edge.Cuts" \
    --page-size-mode 2 04_kicad/xt60-usb-supply.kicad_pcb >/dev/null
  rsvg-convert -w 2400 06_build/renders/$name.svg -o 06_build/renders/$name.png
done
echo "PDFS: schematic.pdf layers.pdf assembly.pdf + renders/"
