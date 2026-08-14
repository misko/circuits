subject: Pluto RX2 8-Way v5 corrected exact-board placement and route-base renewal
date: 2026-08-13
reviewer: Codex fresh-context layout reviewer
context-given: current corrected v5 board and prepared route only
review_stage: pre-route
review_kind: layout
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
board_sha256: bdb0df87886cc15ed8a3ae2aee53c97f4a4cfd49734558967240816c5c73a22e
design_rules_sha256: 6e1a3d39e0600855e690a001bfaeb55ac205940686e79215721a1096347266e7
route_prep_sha256: 31594a8e29417cf6b5a1a374918b1d6979329c38a8f9d4c84182d17a46d7c872

# Fresh corrected placement/layout renewal

## Verdict and boundary

**SOUND / DO-NOT-ORDER.** The prior board's P1 adjacency defect is closed on
the exact board bound above. A fresh reviewer used no earlier-board verdict as
evidence. P0/P1 findings: none. This authorizes the five bounded KRT waves; it
does not approve the as-yet-unrealized routed/stiched board or fabrication.

## Measured placement

| obligation | measured | limit | result |
|---|---:|---:|---|
| U4.3 to J1.A5 on USB_CC1 | 1.9217 mm | 4.0 mm | PASS |
| U4.5 to J1.B5 on USB_CC2 | 3.0283 mm | 4.0 mm | PASS |
| U3.1 to C1.1 on VBUS_PROTECTED | 1.8750 mm | 2.5 mm | PASS |
| U3.5 to C2.1 on 3V3 | 1.8750 mm | 2.5 mm | PASS |

J1/U4 courtyards retain at least 0.225 mm separation and U3/C1/C2 retain at
least 0.330 mm. Minimum copper-to-outline clearance is 1.70 mm against the
0.30-mm rule; the GCT PCB-edge datum is exactly at y=85.0 mm. M3 head
envelopes retain at least 2.505 mm additional clearance.

The prepared r0 matches the corrected placements. All nine RF paths are
connected 0.295-mm F.Cu paths with zero RF vias and no copper, clearance or
edge collision. The current r0 quick denominator is 30 deliberately open
control/power items and 60 GND items deferred to fill/stitch, with zero copper
violations. Direct local ground returns, plane fill and route-following RF
fences remain mandatory later routing-stage work. The refreshed build-located
r0 DRC's 36 library-table warnings arise because that derived copy is outside
the project library context; final canonical DRC runs on the real board after
import/stitch.

Blocking findings: none.

## Targeted route-base renewal — legal endpoint escapes

Fresh independent inspection of exact r0 SHA-256
`cab54a0b9f9d304bdd9cf68c0d4ed756e8e93814dfe845db9de4e923756ca695`
finds P0/P1/P2 = 0/0/0. All added switch, CC, NRST, 3V3 and J11 dogbones are
on their declared nets and exact-collision-clean. R0 has 41 vias: nine
source-owned U1 exposed-pad vias plus 32 prep-added 0.45/0.20-mm vias. Zero
prep-added via centres land in SMD copper; the only via-in-pad construction is
the same nine filled/capped U1 EP field. Fresh DRC contains no short,
clearance, hole, annular or parity findings. Its 36 library-context and 41
pre-fill dangling-via reports remain non-copper-defect derived-input warnings.

RF geometry is unchanged: the saved board retains the identical 23-item RF
copper signature, all 0.295-mm F.Cu with zero RF vias. The source board and all
measured placement obligations above are unchanged. The updated route base is
therefore **SOUND** for one bounded five-wave retry, not for fabrication.

The first guarded retry was rejected before progress because KRT still tried
via-in-pad at U2.8, U2.9 and R6.1. The renewed route base fans the four U2
dogbones into separate legal sites at `(62.40,58.50)`, `(63.40,58.80)`,
`(64.40,59.20)` and `(65.40,59.70)` for V4 through V1, preserving physical
order, and adds separate 0.45/0.20-mm drops for R4.1/R5.1/R6.1/R3.2. The
exact-collision emitter accepts 34/34 banks and 78 items; fresh source-to-r0
comparison finds zero added vias in SMD lands. Fresh DRC has no short,
clearance, hole, annular or parity findings; only 36 derived-library warnings
and 45 expected pre-fill dangling vias. RF remains byte-structurally
unchanged. P0/P1/P2: none; **SOUND** for one new bounded switch-wave attempt.

That retry authenticated switch, Type-C and VBUS with clean per-wave geometry
reports, then the rail gate localized one forbidden via to R3.1. The renewal
adds only a 0.25-mm 3V3 dogbone from R3.1 `(68.00,57.01)` to a 0.45/0.20-mm
via at `(69.00,57.01)`, 1.02 mm centre-to-centre from the already reviewed
R3.2/SW_V4 companion via. The exact emitter accepts 35/35 banks / 80 items;
fresh prep reports zero added vias in SMD lands and fresh DRC has no copper,
clearance, hole, annular or parity findings. RF and source placement remain
unchanged. P0/P1/P2: none; **SOUND** for one bounded restart.
