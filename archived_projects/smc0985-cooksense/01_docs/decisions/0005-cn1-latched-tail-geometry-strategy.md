# ADR-0005 — CN1 is LATCHED; replicate the tail geometry, don't chase the MPN

status: superseded-by-0008
date: 2026-07-22

> **SUPERSEDED 2026-07-24 by ADR-0008.** Clearer photos + an expert connector
> review identify CN1 as a JST **10FDZ-BT top-entry ZIF** that clamps a PLAIN
> 0.125 mm tail — the "two end latches + punched lock-slots" reading below was
> a misread of the ZIF slider. The tail-geometry-replication strategy stands,
> but the **lock-slots are dropped** and the membrane-side connector is now a
> real 10FDZ-BT (not the TRIO-MATE candidate). The coupon gate (G1/G2) and the
> flex-out-of-pipeline caution (T5) are unchanged. See ADR-0008.

## Finding (user photos + TE datasheet, 2026-07-22 — corrects brief §1.2)
The OEM CN1 has TWO END LATCHES that lock the tail; the membrane tail
has TWO PUNCHED LOCK-SLOTS they engage. The brief's candidate
TE 6-520315-0 TRIO-MATE is FRICTION-ONLY ("Mating Retention: Without",
TE TDS) — so CN1 is a LATCHED membrane receptacle (likely a local
appliance-market make), NOT a plain TRIO-MATE. Coupon gating earned
its keep before any part was ordered.

## Strategy
- OEM side: we never buy CN1's mate — we DESIGN OUR FLEX TONGUE to fit
  the existing receptacle: replicate the OEM tail EXACTLY — 10 fingers,
  pitch, width, thickness, finger length, contact face, AND the two
  lock-slots (position/size/edge-distance) so the OEM latches retain
  our tongue as they do the original.
- Our membrane side (receiving the original tail): any compatible
  10-pos 2.54mm membrane receptacle accepting a 0.13-0.38mm printed
  tail; TRIO-MATE 6-520315-0 REMAINS the candidate HERE (friction is
  fine on our side; the tail's holes are inert to it). Coupon-gated.
- Gate-1 measurement list grows: lock-slot dims/positions + latch
  style. The two user photos are archived Gate-1 evidence.
- Fabrication: flex/rigid-flex is OUTSIDE our proven rigid pipeline
  (spec-tension T5) — vendor-assisted CAD, coupon first, >=100 cycles
  on a sacrificial coupon, never first-fit on the OEM connector.
