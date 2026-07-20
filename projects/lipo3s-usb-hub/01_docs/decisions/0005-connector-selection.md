# ADR-0005 — Connector selection (XT60 / USB-A / USB-C)

Status: accepted (2026-07-20)

## Decision

- **Input: XT60PW-M** (J1, LCSC C98732) — PCB-mount XT60, the standard 3S-LiPo pack
  connector; 30 A-rated blades (far above the 8.2 A board draw). **Polarity fact
  (load-bearing): KiCad pad 1 = the "−" blade, pad 2 = "+"** — verified against the
  footprint silk + EasyEDA pad frame (`02_parts/XT60PW-M/part.yaml`). The TSX binds
  pad 1 → GND, pad 2 → VBATT_RAW accordingly. This is the single most dangerous pin
  fact on the board (a reversed XT60 symbol shipped +into GND on a sibling board) — it
  gets an explicit pin review and a first-power multimeter ritual.

- **USB-A ×3: CNCTech 1001-011-01101** (J2–J4), horizontal THT USB-A receptacle,
  current-max variant with 1.10 mm shield holes 11.40 mm apart matching the KiCad
  `USB_A_CNCTech_1001-011-01101_Horizontal` land pattern. Robust THT mechanical
  retention for a hub that will see repeated plug cycles. Hand-solder / consigned at
  JLC (THT connector) — listed in the not-assembled BOM lines.

- **USB-C: GCT USB4105-GF-A** (J5, LCSC C3020560), 16-pin power-capable Type-C
  receptacle, top-mount horizontal. 16P (power + CC + a data pair + SBU) is sufficient
  for a non-PD power source; the full 24-pin part's extra data lanes are unused here.

## Rationale / rejected

- The connector families (XT60 / USB-A / USB-C) are fixed by the brief. The specific
  MPNs are chosen for JLC availability, a correct verified KiCad land pattern, and
  mechanical robustness. A vertical USB-A was rejected (edge-mount horizontal gives a
  cleaner hub face and hole-anchored retention). A 24-pin USB-C was rejected as
  unnecessary pins/area for a no-PD, no-alt-mode power port.

## Consequences

- Two connectors (XT60, USB-A) are THT and hand-soldered/consigned; their orientation
  is an operator instruction, checked in the JLC preview and the twin render.
- The XT60 and fuse-holder silk are edge-trimmed variants in the project footprint lib
  so silk does not cross the board edge.
