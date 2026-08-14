review_kind: redteam_topology
subject: Pluto RX2 8-Way v5 renewed final exact topology, protection and ratings review
date: 2026-08-13
reviewer: Codex sub-agent /root/v5_escape_review (GPT-5 topology/protection lens)
independence: independent-from-design-author
source_commit: dae8320d3a5bab507a5846c7886ea719dc05ef61
schematic_sha256: 1abd0c209be27ac602f55f8e81cf25e4e98bb3a99a2fb76494fc8bbfcf20603b
board_sha256: 39251c24d4b3cc878824f26c48178cbc4a4d418fa528045c6c13f2308e017acd
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
via_process_verdict: PASS
p0_findings: 0
p1_design_findings: 0
p1_order_controls: 4
p2_findings: 2

# Renewed final adversarial topology, protection and ratings review

## Verdict and exact boundary

The exact schematic and corrected saved PCB identified above are **SOUND**.
Both are byte-identical to source commit `dae8320d`. I found no P0 or P1
electrical, protection, ratings or PCB-topology defect. The saved board
implements the approved one-of-eight receive selector, reset-safe state word,
power-only USB-C sink, fused/transient-protected regulator path and keyed SWD
interface without a schematic-to-board discrepancy.

The order verdict is **DO-NOT-ORDER**. Population/process declarations,
current-source evidence, firmware, final fabrication/release artifacts and
actual JLC uploader/DFM confirmation remain incomplete. These are real P1
order and qualification controls, not reasons to mislabel the corrected
copper topology defective.

## Independent exact-artifact evidence

- Fresh exact-schematic export passes 32/32 electrical invariants, 21/21
  label survival and 131/131 pin-map assertions. Schematic-to-PCB parity is
  zero-discrepancy over 22/22 nets, 131/131 connected nodes and 24/24
  intentional no-connects.
- Fresh KiCad DRC reports zero violations, zero unconnected pads, zero
  footprint errors and zero schematic-parity findings. Error-only ERC reports
  zero errors. Component/source count parity is 29/29 across the manifest,
  Circuit JSON, schematic and retained netlist.
- Power/protection grading passes both surge paths and both effective-
  capacitance banks. The 3V3 linear rail has 1.409 V minimum headroom versus
  250 mV dropout and about 45 mW worst-case dissipation versus the adopted
  238 mW ceiling. Rules audit passes 20/20; imported Pluto boundary facts pass
  3/3.
- Applicable placement gates pass with zero findings. Separate-footprint pad
  and paste separation passes over 167 copper pads, and all 29/29 fitted
  footprints have renderer-resolvable bodies. The deliberate stricter
  courtyard-inside-outline option is inapplicable to the edge-mating J1 and
  J2-J10 bodies; pad and body clearances, not connector courtyard overhang,
  are the adopted gate.
- Every RF route is one 0.295 mm F.Cu path with zero RF vias. The exact
  route-following GND fence passes 18/18 flanks; the worst aperture is
  1.3979 mm against the 1.4000 mm limit. The saved board embeds the intended
  four-layer 1.6 mm stackup, 0.2104 mm L1-L2 dielectric and ENIG finish.

## Corrected via-process contract

The prior ordinary-via-in-pad defect is not present in this artifact. A fresh
final-chain-to-board guard finds zero post-route vias introduced in SMD lands.
The independent process census grades all 638/638 vias and every 9/9 actual
via-in-pad site:

- nine U1 exposed-pad vias are 0.45/0.25 mm, individually `filling yes` and
  `capping yes`;
- 629 ordinary routing, stitching, fence and return vias are 0.45/0.20 mm
  with neither treatment;
- the protected and ordinary drill families are disjoint, no site is partial,
  and no other 0.25 mm drill via exists; and
- `assembly.yaml` names IPC-4761 Type VII filled/capped treatment, the
  item-level source, exact protected geometry, drill-family selector and a
  complete order remark requiring treatment of the 0.25 mm family only.

This is internally complete and machine-checkable. It still requires the
final drill package and JLC uploader/order echo to prove the fabricator bought
and interpreted that selective process correctly.

## End-to-end topology and ratings trace

`J2.1 -> RF_COMMON -> U1.22/RFC`; J3-J10 centre contacts connect in order to
U1 RF1-RF8. All connector shells, required U1 grounds and exposed pad 25 are
GND. U1.20 is an allowed no-connect. LS is hard-low; U2 PA0-PA3 own V1-V4.
R3 pulls V4 high and R4-R6 pull V1-V3 low, establishing valid-power all-off
`1000`. The zero-DC, 0 dBm RF boundary and absence of DC blocks, receiver
limiter and system-level connector ESD remain explicit accepted limitations.

