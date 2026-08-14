subject: Pluto RX2 8-Way v5 corrected exact-board placement and route-base renewal
date: 2026-08-13
reviewer: Codex fresh-context layout reviewer
context-given: current corrected v5 board and prepared route only
review_stage: pre-route
review_kind: layout
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
board_sha256: 3c11d72b004dad1d293f2774b2f90d193f3619de41e9a79997e46733bfda8393
design_rules_sha256: 36859a430335ab340763e1dec7161129bb95973d8ba2fd008ee94ecd2cb649b1
route_prep_sha256: b88e7388011cd2ef29484b6a586514e5b2f41a83d731c189e1db327ba1386b25

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

## Targeted post-route-cleanup renewal

Fresh review of the current rule digest replays `via_janitor` over the exact
promoted chain and finds exactly twelve candidate barrels, each attached on
F.Cu only. Removing them leaves the routed-net open count unchanged at zero
and preserves every F.Cu dogbone/trunk. The shared via-site screen now honors
realized pad-local copper and solder-mask expansion: it correctly rejects the
5-mm grid points beside FID1/FID2, whose 1.118-mm centre spacing is below the
1.325-mm copper requirement. Source board, r0, promoted chain, RF geometry and
all placement measurements above are unchanged. P0/P1/P2: none; **SOUND**.

The earlier exact-chain review correctly rejected a mere 0.060-mm cap overlap
at R3.1 as too fragile. The renewed source dogbone terminates on KRT's grid at
an assembly-safe 0.45/0.20-mm via centred `(68.80,57.00)`. KRT terminates its
F.Cu trunk one cell away at `(68.70,57.00)`. The generic normalization does not
pivot either route: it adds only that 0.10-mm same-net bridge, and only because
bridge distance plus 0.125-mm track radius fits exactly inside the existing
0.225-mm via radius, with no geometric tolerance. `via_janitor` may then remove the unused single-layer
barrel while the bridge and dogbone retain an explicit shared endpoint. The
focused fixture also refuses a 0.15-mm move that would enlarge copper. Final
saved-board evidence remains required after replay before fabrication.
