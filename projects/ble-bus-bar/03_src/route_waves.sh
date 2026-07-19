#!/bin/bash
# KRT routing waves for ble-bus-bar (west electronics zone ONLY — the
# slices/corridor are hand-routed by route_channels.py; power is pours).
# 2-layer JLC 2oz (0.16/0.16 floor; we route 0.3/0.2 signals, 0.6 power).
# GND is NOT routed — F/B pours + stitch/rescue vias (stitch_and_fill.py).
# Wave 1: signals 0.3mm; Wave 2: electronics power 0.6mm (EPWR >= 0.5 floor).
set -euo pipefail
cd "$(dirname "$0")/.."
KRT=~/gits/KiCadRoutingTools
R=06_build/route
PY=~/gits/KiCadRoutingTools/.venv/bin/python

$PY "$KRT"/route.py "$R"/r0.kicad_pcb --output "$R"/r1.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.2 --track-width 0.3 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 400000 \
  --nets SDA SCL ALERT USB_DP USB_DM CC1 CC2 SPI_CLK SPI_MOSI \
         SPI_MISO FLASH_CS EN BOOT9 IO8 LED_ST LED1A LED2A TXD RXD FB SHDN

# scoped repair (fine grid): the USB-C 0.5mm weave + the module pins that
# sit in 0.6mm gaps (SCL/ALERT/LED_ST); 0.2mm track is legal (2oz floor 0.16)
$PY "$KRT"/route.py "$R"/r1.kicad_pcb --output "$R"/r1b.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.15 --track-width 0.2 --grid-step 0.05 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 200000 \
  --nets USB_DM USB_DP SCL ALERT LED_ST SPI_MISO IO8 RXD TXD

$PY "$KRT"/route.py "$R"/r1b.kicad_pcb --output "$R"/r2.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.16 --track-width 0.5 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 400000 \
  --nets TMP_3V3 VTAP VIN_E SW BOOT VLDO VUSB

# fine-grid completion for TMP_3V3 stragglers (boxed decoupler pads)
$PY "$KRT"/route.py "$R"/r2.kicad_pcb --output "$R"/r3.kicad_pcb \
  --layers F.Cu B.Cu --clearance 0.16 --track-width 0.3 --grid-step 0.05 \
  --via-size 0.6 --via-drill 0.3 --fab-tier standard --no-stub-layer-swap \
  --keepout --keepout-layer User.2 --max-iterations 200000 \
  --nets TMP_3V3

echo "waves done -> $R/r3.kicad_pcb"
