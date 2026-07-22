# ADR-0005 — power terminals + fuse holders

Status: accepted 2026-07-18

## Context

Input feed must carry 60 A, each port up to 30 A. Commission offers
M5/M6 screw-lug terminals or 30 A+ screw terminal blocks; ports
likewise. Fuses: ATO/ATC PCB-mount holders (A3).

## Decisions

1. **Bolted ring-lug studs, not screw terminal blocks.**
   - Input: M5 plated through-hole (Ø5.3 hole, Ø13 annulus, both
     layers) for a crimped M5 ring lug on 6 AWG-class wire. A proper
     lug + bolt joint is the gold standard at 60 A (mΩ-free, torque
     spec'd, vibration-proof); the stud barrel also bonds the F/B
     trunk pours.
   - Ports: M4 plated through-holes (Ø4.3 hole, Ø11 annulus) for M4
     ring lugs on 10 AWG-class wire, 30 A each.
   - GND reference: M4 stud, silk-labeled "GND REF — NOT LOAD RETURN"
     (loads return to battery/chassis; ARCHITECTURE ground strategy).
   REJECTED: PCB screw terminal blocks at 30 A+ — the JLC/LCSC catalog
   is effectively empty of genuine 30 A PCB terminals (KF128-class
   parts are 10–15 A); barrier blocks that qualify are large, costly,
   and still end in a ring lug. The stud IS the terminal, with zero
   BOM risk. Hardware (M5/M4 bolts, nuts, washers) is user-supplied —
   listed with torque specs in ORDER_README.

2. **Fuse holder: Keystone 3557-2** (LCSC C352820, 957 stock, $1.44) —
   "2-in-1" PCB holder for standard ATO/ATC blades (and low-profile
   Mini), UL 30 A @ 500 V AC, THT, insulated body so a dropped tool
   can't short across the clips. Land pattern from the M65 catalog
   p.41 mounting detail: 4 pins Ø1.6 holes, pairs 13.5 mm apart
   (= standard blade spacing), 3.4 mm within a pair; body
   19.8×7.4 mm, vertical fuse entry (blade swaps from above, P5 human
   factors). One holder per port. Hand-solder line (THT, 30 A joints
   deserve a human), deliberately uncoded in the assembly BOM.
   REJECTED: bare clip pairs (Keystone 3557/3577 singles — no
   insulator, two parts to misalign per port); Fuse_Blade_ATO
   directSolder footprint (fuse not user-replaceable — violates A3);
   MINI-blade holders (A3 says ATO/ATC).

3. **Fuses themselves are user-supplied** (not in BOM): any ATO/ATC
   blade ≤30 A. ORDER_README notes the 80 % continuous derating
   convention (30 A fuse ≈ 24 A continuous) and that the board's
   copper is sized for the full 30 A regardless.