J1 is a sink-only, power-only receptacle. Both CC pins retain independent
5.1 kohm Rd paths through U4; D+/D-/SBU are explicit no-connects. The supply
trace is `VBUS_RAW -> F1 -> VBUS_PROTECTED -> U3 -> 3V3`. D1 cathode/pad 1 is
on the protected positive node and anode/pad 2 is GND, so it does not forward-
clamp normal VBUS. U3 IN and EN are protected, OUT is 3V3, and its input/output
capacitors meet the effective minimum. The TVS is transient protection, not
sustained overvoltage cutoff, consistent with the approved requirement.

U2 power, return, reset, four control outputs and SWD pins agree with its
dossier. J11 exposes target-powered VTref, SWDIO, SWCLK, three grounds and
NRST on the keyed Cortex map. A Pi or ST-LINK must sense the self-powered
target and must not source J11.1. There is no Pluto control or power link.

## Findings

| ID | Severity | Finding | Required disposition |
|---|---|---|---|
| V5-DAE-RT-001 | Closed; no design defect | Exact parity, DRC, electrical invariants, protection arithmetic, RF routes/fence and corrected via-process census are green. | Preserve the hash-bound artifacts; any schematic, pad-net, route, via or stackup change requires renewed review. |
| V5-DAE-RT-002 | P1 order/process blocker | A fresh A-POP run now correctly exempts H1-H4, so the former mounting-hole prefix error is closed. Ten findings remain: no release MANIFEST `not_assembled:` line and J2-J10 are through-hole, paste-free connectors on an SMT CPL without the gate's machine-readable `through_hole: {process, refs, evidence}` declaration. | Before ordering, declare the bought THT/wave process with evidence or remove J2-J10 from SMT placement and control hand assembly; regenerate the final BOM/CPL/MANIFEST and rerun A-POP. |
| V5-DAE-RT-003 | P1 evidence/freeze blocker | The locally retained STM32 document is older than current ST DS13866 Rev 5. Manufacturer Samtec lands differ from JLC C2932107 CAD, and Amphenol SMA drills differ by 0.10 mm from JLC C429844 CAD. | Capture/recheck current ST Rev 5. Preserve manufacturer lands and obtain explicit JLC DFM/assembly acceptance; geometry changes invalidate this review. |
| V5-DAE-RT-004 | P1 fab/release/order blocker | No final sealed Gerber/drill/BOM/CPL package, exact-Gerber RF fab review, MANIFEST, same-day stock evidence, uploader allocation echo or order preview exists. The board embeds the intended stackup and the selective-via remark is complete, but neither proves JLC execution. | Generate and independently review the exact final package; confirm JLC04161H-7628 controlled impedance, selective 0.25 mm U1 fill/cap processing, connector lands, orientations and THT disposition before payment. |
| V5-DAE-RT-005 | P1 firmware/functional blocker | `05_firmware` contains generated profile consumers and instructions but no STM32 application source, reproducible build, tests or binary. No article demonstrates BOR/watchdog recovery, atomic writes, timing inference, programming, rail/thermal behavior or RF performance. | Implement/build/test/flash firmware and decoder, then complete first-article timing, power, thermal and all-path VNA acceptance. |
| V5-DAE-RT-006 | P2 accepted interface risk | U1 all-off is guaranteed only at valid VDD. SMA centres have no DC blocks, receiver limiter or system-level IEC ESD network. | Preserve zero-DC, 0 dBm and controlled-ESD operating limits; redesign if biased antennas, high power, guaranteed power-off isolation or connector-level immunity becomes required. |
| V5-DAE-RT-007 | P2 process debt | Raw ERC has 190 warnings despite zero errors and independently exact connectivity. | Retain the warning baseline and improve producer/library/grid presentation later; never suppress a new warning merely because this baseline is noisy. |

## Severity summary

- P0: 0.
- P1 electrical/protection/ratings/PCB-topology design defects: 0.
- P1 order, evidence, release and functional-qualification controls: 4.
- P2 accepted interface/process risks: 2.

The corrected board may advance to the remaining final lenses and fabrication-
package generation. It is not ready to order, and this design verdict is not
physical or production performance evidence.
