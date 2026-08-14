review_kind: redteam_layout
subject: Pluto RX2 8-Way v5 exact final layout with current STM32 evidence 770ac064
date: 2026-08-13
reviewer: redteam-agent (Codex GPT-5 layout, power-integrity, manufacturability and order lens)
independence: independent-from-design-author
context-given: exact commit board plus exact RF, power, route, assembly, evidence and JLC manufacturing sources
source_commit: 770ac0640aadd2558ea98271a2589d2b8785e598
board_sha256: 39251c24d4b3cc878824f26c48178cbc4a4d418fa528045c6c13f2308e017acd
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
p0_design_findings: 0
p1_design_findings: 0
p2_design_findings: 0
p1_order_release_controls: 4
review_status: historical-superseded-before-seal

# Fresh adversarial layout, process and order renewal

## Verdict

The exact saved board is **SOUND**. P0/P1/P2 design findings are **0/0/0**:
no connectivity, routing, RF-return, coupling, plane, power-integrity,
thermal, via-process, mechanical or manufacturability defect was found. The
THT ownership source and the official local STM32 Rev 5 authority are both
complete at this commit.

The order verdict is **DO-NOT-ORDER**. Four grouped P1 release/order/
qualification controls remain below. This review is historical because
`770ac064` was superseded by a findings-ledger-only source commit before seal.

## Independent exact-board evidence

- DRC with refill and parity is 0 violations / 0 unconnected / 0 parity.
  There are 242 tracks, 638 vias, no duplicate or zero-length route, no
  coincident via and no disconnected signal via. All 13 non-GND vias attach to
  copper on both used outer layers.
- P-PADSEP passes over 167 copper pads, 12,971 inter-footprint pad pairs and
  17,058 paste-to-foreign-copper pairs. Model coverage is 29/29. Advanced-tier
  preflight is 0 FAIL / 0 WARN.
- All nine RF nets are 0.295 mm F.Cu-only paths with zero RF vias, branch,
  stub, loop, crossover or layer change. The length gate correctly reports
  N-A because this sequential selector declares no phase-match group.
- Both inner layers retain continuous GND polygons with no signal tracks.
  All 18 RF fence flanks pass at 1.3979 mm worst versus 1.4000 mm. No digital
  track cuts the In1 reference.
- Final-chain guarding finds zero newly introduced SMD-land vias. The complete
  census is nine filled/capped 0.45/0.25 mm U1 vias and 629 untreated
  0.45/0.20 mm ordinary vias, with drill-disjoint families and zero partial
  process sites.
- VBUS copper is 0.30 mm and 3V3 is 0.25 mm for only 100 mA/20 mA declared
  loads. U3 dissipates 44.825 mW against 238 mW. Local supply bypass distances
  remain 1.875 mm at U3, 1.22 mm at U1 and 2.403 mm at U2, with nearby returns.

## THT and current manufacturer evidence

`through_hole.process`, `.refs` and `.evidence` cover exactly J2-J10 and are
consumed by A-POP. A fresh 29-placement candidate plus the generated empty
manifest passes A-POP; no paste-free SMA is misclassified as SMT-placeable.
The external hard stop remains: the real uploader must accept exact C429844
for wave/manual assembly or this release stops and a distinct hand-solder
release is generated.

The official 97-page ST DS13866 Rev 5, February 2026, is locally retained at
the digest named by the STM32 dossier. A focused Rev 3-to-Rev 5 comparison is
recorded clean for the consumed pin, supply, BOR, timing and package facts.
This closes the prior committed-evidence-cache blocker without a PCB change.

## Remaining P1 order and qualification controls

| ID | Open control | Closure required |
|---|---|---|
| V5-770-LAY-001 | No sealed release MANIFEST or final Gerber/drill/BOM/CPL archive exists; the temporary candidate is not order paperwork. | Generate the reviewed-commit release and exact RF-fab witness; rerun A-POP, M-BOM, twin, policy and freshness gates on shipped bytes. |
| V5-770-LAY-002 | The candidate exporter reports 14 placements across six LCSC codes with unsourced rotations, and U1 requires the single-channel A-POL human gate. | Source rotations, regenerate without escape hatches, and approve U1/D1/J1/J11/SMA orientation in the actual JLC preview. |
| V5-770-LAY-003 | JLC execution remains external: C429844 THT acceptance, controlled impedance, selective 0.25 mm U1 fill/cap, U1 MSL handling, and manufacturer-land acceptance are unconfirmed. | Obtain explicit uploader/DFM echoes before payment; any refusal or geometry substitution stops this release. |
| V5-770-LAY-004 | Same-day stock/allocation, the STM32 application/binary, decoder integration, and first-article rail, thermal, dwell and all-path VNA evidence do not yet exist. | Refresh stock for actual quantity, complete reproducible firmware/programming, and execute first-article acceptance before production claims. |

Severity summary: P0 design 0; P1 design 0; P2 design 0; P1 release/order/
qualification control groups 4. The layout may advance, but this exact commit
is not an order authorization.
