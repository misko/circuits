# SUPERSEDED by crow-recorder-central-v2-v1.2-2026-07-24

Sealed: 2026-07-24 (seal d9d5ae1, source b08f182). Superseded the same day.

Reason: a SECOND external review (archived verbatim:
`08_reviews/2026-07-24_v1.1_external-llm2_full.md`; verdict HOLD for
ordering this exact archive) found the XU316 0V9 core rail carrying only
**8 local 100 nF bypass capacitors (C_c1..C_c8) against the vendor minimum
of 12** — verified against the XU316-1024-TQ128 datasheet
XM-014532-PC-2.0.0 §14 "Integration" p.29 ("Place many (at least 12)
100 nF low inductance multi-layer ceramic capacitors close to the chip"),
not taken on reviewer authority. Our own v1.1 pin review had measured 0V9
landing on 15 core-VDD pins {5,11,14,18,39,45,50,54,68,85,95,104,105,106,
113}; 8 caps for 15 pins is below the datasheet floor.

v1.2 ships **13× 100 nF on 0V9** (C_c9..C_c13 added, anchored at the
previously under-served pins; measured per-pin table in
`../crow-recorder-central-v2-v1.2-2026-07-24/verification/decoupling_fix.md`).

v1.1 is OTHERWISE SOUND: the same review positively confirms all four v1.0
blocker closures (U1 filled+capped EP vias, USB 90 Ω constraint, LV-strap
floats, manifest consistency), and v1.2 re-measures them intact. v1.1
remains technically orderable for a controlled bench first-article under a
written decoupling waiver (the review's conditional path) — but the
preferred and executed disposition is the v1.2 spin. Do not order this
archive when v1.2 is available.
