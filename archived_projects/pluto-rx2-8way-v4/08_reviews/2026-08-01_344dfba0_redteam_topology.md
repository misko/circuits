# Fresh-context adversarial topology / protection review

subject: pluto-rx2-8way-v4 344dfba0
date: 2026-08-01
reviewer: redteam-agent (topology/protection/ratings lens)
context-given: full-tree
review_type: redteam_topology
review_date: 2026-08-01
reviewer_context: fresh; prior reviews, journals, learnings, and STATUS were not read
source_commit: 344dfba05f7160b99b56dc9722cf8be72e846c7e
board_sha256: 4a5e69d474f5354346edbb64683edb3c69946b9ad437c1ddf49e4b126fc7f14a
fab_zip_sha256: 4f1d2fea756f86220cb8c8dc2712198f4df0d306d6cd9a174587293f8b0e494d
design_verdict: SOUND
order_verdict: DO-NOT-ORDER

## Executive verdict

The frozen carrier topology is electrically coherent and implements the
declared module-first architecture. I found **no P0 design defect**. The
PE42482 pin map and truth table agree with the committed vendor PDF; the
exported netlist connects GP0..GP3 through four independent 100-ohm source
resistors to V1..V4, places four 10-kohm pull-downs on the switch side, grounds
LS/NC/EP as intended, and routes RF1..RF8/RFC to the declared connector nets.
The firmware's non-linear GPIO codes `{0,4,2,6,1,5,3,7}` correctly compensate
for V1 being the mux MSB while GP0 is the PIO word LSB. V4=`1`, V1..V3=`0`
implements the all-ports-terminated state.

The design may be sealed as a **sound design**, but the present candidate must
not be ordered yet. Catalog sourcing is clear (11/11 BOM lines pass for the
five-board quantity); the hold is instead the documented vendor-process,
freshness, and physical-qualification work: plug-in assembly acceptance for
the ten SMA jacks, POFV/controlled-impedance production-file acceptance,
uploader polarity/BOM echo, refreshed exact-artifact seal evidence, and the
first physical module/USB/thermal checks.

## Exact subject and methods

- MEASURED: the working source folders `01_docs`, `02_parts`, `03_src`,
  `03_tscircuit`, and `04_kicad` have no diff from the stated source commit.
- MEASURED: the board and fabrication archive reproduce the hashes in the
  provenance header above.
- MEASURED: fresh KiCad 10 ERC returned exit 0 and 0 violations; fresh full
  DRC with refill and schematic parity returned 0 violations / 0 unconnected /
  0 parity.
- MEASURED: `net_label_survival.py` passed 23/23 labels;
  `electrical_invariants.py` passed 25/25 assertions; `count_parity.py` passed
  all four source pairs over 28/28 refdes; the staged BOM source check passed
  with 7/7 R/C rows value-graded and 11 BOM rows present.
- MEASURED: `power_topology.py` passed 1/1 rail. At the declared corners the
  linear rail has 1384 mV headroom versus 250 mV dropout, 252 mW dissipation
  versus the declared 400 mW supported-envelope budget, and 934 mV load
  headroom versus a 12 mV delivery drop after the gate's 1.2 factor. E-OFF is
  correctly N-A for an externally USB-powered board de-energized by unplugging.
- MEASURED: the native control-core test passed, including the eight state
  codes, 62,464 nominal-sample frame arithmetic, and all-off code; the eight
  host protocol tests also passed.
- MEASURED independently from pSemi DOC-75785-4 pages 10 and 20: LS=0,
  V4=0 selects RF1..RF8 with `n-1 = 4*V1 + 2*V2 + V3`; V4=1 with V1..V3=0
  terminates all ports; LS has the documented internal pull-up; pins 2/4/6/
  13/15/17/19/22/24 are RF2/RF3/RF4/RF5/RF6/RF7/RF8/RFC/RF1.

## Independent topology trace

### RF and connector mapping

The exported netlist traces J_ANT1..J_ANT7 signal pad 1 to U_SW RF1..RF7,
respectively. J_ANT8 and J_RX1 share `RX1_MAIN`; the branch is exactly
`RX1_MAIN -> R_T1 (220) -> RX1_TAP_MID -> R_T2 (220) -> RX1_TAP -> U_SW.19
(RF8)`. U_SW.22 (RFC) connects only to J_RX2 signal pad 1. Every SMA pad 2..5
is GND. This agrees with the KH-SMA-KE-Z dossier's centre-signal/four-ground-
post drawing and with the stated passive, 50-ohm, 0-VDC system boundary.

### Control and safe state

U_MCU pins 1..4 are GP0..GP3 and connect through R_S1..R_S4 to U_SW pins
9..12 (V1..V4). R_PD1..R_PD4 each connect from the corresponding switch-side
node to GND. Reset/module-absent behavior is therefore V1..V4=`0000`, which
selects RF1 with LS tied low; it is deterministic but intentionally not mute.
The explicit `OFF` command writes `0x08`, the documented all-isolated code.
The 100-ohm/10-kohm network remains well inside the cited switch control
thresholds at the declared 3V3 corners.

### Power, protection, and module boundary

