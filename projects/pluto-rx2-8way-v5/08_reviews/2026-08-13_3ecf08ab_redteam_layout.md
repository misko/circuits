review_kind: redteam_layout
subject: Pluto RX2 8-Way v5 final exact adversarial layout 3ecf08ab
date: 2026-08-13
reviewer: redteam-agent (Codex GPT-5 layout, power-integrity, manufacturability and order lens)
independence: independent-from-design-author
context-given: exact final source/board plus exact RF, power, route, assembly, findings and JLC manufacturing sources
source_commit: 3ecf08abe5f44c098144abfc8cea31fc89354c59
board_sha256: 39251c24d4b3cc878824f26c48178cbc4a4d418fa528045c6c13f2308e017acd
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
p0_design_findings: 0
p1_design_findings: 0
p2_design_findings: 0
p1_order_release_controls: 4

# Final fresh adversarial layout, process and order review

## Verdict

The exact final source/board pair is **SOUND**. P0/P1/P2 design findings are
**0/0/0**: no connectivity, routing, RF-return, coupling, plane,
power-integrity, thermal, via-process, mechanical or manufacturability defect
was found. The corrected via construction, J2-J10 assembly ownership, current
STM32 manufacturer authority and findings-ledger closure are internally
consistent and machine-checkable.

The order verdict is **DO-NOT-ORDER**. Four grouped P1 release/order/
qualification controls remain below. They do not make the layout defective,
but none may be inferred from clean DRC or waived by this review.

## Independent exact-board evidence

- KiCad DRC with refill and schematic parity reports zero violations, zero
  unconnected and zero parity discrepancies. The board contains 242 tracks and
  638 vias, no duplicate or zero-length route, no coincident via site and no
  disconnected signal via. Every one of the 13 non-GND vias attaches on both
  used outer layers.
- P-PADSEP passes over 167 copper pads, 12,971 inter-footprint pad pairs and
  17,058 paste-to-foreign-copper pairs at the 0.09 mm floor. All 29 fitted
  footprints resolve a body. Advanced-tier preflight is 0 FAIL / 0 WARN.
- RF_COMMON and RF_ANT1-RF_ANT8 are individual 0.295 mm F.Cu paths with zero
  RF vias, branch, stub, loop, crossover or layer change. The length gate
  explicitly reports N-A because a sequential antenna selector declares no
  phase-match group.
- Final-chain-to-board guarding finds zero newly introduced SMD-land vias.
  Conservative hole/annulus checking reaches only U1's nine declared pad-25
  sites and no other SMD land, including corrected J11.3.

## RF return, planes and congestion

- In1.Cu and In2.Cu each contain one continuous filled GND polygon and no
  signal track. Every smaller F.Cu filled island has a local GND via or plated
  ground termination; no digital track cuts the In1 RF reference.
- All 18 route-local fence flanks pass, with 1.3979 mm worst aperture against
  the 1.4000 mm limit. U1 alternating perimeter grounds feed pad 25 and its
  protected field; each SMA supplies four plated ground posts.
- The radial arms diverge without an avoidable long parallel aggressor,
  digital crossover, fence incursion into the controlled gap, RF layer
  transition, or connector/mounting-hole choke point.

## Power integrity, thermal and process geometry

- VBUS_RAW/VBUS_PROTECTED use 0.30 mm F.Cu and 3V3 uses 0.25 mm F.Cu for only
  100 mA input hold and 20 mA rail load. U3 worst dissipation is 44.825 mW
  against a 238 mW ceiling.
- Supply bypass centres remain 1.875 mm at U3, 1.22 mm at U1 and 2.403 mm at
  U2, with nearby GND returns. U1's exposed pad has nine direct protected
  drops.
- All 638 vias are process-graded. Exactly nine U1 GND sites are filled/capped
  0.45/0.25 mm; all 629 routing, fence, stitch and return vias are untreated
  0.45/0.20 mm. The families are drill-disjoint, and fresh Excellon output
  preserves separate 0.20 and 0.25 mm tools.

## THT contract and source-document closure

The machine-readable `through_hole.process`, `.refs` and `.evidence` fields
cover exactly J2-J10. A fresh source-derived 29-placement candidate plus the
generated empty manifest passes A-POP with no THT-placeability finding and
0.00050 mm worst position-datum error. The external hard stop is unambiguous:
the real JLC uploader must accept exact C429844 for wave/manual assembly or
this release stops and a distinct hand-solder release is generated.

The official local ST DS13866 Rev 5 byte matches its dossier digest, and the
final `findings.yaml` closes V5-F2 with the retained STM32 and Amphenol
evidence. The focused revision comparison records no change to the pin,
supply, BOR, HSI48 or package facts consumed by this layout. The delta from
the preceding reviewed commit is documentation/governance only; the board
hash remains exact.

## Remaining P1 order and qualification controls

| ID | Open control | Required closure |
|---|---|---|
| V5-3EC-LAY-001 | No sealed release MANIFEST or final reviewed Gerber/drill/BOM/CPL archive exists; the temporary candidate is not order paperwork. | Generate the reviewed-commit release and exact RF-fab witness; rerun A-POP, M-BOM, twin, policy and freshness gates on shipped bytes. |
| V5-3EC-LAY-002 | The candidate exporter reports 14 placements across six LCSC codes with unsourced rotations, and U1 requires the single-channel A-POL human gate. | Source rotations, regenerate without escape hatches, and approve U1/D1/J1/J11/SMA orientation in the actual JLC preview. |
| V5-3EC-LAY-003 | JLC execution remains external: C429844 THT acceptance, JLC04161H-7628 controlled impedance, selective 0.25 mm U1 fill/cap, U1 MSL handling, and manufacturer-land acceptance are not yet uploader/DFM-proven. | Obtain explicit order-interface echoes before payment; any refusal or geometry substitution stops this release. |
| V5-3EC-LAY-004 | Same-day stock/allocation, the STM32 application/binary, decoder integration, and first-article rail, thermal, dwell and all-path VNA evidence do not yet exist. | Refresh stock for actual quantity, complete reproducible firmware/programming, and execute first-article acceptance before production claims. |

Severity summary: P0 design 0; P1 design 0; P2 design 0; P1 release/order/
qualification control groups 4. This exact layout may advance to release and
fabrication-package review, but it is not yet an order authorization.
