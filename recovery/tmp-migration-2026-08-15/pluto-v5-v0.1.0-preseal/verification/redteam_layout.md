review_kind: redteam_layout
subject: Pluto RX2 8-Way v5 final exact adversarial layout and J11-role rebind 4cf5c818
date: 2026-08-13
reviewer: redteam-agent (Codex GPT-5 layout, power-integrity, manufacturability and order lens)
independence: independent-from-design-author
context-given: exact final source/board plus exact RF, power, route, assembly, J11 dossier and JLC manufacturing sources
source_commit: 4cf5c818684e4c39f594b50a567fb086b9cf6f13
board_sha256: 39251c24d4b3cc878824f26c48178cbc4a4d418fa528045c6c13f2308e017acd
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
p0_design_findings: 0
p1_design_findings: 0
p2_design_findings: 0
p1_order_release_controls: 4

# Final fresh adversarial layout, source-role and order review

## Verdict

The exact source/board pair is **SOUND**. P0/P1/P2 design findings are
**0/0/0**: no connectivity, routing, RF-return, coupling, plane,
power-integrity, thermal, via-process, connector-role, mechanical or
manufacturability defect was found. P-ESC now grades all 13/13 dossiers and
J11's physical role agrees with both its model and mating explanation.

The order verdict is **DO-NOT-ORDER**. Four grouped P1 release/order/
qualification controls remain below. These are external release and execution
controls, not reasons to relabel a clean exact layout defective.

## Independent exact-board evidence

- KiCad DRC with refill and schematic parity reports zero violations, zero
  unconnected and zero parity discrepancies. The board contains 242 tracks and
  638 vias, no duplicate or zero-length route, no coincident via site and no
  disconnected signal via.
- P-PADSEP passes over 167 copper pads, 12,971 inter-footprint pad pairs and
  17,058 paste-to-foreign-copper pairs. All 29 fitted footprints resolve a 3D
  body. Advanced-tier preflight is 0 FAIL / 0 WARN.
- RF_COMMON and RF_ANT1-RF_ANT8 are individual 0.295 mm F.Cu paths with zero
  RF vias, branch, stub, loop, crossover or layer change. This sequential
  selector declares no phase-matched group, so the length gate correctly
  reports N-A rather than inventing a pass.
- Final-chain guarding finds zero newly introduced SMD-land vias. Conservative
  hole/annulus review reaches only U1's nine declared pad-25 sites and no other
  SMD land, including corrected J11.3.

## RF return, power and process integrity

- In1.Cu and In2.Cu each retain a continuous filled GND polygon with no signal
  track. Every smaller F.Cu island has a GND via or plated return. All 18
  route-local fence flanks pass at 1.3979 mm worst versus 1.4000 mm.
- VBUS uses 0.30 mm F.Cu and 3V3 uses 0.25 mm F.Cu for only 100 mA/20 mA
  declared loads. U3 worst dissipation is 44.825 mW versus a 238 mW ceiling.
  Bypass centres remain 1.875 mm at U3, 1.22 mm at U1 and 2.403 mm at U2,
  with nearby GND returns.
- All 638 vias are process-graded: nine filled/capped 0.45/0.25 mm U1 sites
  and 629 ordinary untreated 0.45/0.20 mm vias. The families are drill-
  disjoint and fresh Excellon output retains separate tools.

## J11 schema-role delta

The only part-source delta from the preceding reviewed board state is J11's
`mates` value changing from a cable-family description to the connector-role
schema's `plug`, plus an explicit note identifying the keyed FFSD-family cable
receptacle. Fresh P-ESC reports `13/13 part.yaml graded, 0 problem(s)`.

The dossier now matches the physical chain visible in the render:
board-side keyed male header/plug -> keyed 1.27 mm FFSD-family receptacle and
cable. The change does not touch the footprint, model, pin map, SWD nets,
connector keepout or board bytes. No new mechanical or electrical obligation
is introduced.

## THT contract and remaining order controls

The bought-THT process still covers exactly J2-J10 and passes A-POP on a fresh
29-placement candidate with a generated empty manifest; worst placement datum
is 0.00050 mm. The real JLC uploader must still accept exact C429844 for
wave/manual assembly or this release stops and a distinct hand-solder release
is generated.

| ID | Open control | Required closure |
|---|---|---|
| V5-4CF-LAY-001 | No sealed release MANIFEST or final reviewed Gerber/drill/BOM/CPL archive exists; the temporary candidate is not order paperwork. | Generate the reviewed-commit release and exact RF-fab witness; rerun A-POP, M-BOM, twin, policy and freshness gates on shipped bytes. |
| V5-4CF-LAY-002 | The candidate exporter reports 14 placements across six LCSC codes with unsourced rotations, and U1 requires the single-channel A-POL human gate. | Source rotations, regenerate without escape hatches, and approve U1/D1/J1/J11/SMA orientation in the actual JLC preview. |
| V5-4CF-LAY-003 | JLC execution remains external: C429844 THT acceptance, controlled impedance, selective 0.25 mm U1 fill/cap, U1 MSL handling, and manufacturer-land acceptance are not uploader/DFM-proven. | Obtain explicit order-interface echoes before payment; any refusal or geometry substitution stops this release. |
| V5-4CF-LAY-004 | Same-day stock/allocation, the STM32 application/binary, decoder integration, and first-article rail, thermal, dwell and all-path VNA evidence do not yet exist. | Refresh stock for actual quantity, complete reproducible firmware/programming, and execute first-article acceptance before production claims. |

Severity summary: P0 design 0; P1 design 0; P2 design 0; P1 release/order/
qualification control groups 4. This exact layout may advance to seal and
fabrication-package review, but it is not yet an order authorization.