The only carrier supply path is U_MCU pin 21 (`3V3_MOD`) through FB_3V3 to
filtered `3V3`, then U_SW pin 8 and C_BULK/C_SW1/C_SW2. U_MCU pin 23 (the
module's USB VBUS/5V castellation) is explicitly no-connect, so the carrier
does not create a second USB/power path or backfeed route. The module owns USB
entry protection and regulation. There is no battery or stored-energy source.
The lack of RF shunt ESD is deliberate and bounded by the documented
ESD-controlled, passive receive-only, 0-VDC, +18-dBm-CW use envelope; it is not
silently presented as a field-hardened interface.

### Population boundary

U_MCU is absent from BOM, CPL, and paste and is declared user-supplied. The
candidate contains 27 placed rows and five declared unpopulated refs (H1..H4
and U_MCU). All ten SMA jacks remain on the CPL as JLC plug-in parts, rather
than being silently treated as reflowable or omitted.

## Findings

| Finding | Severity | Evidence | Disposition |
|---|---|---|---|
| RT-TOP-001 — The advertised sample counts are a **nominal local PIO cadence**, not absolute Pluto ADC sample boundaries. There is no Pluto sample-clock/trigger input on the carrier, and the RP2040 divider free-runs from the module crystal. | P1 bring-up / requirement boundary; not a carrier defect under binding A3 | BRIEF G3/G4 state the sample arithmetic while A3 explicitly preserves the free-running PIO model. Firmware README states `sync=FREE_RUNNING`, reports requested and quantized rate, and disclaims exact Pluto sample-index alignment. | Keep the non-claim prominent. Before accepting timed operation, measure drift using the RX1 reference marker and calibrate the requested rate. If phase-locked sample boundaries become a requirement, this hardware needs a shared clock/trigger revision; USB timing cannot substitute for it. |
| RT-TOP-002 — The present JLC order still depends on vendor-process confirmation that catalog/geometry checks do not prove. | P1 order blocker; not a design blocker or sourcing shortfall | Stock evidence is PASS, 11/11, including C504007 as `Plugin`. The assembly rule itself records `assemblyProcess: null` and says availability of the through-hole line for this order is not proven. The design also requires board-wide filled/capped vias, ten specifically audited via-in-pad sites, the 1.2-mm advanced-via stack, and controlled impedance without silent geometry edits. | Before payment obtain written plug-in acceptance for all ten SMA jacks and DFM acceptance of filling/capping and the ten U_SW sites; confirm JLC04121H-7628, 0.25/0.15-mm advanced vias, impedance coupon/TDR, and production plots. A declined SMA process requires a revised BOM/CPL and a new review/seal. |
| RT-TOP-003 — Exact-artifact release evidence is not yet fresh enough to support an order. | P1 release blocker; not an electrical defect | Current board hash is `4a5e69...`; `06_build/layout_seal.json` still binds an earlier board hash `dbbb3f...`. The current `policy_audit.md` predates the final board/fab regeneration and still contains an A-POP failure caused by a missing release MANIFEST declaration. | Regenerate the layout-seal/policy/release battery against this exact board and staging archive. Do not copy the stale files into the release. Confirm U_SW/LED orientation, uploader BOM echo, and the single-channel U_SW rotation preview in the actual order UI. |
| RT-TOP-004 — Physical module integration is intentionally outside automated PCBA and remains unqualified on hardware. | P1 first-article qualification; not a schematic defect | Vendor STEP evidence shows carrier-facing parts up to 1.000 mm proud. The module has no direct-reflow seating plane; the design therefore excludes it from paste/CPL and requires an insulating edge-support fixture, positive-gap inspection, and hand solder. The 125-mA / 50-C rail envelope uses a conservative analytical thermal model rather than a measured module theta-JA. | Before hardware acceptance, perform sample metrology, gap/parallelism and joint inspection, resistance checks, 3V3 rail/current/case-temperature tests with representative firmware and WS2812 dark, USB enumeration in both cable orientations, and flash/control tests. |
| RT-TOP-005 — The E-ADR coverage result is vacuous and the invariant-to-ADR labels contain stale semantics. | P2 process debt | The live command reports `E-ADR OK: 0/0` despite four accepted design decisions and 25 invariants. In `electrical_invariants.yaml`, RF-port/tap assertions are labelled ADR-0001 although the decision register assigns the RF switch/tap to ADR-0003; the closing comment calls ADR-0003 the stackup although that is ADR-0004. Only R_PD1's value is asserted explicitly, even though R_PD2..R_PD4 are equally load-bearing. The actual BOM presently has all four at 10 kohm and the BOM/source check passes. | Repair the review-gate metadata in the next process change: make E-ADR discover the decisions, remap assertions to the correct ADR IDs, and add value assertions for R_PD2..R_PD4. This does not require changing the frozen netlist or copper. |

## Severity summary

- P0: 0
- P1: 4, all explicitly classified as bring-up/order/release qualifications
  rather than latent schematic defects
- P2: 1 process-coverage finding

## Order and first-article gates

Catalog sourcing is **CLEAR at the recorded query**: 11/11 coded lines pass
for five boards, including 1,284 PE42482A-X and 22,674 KH-SMA-KE-Z. The stock
record correctly says it does not predict JLC allocation, so the uploader echo
and order-day recheck remain mandatory. The current `DO-NOT-ORDER` verdict is
therefore not `BLOCKED-SOURCING`; it is driven by RT-TOP-002 through -004.

After the vendor/process/freshness gates clear, the first article still needs
the already-declared POFV joint inspection, module metrology and rail/thermal
checks, USB and RX2CTL/1 exercise, all eight states plus all-off verification,
and VNA measurement of insertion loss, return loss, isolation, RX1 tap/main
loss, and phase. Those measurements qualify the physical implementation; they
do not reverse the topology verdict above.
