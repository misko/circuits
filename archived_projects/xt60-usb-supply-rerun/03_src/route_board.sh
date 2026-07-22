#!/bin/bash
# Re-route from scratch with KiCadRoutingTools (routing-pipeline.md).
# Produces 03_src/route/routed_final.kicad_pcb (the committed KRT chain
# file that rebuild_all.sh re-imports). Only signal nets are routed —
# power rides pours; EN/ILMT/CBS taps are DESIGNED_TRACKS in
# generate_board.py.
set -euo pipefail
cd "$(dirname "$0")/.."

PY=/usr/bin/python3
KRT=~/gits/KiCadRoutingTools
KRTPY=/home/mouse9911/virtual-envs/spf/bin/python

NETS="PFET_G DCP1 DCP2 DCP3 LED1_A LED2_A LED3_A"

$PY 03_src/generate_board.py --krt-input

# pass 1: CC lines F.Cu-only (a via would land in the USB-C pad field —
# KRT necked to 0.3/0.15 vias there once; standard tier forbids them)
$KRTPY $KRT/route.py 06_build/route/krt_input.kicad_pcb \
  --output 06_build/route/krt_s1.kicad_pcb \
  --layers F.Cu \
  --clearance 0.13 --track-width 0.2 --via-size 0.6 --via-drill 0.3 \
  --fab-tier standard --keepout --keepout-layer User.2 \
  --max-iterations 300000 \
  --nets CC1 CC2

# pass 2: the rest, chained on pass 1's output (KRT-dialect chain file)
$KRTPY $KRT/route.py 06_build/route/krt_s1.kicad_pcb \
  --output 06_build/route/krt_s2.kicad_pcb \
  --layers F.Cu B.Cu \
  --clearance 0.2 --track-width 0.3 --via-size 0.6 --via-drill 0.3 \
  --fab-tier standard --keepout --keepout-layer User.2 \
  --max-iterations 300000 \
  --nets $NETS

mkdir -p 03_src/route
cp 06_build/route/krt_s2.kicad_pcb 03_src/route/routed_final.kicad_pcb
echo "ROUTE: chain file staged at 03_src/route/routed_final.kicad_pcb"
echo "Now run: bash 03_src/rebuild_all.sh"
