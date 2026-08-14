# Pluto RX2 eight-way v5 — strict RF module review

subject: pluto-rx2-8way-v5
release_candidate: v0.2.1-2026-08-14
review_type: integrated blocking RF source/realized verification
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
reviewed_on: 2026-08-14
source_commit: 35900c222263beb47362c67e9050689a6b65f76b
board_sha256: e2d1deaf4052b18b84df02d1b5cab48e131c6debbd70a03678c3ed918b24c2d5
rf_contract_sha256: 625acbc4c6f40b1a521c011399c0617fa5ec02817a3bccac31f2b149918b00bb
rf_source_bundle_sha256: a89deb1fe5f387458061f22670d43920a046bd9e9bc9feca29472cfb50693fb6
rf_realized_bundle_sha256: 2893a81003f5c90ea962d9ce627c2170896652ce7cf58ff2666c48571c859cc8

The bounded clean-room context stage selected nine retained source cards and
covers all three required topics: RF discontinuities, grounding/fencing and
layout validation. Source verification grades all 9/9 RF nets. It finds 14
declared native arcs, no sharp line junction, no undeclared exception, one
explicit fence-band authority, and a worst source bend radius of 3.350 routed
widths against the blocking 3.0 minimum.

The complete deterministic hardware replay, including J12 bench power, passes
final KiCad DRC 0/0/0.
Realized verification independently grades the saved board, again covering
9/9 RF nets and the same 14 native arcs with zero RF vias. Route-following
ground-fence verification passes 18/18 flanks; the worst along-route aperture
is 1.3979 mm against the 1.4000 mm limit. The source and realized evidence
bundles are exact-artifact-bound by the RF schematic and PCB reviews.

This release therefore completes migration from the legacy advisory geometry
contract to blocking `rf-module-v1`. The machine and visual evidence agree:
seven paths use tangent rounded transitions and two remain straight. No
firmware was generated, reviewed or included. P0/P1/P2 findings are 0/0/0;
the design is **SOUND**. JLC upload/process acknowledgements and physical
first-article VNA acceptance remain mandatory, so ordering is
**DO-NOT-ORDER**.
