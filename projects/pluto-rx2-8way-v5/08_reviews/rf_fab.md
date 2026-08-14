review_kind: RF_FAB
subject: pluto-rx2-8way-v5 exact Gerber/Excellon fabrication archive
date: 2026-08-13
reviewer: independent RF fabrication-output reviewer
independence: independent-from-design-author
evidence_scope: pinned local bytes only
source_commit: 9706143aea030b4e4ddddcd72e5e55293f3b19e8
artifact: 06_build/fab/pluto_rx2_8way_v5_gerbers.zip
artifact_sha256: 97ffb613eae98a02da959a5054629cf8daf3823fd376199f0b648f58eb548fd1
board_sha256: 39251c24d4b3cc878824f26c48178cbc4a4d418fa528045c6c13f2308e017acd
rf_contract_sha256: 101112345ca8b3f6e004b793badb92ae4891da3f54a83a6c42ecb8ddcd37d1c1
assembly_contract_sha256: b85a19f96355d42f2cc2b60d8d00e74551c035e6117c2d25b1f7ff7c37b4b341
fab_package_verdict: READY
physical_rf_performance_verdict: NOT_YET_MEASURED

# Exact-artifact RF fabrication review

requirement: RF-FAB-STACKUP PASS
requirement: RF-FAB-COPPER PASS
requirement: RF-FAB-DRILLS PASS
requirement: RF-FAB-FIRST-ARTICLE PASS

## Verdict and binding

The exact pinned archive is internally complete and locally consistent with
the exact reviewed board. It contains 13 valid, expected members: four copper
layers, two mask layers, two paste layers, two silkscreen layers, one outline,
one plated-drill file and one non-plated-drill file. A fresh export from the
bound board reproduced all 13 member names and all 13 member contents after
normalizing only KiCad creation timestamps. Fresh DRC evidence is zero
violations, zero unconnected items and zero schematic-parity findings.

This is a local package verdict, not permission to pay for an order. The JLC
uploader must echo the specified construction and special processes without
substitution. Nor is this a claim that fabricated hardware meets RF
performance: that remains a future first-article measurement gate.

## Stackup and impedance contract

- The archive carries copper outputs in the required order: F.Cu, In1.Cu,
  In2.Cu and B.Cu. The four-layer payload census finds copper pours on all
  four expected copper layers; no required plane output is blank or missing.
- The bound contract requires JLCPCB `JLC04161H-7628`, four layers, nominal
  1.6 mm thickness, F.Cu referenced to solid In1.Cu, 0.2104 mm dielectric
  height, and controlled impedance for the locked 0.295 mm / 0.20 mm CPWG
  geometry. The retained calculator result is 49.971863887 ohm.
- Gerber geometry cannot itself compel laminate choice, dielectric thickness,
  copper build or impedance service. Before payment, the JLC uploader/order
  preview must echo the exact stackup and controlled-impedance selection. A
  substituted stack, omitted impedance service or altered geometry is a stop.

## Copper and RF geometry

- The exact board has nine declared RF paths (`RF_COMMON` and `RF_ANT1` through
  `RF_ANT8`). Each is routed on F.Cu at 0.295 mm, and the RF paths contain zero
  vias. The corresponding fabrication output preserves the four-layer copper
  set and continuous inner reference-plane payloads.
- The package therefore preserves the locally reviewed topology: top-layer
  CPWG signal paths over In1.Cu, with no RF layer transition. This establishes
  fabrication-file continuity only; it does not replace impedance-coupon/TDR
  evidence or assembled-path VNA measurements.

## Drills and special processes

- The plated drill census contains the nine SMA signal holes at 1.50 mm and
  36 SMA ground-post holes at 1.70 mm. It also preserves two disjoint via
  families: 629 ordinary 0.20 mm drills and nine protected 0.25 mm drills in
  U1's exposed ground pad.
- The assembly contract requires copper-paste fill and copper cap on the
  complete 0.25 mm drill family only. The 629 ordinary 0.20 mm routing,
  stitching, fence and return vias must remain untreated. The drill files
  supply an unambiguous selector, but the JLC order must echo that selective
  treatment before payment; whole-board fill/cap or omitted protection is a
  stop.
- J2-J10 are through-hole `901-143-6RFX` SMA connectors. Their holes are in the
  archive, but assembly acceptance is separate: the uploader must identify
  exact C429844 for wave/manual through-hole assembly. Rejection or silent
  omission requires a distinct hand-solder release, not reuse of this CPL.

## First-article gate carried forward

The fabrication package passes this requirement because the RF contract has a
specific, non-inferential physical acceptance plan and the archive preserves
the geometry needed to execute it. It does **not** mean an article has passed.

After fabrication and assembly, retain calibrated Touchstone data at the SMA
mating-plane reference planes and measure every selected path from 100 MHz to
5.9 GHz. Acceptance requires: S21 loss no worse than 2.0 dB through 1 GHz and
3.5 dB at 5.9 GHz; maximum eight-path insertion-loss spread no greater than
1.5 dB at each retained frequency; common-to-off isolation at least 30 dB
through 4 GHz and 25 dB at 5.9 GHz in every required state; and active-path
S11/S22 return loss at least 10 dB across the band. Required off states and
paths must be measured rather than inferred. Control-state dwell timing also
requires an independent timebase. Operation outside the official AD9363 band
is article-specific and must not be represented as ADI-guaranteed.

## Findings and release boundary

- P0 fabrication-output defects: 0.
- P1 fabrication-output defects: 0.
- Local archive disposition: ready for the JLC uploader and order-preview
  review.
- Order stop conditions: missing or substituted `JLC04161H-7628`; missing
  controlled-impedance service; incorrect selective 0.25 mm fill/cap echo;
  rejection or omission of the nine exact C429844 through-hole placements; or
  any uploader geometry alteration.
- Production/performance release remains blocked until physical first articles
  pass the retained calibrated VNA and timing acceptance plan.
