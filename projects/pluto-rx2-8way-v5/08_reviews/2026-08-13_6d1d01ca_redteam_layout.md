review_kind: redteam_layout
subject: Pluto RX2 8-Way v5 assembly-contract-renewed exact final layout 6d1d01ca
date: 2026-08-13
reviewer: redteam-agent (Codex GPT-5 layout, power-integrity, manufacturability and order lens)
independence: independent-from-design-author
context-given: exact commit board plus exact RF, power, route, assembly and JLC manufacturing sources
source_commit: 6d1d01cabb06301646136c6f729a027d8235160e
board_sha256: 39251c24d4b3cc878824f26c48178cbc4a4d418fa528045c6c13f2308e017acd
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
p0_design_findings: 0
p1_design_findings: 0
p2_design_findings: 0
p1_order_release_controls: 5
review_status: historical-superseded-before-seal

# Fresh adversarial layout, process and order renewal

## Verdict

The exact saved PCB is **SOUND**. I found no P0, P1 or P2 connectivity,
routing, RF-return, coupling, plane, power-integrity, thermal, via-process,
mechanical or manufacturability design defect. The new J2-J10 THT declaration
closes the prior source-level assembly-owner omission and is consumed correctly
by the assembly gate.

The order verdict remains **DO-NOT-ORDER**. Five grouped P1 release/order/
qualification controls remain below. They do not contradict the SOUND board
verdict, but none may be converted into an assumed pass. This review is
historical because commit `6d1d01ca` was scheduled to be superseded by an
evidence-only source commit before seal.

## Exact-board evidence and hidden-failure search

- KiCad 10.0.4 DRC with zone refill and schematic parity reports zero
  violations, zero unconnected items and zero parity discrepancies. The board
  contains 242 tracks and 638 vias, with no zero-length or exact-duplicate
  track, coincident via site or dangling signal via. Every one of the 13 non-
  GND vias has copper attached on both used outer layers.
- P-PADSEP passes over 167 copper pads, 12,971 inter-footprint pad pairs and
  17,058 paste-to-foreign-copper pairs at the 0.09 mm declared floor. Model
  coverage is 29/29. Advanced-tier preflight is 0 FAIL / 0 WARN.
- RF_COMMON and RF_ANT1-RF_ANT8 are individual 0.295 mm F.Cu paths with zero
  RF vias, no stub, branch, loop, crossover or layer change. Inter-path length
  matching is not a requirement for sequential antenna selection; the length
  gate explicitly grades zero declared phase groups rather than inventing one.
- Final-chain-to-board via-in-pad guarding reports zero newly introduced SMD-
  land vias. Conservative hole/annulus-to-SMD checking reaches only the nine
  declared U1 pad-25 sites and finds no other intersection, including J11.3.

## RF return, plane integrity and congestion

- In1.Cu and In2.Cu each have one continuous filled GND polygon and no signal
  track. F.Cu's main pour and all seven smaller islands have a local GND via or
  plated ground termination; B.Cu also remains connected. No digital route
  cuts the In1 RF reference.
- All 18 RF fence flanks pass, with 1.3979 mm worst aperture against the
  1.4000 mm limit. U1 alternating perimeter grounds feed pad 25 and its nine
  protected drops; every SMA provides four plated ground posts.
- The radial RF arms diverge without an avoidable long parallel aggressor,
  digital crossover, fence incursion into the controlled gap, or connector/
  mounting-hole choke point.

## Power integrity, via process and drill separation

- VBUS_RAW and VBUS_PROTECTED use 0.30 mm F.Cu; 3V3 uses 0.25 mm F.Cu. These
  have ample margin for the declared 100 mA input hold and 20 mA 3V3 load.
  U3 worst dissipation is 44.825 mW versus the 238 mW ceiling.
- Local bypass centres remain close: U3 input/output capacitors are each
  1.875 mm from their supply pad, U1's 100 nF is 1.22 mm from its supply, and
  U2's 100 nF is 2.403 mm from VDD. Each local return has a nearby GND via;
  U1's exposed pad has nine direct protected drops.
- All 638 vias are process-graded: exactly nine U1 GND vias are filled/capped
  0.45/0.25 mm, while all 629 ordinary routing, fence, stitch and return vias
  are untreated 0.45/0.20 mm. The drill families are disjoint. Fresh Excellon
  output carries separate 0.20 and 0.25 mm tools plus the intended connector,
  slot and mounting-hole families.

## Machine-readable THT contract and hard stop

The new `through_hole.process`, `through_hole.refs` and
`through_hole.evidence` fields are non-empty and cover exactly J2-J10. On a
fresh candidate BOM/CPL generated from this board, all 29 placements and the
nine paste-free SMA footprints pass A-POP after supplying the generated empty
population manifest; worst position-datum error is 0.00050 mm at J1. Removing
or failing to satisfy this declaration would expose each SMA as not SMT-
placeable.

The source also makes the external decision fail-closed: the real JLC uploader
must accept exact C429844 for wave/manual assembly on every J2-J10 row. If it
does not, this release stops. A hand-solder fallback is a separately generated
population contract and CPL, not an informal instruction.

## Remaining P1 order and qualification controls

| ID | Control still open at this commit | Required closure |
|---|---|---|
| V5-6D-LAY-001 | No sealed release MANIFEST or final Gerber/drill/BOM/CPL package exists. A source-derived candidate passes A-POP when given the generated empty manifest, but that temporary proof is not shipped order paperwork. | Generate the reviewed-commit release, generated MANIFEST line and exact RF-fab witness; rerun A-POP, M-BOM, twin, policy and freshness gates on the shipped bytes. |
| V5-6D-LAY-002 | The candidate exporter reports 14 placements across six LCSC codes with unsourced rotations: U3, J11, J2-J10, J1, U2 and D1. U1 additionally requires the single-channel A-POL human check. | Measure/source the rotations, regenerate without either escape hatch, and approve U1/D1/J1/J11/SMA orientation in the real JLC preview. |
| V5-6D-LAY-003 | JLC execution is not yet proven: C429844 THT acceptance, JLC04161H-7628 controlled impedance, selective fill/cap of only the 0.25 mm U1 family, U1 MSL handling, and exact manufacturer-land acceptance are external order-interface facts. Manufacturer SMA and J11 lands also differ from the distributor CAD variants. | Obtain explicit uploader/DFM echoes before payment. Any refusal or geometry substitution stops this release; connector process refusal requires the distinct hand-solder release. |
| V5-6D-LAY-004 | The local STM32 document retained by this exact commit identifies as DS13866 Rev 3 despite its legacy filename; the dossier refers to current Rev 5 online. This leaves the committed evidence cache behind its stated authority. | Commit the official Rev 5 byte, correct the legacy filename/record, and renew source-sensitive witnesses. No PCB geometry change is implied by the already-clean focused comparison. |
| V5-6D-LAY-005 | Same-day stock/allocation evidence, STM32 application firmware/binary, decoder integration, and first-article rail, thermal, dwell-timing and all-path RF/VNA evidence do not yet exist. | Refresh stock for the actual build quantity, complete reproducible firmware/programming evidence, and execute first-article acceptance before treating prototype results as production evidence. |

Severity summary: P0 design defects 0; P1 design defects 0; P2 design findings
0; P1 release/order/qualification control groups 5. The board may advance to
the next exact source-review and release stages, but this exact commit is not
an order authorization.
