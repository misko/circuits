review_kind: redteam_topology
subject: Pluto RX2 8-Way v5 true-final exact topology, protection and order review
date: 2026-08-13
reviewer: Codex sub-agent /root/v5_escape_review (GPT-5 topology/protection lens)
independence: independent-from-design-author
source_commit: 770ac0640aadd2558ea98271a2589d2b8785e598
schematic_sha256: 1abd0c209be27ac602f55f8e81cf25e4e98bb3a99a2fb76494fc8bbfcf20603b
board_sha256: 39251c24d4b3cc878824f26c48178cbc4a4d418fa528045c6c13f2308e017acd
stm32_rev5_sha256: e392b1542086b25f6bcb8856b6c0467aa3ec10e31f03bdafca74796485c531fe
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
evidence_lifecycle_verdict: PASS
findings_ledger_verdict: STALE
via_process_verdict: PASS
assembly_contract_verdict: PASS
p0_findings: 0
p1_design_findings: 0
p1_order_controls: 4
p2_findings: 2

# True-final adversarial topology, protection and order review

## Verdict and exact boundary

The exact schematic and PCB are **SOUND**, byte-identical to commit
`770ac064`, and contain no P0/P1 electrical, protection, rating or routed-
topology defect. The evidence delta is also technically sound: official local
ST DS13866 Rev 5 is correctly hash-bound, while the older byte copy is retained
under its actual Rev 3 identity.

The order verdict remains **DO-NOT-ORDER**. Final population/release evidence,
JLC order interpretation, firmware and first-article qualification remain
open. In addition, the machine-readable findings ledger still describes the
now-closed STM32 document gap as open, so project maturity cannot advance until
that stale governance record is dispositioned.

## Exact evidence and STM32 comparison

- ST Rev 5 directly confirms TSSOP-20 pins 1-20, including VDD/VDDA pin 4,
  VSS/VSSA pin 5, PF2/NRST pin 6, PA0-PA3 pins 7-10, PA13/SWDIO pin 18 and
  PA14/BOOT0/SWCLK pin 19. It confirms 2.0-3.6 V supply, BOR4 rising
  2.80-3.00 V/falling 2.70-2.90 V, HSI48 -1/+1% at 0-85 C and -2.5/+2% over
  -40 to 125 C, and TSSOP-20 6.5 x 4.4 mm at 0.65 mm pitch. Focused Rev 3
  comparison shows these consumed facts unchanged.
- Fresh schematic export passes 32/32 invariants, 21/21 labels and 131/131
  pin maps. Exact schematic/PCB parity is zero-discrepancy over 22 nets,
  131 nodes and 24 no-connects. Component parity is 29/29.
- Fresh DRC reports zero violations, unconnected pads, footprint errors and
  parity findings. Error-only ERC has zero errors.
- Both surge paths, both effective-capacitance banks and the 3V3 rail pass.
  The LDO has 1.409 V minimum headroom versus 250 mV dropout and about 45 mW
  worst-case dissipation versus the adopted 238 mW ceiling.
- Rules audit passes 20/20; placement, pad/paste separation and 29/29 body-
  model coverage pass. Nine RF paths remain stub-free 0.295 mm F.Cu with zero
  RF vias; their fence passes 18/18 flanks, worst 1.3979 mm versus 1.4000 mm.
- Via-process grading covers 638/638 vias and all 9/9 via-in-pad sites: nine
  U1 0.45/0.25 mm vias are filled/capped, 629 ordinary 0.45/0.20 mm vias are
  untreated, drill families are disjoint and no new routed via-in-pad exists.

## Population and order boundary

The machine-readable J2-J10 through-hole contract remains effective. Fresh
A-POP recognizes all nine exact THT refs and reports none of the former
paste-free-on-SMT-process findings. H1-H4/FID1-FID3 are declared exemptions;
29 CPL rows agree with their pad-array centres, worst 0.00050 mm at J1; there
is no unexplained population delta. The only A-POP finding is the absent final
release MANIFEST `not_assembled:` line. The contract correctly requires an
uploader stop if exact C429844 is not accepted for wave/manual assembly.

## End-to-end topology trace

J2.1 connects through `RF_COMMON` only to U1.22/RFC; J3-J10 centres connect in
order to RF1-RF8. SMA shells, required U1 grounds and pad 25 are GND; U1.20 is
allowed NC. LS is low; PA0-PA3 own V1-V4. R3 high plus R4-R6 low establishes
valid-power all-off `1000`. RF remains zero-DC and 0 dBm operator-limited.

J1 is a sink-only power input with independent 5.1-kohm CC Rd paths; USB
data/SBU are no-connects. Power is `VBUS_RAW -> F1 -> VBUS_PROTECTED -> U3 ->
3V3`. D1 cathode is protected-positive and anode is GND. The TVS is transient
protection, not active sustained-overvoltage cutoff. J11 is the target-powered
keyed Cortex SWD map; the programmer must not source the board.

## Findings

| ID | Severity | Finding | Required disposition |
|---|---|---|---|
| V5-770-RT-001 | Closed; no design defect | Exact connectivity, protection arithmetic, RF routing/fence, stackup and via process are green. | Preserve exact hashes; artifact changes require renewal. |
| V5-770-RT-002 | Closed evidence / P1 governance blocker | Official local ST Rev 5 now satisfies V5-F2's closure condition, but `01_docs/findings.yaml` still marks V5-F2 open and describes the old document state. | Correctly close V5-F2 with Rev 5/dossier evidence before claiming DESIGN_CLEAN; do not reinterpret the stale open row silently. |
| V5-770-RT-003 | P1 population/order blocker | THT ownership passes, but no final MANIFEST line or JLC uploader acceptance of exact C429844 wave/manual assembly exists. | Generate final BOM/CPL/MANIFEST, rerun A-POP, and require uploader acceptance or stop for a distinct hand-solder release. |
| V5-770-RT-004 | P1 fab/release/order blocker | No sealed Gerber/drill/BOM/CPL package, exact-Gerber RF review, same-day stock, uploader echo or order preview exists. Samtec/JLC lands and Amphenol/JLC SMA drills still require explicit DFM acceptance. | Generate/review the package and confirm stackup, impedance, selective fill/cap, allocation, geometry, orientation and process before payment. |
| V5-770-RT-005 | P1 firmware/functional blocker | Generated profile consumers exist, but no STM32 application source, reproducible build, tests or binary; no article proves timing, BOR/watchdog, power, thermal or RF behavior. | Implement/build/test/flash, then execute all first-article timing, rail, thermal and VNA tests. |
| V5-770-RT-006 | P2 accepted interface risk | U1 all-off requires valid VDD; SMA centres lack DC blocks, an RF limiter and system-level IEC ESD protection. | Preserve zero-DC, 0 dBm and controlled-ESD limits; redesign if scope expands. |
| V5-770-RT-007 | P2 process debt | Raw ERC retains 190 presentation/library warnings despite exact connectivity and zero errors. | Reduce producer noise later and never mask a new warning in the baseline. |

## Severity summary

- P0: 0.
- P1 electrical/protection/ratings/PCB-topology defects: 0.
- P1 governance, order, release and functional controls: 4.
- P2 accepted interface/process risks: 2.

The design may advance after governance and release controls close. It is not
ready to order, and this review is not physical performance evidence.
