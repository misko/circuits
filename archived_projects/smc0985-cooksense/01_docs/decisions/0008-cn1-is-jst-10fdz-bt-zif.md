# ADR-0008 — CN1 is a JST 10FDZ-BT top-entry ZIF (corrects ADR-0005's retention model)

status: accepted
date: 2026-07-24
supersedes: 0005

## Finding (clearer user photos + expert connector review, 2026-07-24)

The OEM front-panel receptacle CN1 is identified as a **JST FDZ-series
10-position, top-entry ZIF membrane-switch connector**, MPN
**`10FDZ-BT(S)(LF)(SN)`** (commonly `10FDZ-BT`). JST datasheet geometry:

- 10 contacts, **2.54 mm** pitch
- **pin-1-to-pin-10 center = 22.86 mm** (the confirming measurement — NOT the
  ~34 mm outer-housing reading, which catches the latch/lock projections and is
  ambiguous)
- housing width 36.26 mm, depth 7.7 mm, installed height 10.2 mm
- **nominal membrane-tail thickness 0.125 mm**
- variant discipline: **BT = top/vertical entry (correct)**; do NOT order
  `10FDZ-ST` (side/right-angle entry).

## The correction to ADR-0005 / D5

ADR-0005 (from the earlier, lower-resolution photos) read CN1 as a **latched
receptacle: two end-latches engaging two punched lock-slots in the tail**. The
clearer photos + review reinterpret that "ribbed" feature as the **ZIF sliding
clamp bar** — a fundamentally different retention mechanism. An FDZ ZIF grips a
**plain** membrane/FPC tail across all ten contacts; it needs **no punched
holes in the tail**.

**Decisive basis:** the original OEM membrane keypad tail is a **plain tail
(no punched lock-slots)** — consistent with a ZIF, inconsistent with a
latch-slot receptacle (a genuine FDZ would not use, or need, tail holes). The
2.54 mm pitch and the slider geometry match 10FDZ-BT. (User-confirmed
identification, 2026-07-24; the four receptacle photos are the Gate-1 evidence,
cited here per the ADR-0005 photo-as-evidence precedent.)

## Design implications (why this matters)

1. **Our OEM-side tongue simplifies to a PLAIN tail** — 10 fingers, 2.54 mm
   pitch, 0.125 mm thickness, finger length/contact-face per the FDZ datasheet.
   **The two lock-slots are DROPPED** — the fiddliest, most failure-prone
   feature of the tongue is gone.
2. **The membrane side can use a real 10FDZ-BT too.** CN1 is exactly the socket
   the original keypad tail came out of, so a purchased 10FDZ-BT on our
   interposer's membrane side is *proven-compatible by construction* — this
   **retires the unproven TE 6-520315-0 TRIO-MATE candidate** (ADR-0005
   membrane-side selection and BRIEF §5 candidate). One connector part serves
   both interposer interfaces.
3. **Sourcing:** distributor-stocked (Mouser / RS / DigiKey) but **not
   confirmed on LCSC/JLC** → treat as a **self-supplied, hand-solder,
   DO-NOT-SUBSTITUTE** part (same posture as the DIP05 relays and the PCC-SMP-K
   jack). Confirm LCSC/JLC before assuming JLC assembly.

## What is UNCHANGED (carried forward from ADR-0005)

- **Coupon gating (G1/G2) is still MANDATORY before any Board C fabrication.**
  A correct identification is not a fit proof.
- **Flex / rigid-flex fabrication is still OUTSIDE our proven rigid pipeline**
  (spec-tension T5): vendor-assisted CAD, **>=100 insertion cycles on a
  sacrificial coupon**, and **never first-fit on the OEM connector**.
- Board C stays **passive**: straight-through pass of U1-U6/D1-D4, breakout of
  the same ten lines to the CookSense board, labeled test points both sides,
  **no bond to logic ground or chassis** (keypad-domain isolation).

## Consequence for architecture

Because CN1 is now a known, purchasable ZIF that clamps a plain tail, the
brief's "rigid + short custom flex tail + proven connector" option (BRIEF §5)
becomes the low-risk decomposition: a **rigid interposer** (inside our proven
pipeline, both interfaces = 10FDZ-BT) plus **one dumb double-ended 10-finger
0.125 mm flex jumper** as the only out-of-pipeline, coupon-gated item. The
alternative single-part **rigid-flex** interposer remains valid but puts the
whole board out-of-pipeline. Fork recorded to the user; not decided here.
