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
