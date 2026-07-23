# Journal — usb-hub-3s-v3 board backend (placement/route)

## 2026-07-22 — placement (drop PD cell, pour 5VC to J5)
- did: Carried v2's proven floorplan and removed only the USB-C/PD corner.
  Deleted anchors RS3/Q6/Q7/U1 and seeds R23-R26/C44-C48/C51; kept U12/J5;
  seeded C49/C50 (VBUS bulk, unchanged positions) + added R28/R29 (CC Rp
  pull-ups near J5). Reworked the SE pours: removed RSNS/PDSRC islands and
  renamed the 4 VBUSC zones to **5VC**, adding a bridge rect so the buck-C 5VC
  pour runs continuously east+south into J5's VBUS pads (VBUS == 5VC). Removed
  the `pd_escape` keepout; fixed the pad_net asserts (J5.A4/A9 on 5VC) and the
  silk (USB-C caption + v3 version label). Copied audit_board.py (PD invariants
  removed, CC-pull-up proximity added) + rebuild_all.sh/rebuild_fast.sh from v2.
  Backfilled datasheet `layout:` blocks on the 10 in-scope parts (v2 never had
  them — P-LAYOUT was FAIL there); deleted the orphaned PMR100 (RS3's 5mR sense).
- result: MEASURED —
  - generate_board_generic: **100 placed (33 anchored), 24/24 asserts PASS,
    34 legalized.**
  - **audit_board: PASS** (16 polarity, 19 proximity, 4 edge, 104 silk).
  - **policy_audit --skip-drc: P-LAYOUT PASS, P-ADJ PASS** (no QFN — the v2
    RSNS/PDSRC keep-short waiver is GONE). Remaining FAILs are pre-route only:
    R-THERM (power pads unbonded until stitch adds thermal vias/pour bond).
  - 5VC pour geometry verified: all J5 VBUS pads (y104.95), C49/C50, R28/R29
    5VC pins, U12.5 sit inside overlapping 5VC zones -> one connected island.
- next: route (fab tier STANDARD — verify escape_check; race:6 KRT); drive DRC 0/0/0.

## 2026-07-22 — routing GATE GREEN (DRC 0/0/0, STANDARD tier)
- did: Dropped to STANDARD fab tier (jlc_4layer_standard) — escape_check grades
  every remaining part at jlc_2layer_default (the TPS25740A QFN was the sole
  advanced driver). Updated nets.yaml (tier + removed AUX_5V/PD_NET classes,
  clearances >=0.127), floorplan design_rules (0.127 clr / 0.45-0.3 vias / 0.5
  hole-to-hole), route.yaml (standard vias, race:6, removed PD waves/pdaux + PD
  taps, CC1/CC2 taps now J5->R28/R29). KRT race:6 rolled CLEAN on the first try
  (no 0.5mm QFN): all signal waves routed; promoted c0/r4 -> final_chain.
- FIXES to clear the tail (all mechanical; 0 routing failures):
  * TPS2557 (U3/U4/U5) footprint had 0.2mm baked-in thermal vias (fail STANDARD
    0.3mm min) -> non-ThermalVias VSON-8 variant (cleared 18 drill errors).
  * LM5116 (U2/U11) ThermalVias EP array collided with GND stitch vias
    (hole_to_hole) -> non-ThermalVias variant (6 warnings). Footprint changes
    need kicad_sch + netlist regenerated (generate_board reads the netlist FPID).
  * J1 XT60 no-net alignment posts at x24 -> stitch grid start x24->x26 (4
    clearance). 1 lone GND via dangling in the VBUSA3 pour -> grid x capped at 116
    (east strip is VBUS/5VC pours; GND lives on In1, pad_rescue bonds connector GND).
- result (MEASURED, reproducible via rebuild_fast.sh):
  **DRC 0/0/0** — `kicad-cli pcb drc --severity-all --refill-zones
  --schematic-parity` = 0 violations / 0 unconnected / 0 schematic-parity (sch
  placed beside the board so parity actually RUNS). Trajectory: 28 -> 25 -> 1 -> 0.
  audit_board PASS; count_parity 100 across all 5 representations. policy_audit
  full: PASS=22, only R-THERM flags 4 pour-carried power pads (U11.21 GND EP,
  Q1/Q3/Q5 FET drains on SW/VBAT_F pours) — addressed next.
- KRT rolls: race 6, winner c0/r4 (promoted).
