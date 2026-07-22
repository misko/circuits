---
id: 0005
date: 2026-07-17
status: accepted
---
# 0005 — Connectors, assembly split, board format

## Context

A3: all terminals one 3.5mm family, qty 9. P2: THT connectors OK as
hand-solder. P10: 2-layer, M3 corner holes, plain-words silk.

## Options / decisions

- **Screw terminals**: KF128L-3.5-2P (C474930, 5.9k stock) — classic
  KF128 3.5mm family, 10A/300V, fits the KiCad Phoenix MPT-0,5-2 3.5mm
  land pattern (verified in part.yaml). Hand-solder (THT; JLC THT
  assembly for 9 terminals would force the economic-PCBA tier's THT
  setup — a bench build solders 20 joints in minutes). Wire openings
  face the board edge; every terminal gets a plain-words silk label
  ("LASER 1 5V/SW-GND" class wording, P10).
- **USB-C**: TYPE-C-31-M-12 (C165948, 326k stock, $0.18) — the KiCad
  standard library carries a footprint named for exactly this MPN;
  16P USB2.0 receptacle, SMD shell tabs, assembled by JLC.
- **OLED header**: THT 2.54mm 1x4 FEMALE socket, hand-solder,
  deliberately uncoded (JLC THT sockets are consign-class; any $0.05
  socket works). Prominent silk: pin words GND VCC SCL SDA plus
  "⚠ SOME MODULES SWAP GND/VCC — CHECK YOUR MODULE" warning text (P8).
- **Tactiles**: TS-1187A-B-A-B (C318884, Basic) for BOOT + RESET,
  SMD, assembled.
- **Board**: 92 x 62mm 2-layer, M3 (3.2mm drill) holes at 5.5mm corner
  insets; WROOM antenna overhangs the north edge (keepout satisfied by
  construction, audited).
- **Test points**: bare 1.5mm pads (TestPoint_Pad_D1.5mm), no BOM
  lines: COMP1-3, 5V, 3V3, GND (P10).
- **Power LED (D8)**: green 0805 + 1k on 3V3 — two Basic parts for
  at-a-glance rail confirmation on a bench instrument; not in the brief
  but squarely inside its purpose; zero Extended cost.

## Decision

As above; assembly split = all SMD top-side JLC-assembled, 10 THT
joints (9 terminals + 1 socket) hand-soldered, listed in the MANIFEST.
