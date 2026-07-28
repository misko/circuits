# Journal — 03 design docs / ADRs / rules (pluto-rx2-8way)

## 2026-07-28 09:10 — start (stage 1-3 entry)

- did: read the binding canon (CLAUDE.md, pcb-design SKILL stages 1-3 +
  D-SPEC/D-ESC/D-TIER/D-LAYOUT/D-ADJ + journal/beacon discipline,
  design-policies.md, every project `contracts.md`), the commission
  (`4caf0d6`) and the D-SPEC sourcing spike (`150a869`), then measured the
  gate baseline before writing anything.
- result: BASELINE, measured, not assumed —
  `contracts_audit.py` **243 files, 0 violations**;
  `policy_audit.py projects/pluto-rx2-8way` **FAIL=3, HUMAN=6, N-A=25, PASS=6**
  with the three FAILs being **P-TIER** (`fab_tier: jlc_2layer_default` vs
  PE42482A-X needing `jlc_4layer_advanced`), **E-INV** (no exported netlist —
  a stage-4 artifact) and **E-TOPO** (the TEMPLATE `power_tree.yaml` still
  names `LM5116MHX-NOPB`, a converter that is not in this board's `02_parts`).
  `electrical_invariants.py --adr-coverage` = **E-ADR OK 0/0** — there are no
  ADRs at all yet, so the loop is closed over an empty set.
  `03_src/floorplan.yaml`, `route.yaml` and all three `rules/*.yaml` are still
  VERBATIM skill templates describing `cook_loadcell` / a 3S-LiPo board.
- next: user has CONFIRMED D3 with the split-arm variant (2x 220R). Write the
  ADRs (T1 Ku deferral, T2 coupler refuted + pickoff adopted, D-TIER,
  input-protection posture, the D4 phase/loss policy, the radial-star
  floorplan), then ARCHITECTURE + DETAIL_DESIGN, then replace the three
  template `rules/` files, then re-measure every gate.

## 2026-07-28 10:20 — iterate 1 (standalone gap closed; a resistor with two stock numbers)

- did: attacked the two OWED datasheets before writing anything that would cite
  them, then re-verified the confirmed pickoff part's identity and stock rather
  than inheriting the spike's figures.
- result, three findings:
  1. **The LCSC `datasheet.lcsc.com/lcsc/<id>_<part>_<code>.pdf` URLs now serve
     an HTML LANDING PAGE**, to a browser User-Agent as well as to a plain
     fetch — which is what defeated the spike. The real document is behind a
     CDN link embedded in that page's own markup
     (`datasheet.lcsc.com/datasheet/pdf/<hash>.pdf`). Both PDFs fetched that
     way and COMMITTED. The SMA sheet hashes to
     `05257621aa124d9a077a47230c4ffc0030b23477c0e5c5e694abffa5f8daee08` — byte
     for byte the value `02_parts/README.md` had recorded as EXPECTED on
     2026-07-27 from the sibling's read-only copy. Independent fetch, prior
     hash, agreement: that is a confirmation, not a copy.
  2. **C25091 = `0402WGF2200TCE`, 220 ohm +/-1% 62.5 mW** — confirmed from the
     LCSC product record AND decoded from the UniOhm series sheet's own
     ORDERING PROCEDURE (section 3, p2): `0402 / WG = 1/16 W / F = +/-1% /
     2200 = 220 with no trailing zeros`. Every electrical fact in both resistor
     dossiers is now CITED from a document instead of from a parametric record.
  3. **THE POOL TRAP, and it nearly read as a blocker.** The LCSC RETAIL
     product page for C25091 reports **stock 0** on 2026-07-28. The JLCPCB
     ASSEMBLY parts library reports the same code as `base` with **995,162**.
     Two different pools; a PCBA order allocates from the assembly one.
     Measured with `jlc_stock_check.py`: C25091 995,162 / C25117 1,871,945 /
     C5121458 1,498 / C504007 18,585 (19,136 the day before — -551 in a day).
- next: the ADRs.

## 2026-07-28 11:05 — iterate 2 (T3: the finding that the tap value cannot fix)

- did: while writing the ADR for the confirmed pickoff, computed what a
  -20 dB tap does to the REFERENCE dwell's signal-to-interference ratio. T2 had
  only ever optimised RX1's sensitivity.
- result: **NEW SPEC TENSION T3.** On the reference dwell RF8 carries the tapped
  copy at -20.26 dB (relative to a plain antenna port) while the seven LIVE
  antennas leak into RFC at full strength through finite isolation. Power-summing
  the guaranteed-minimum isolation column (Table 3, PDF p5):
  SIR = **+34.7 / +20.2 / +14.4 / +7.8 / +1.2 dB** across the five in-band rows,
  i.e. worst-case coherent phase pull 1.1 / 5.6 / 11.0 / 23.9 / **60.1 deg**.
  Ordinary antenna dwells are FINE at **+21.7 dB / 4.75 deg** — which reproduces
  the spike's own -21.5 dB figure by an independent route, so the method checks
  out before it is used on the new case.
  **NO TAP VALUE FIXES IT:** 2x220R +1.2 dB, single 220R +6.1, a matched 6 dB
  split +15.5, an ideal lossless 3 dB split +18.5. The ceiling is the seven live
  ports' aggregate isolation. So the confirmed 2x220R is KEPT — it spends
  0.43 dB of a PERMANENT quantity (RX1 sensitivity) to give up ~5 dB of a
  RECOVERABLE one — and the fix is that the interference is COMPUTABLE from the
  same frame's other seven dwells, which the absorptive switch makes constant.
  A zero-board-cost lever stays available: `R_T2` populated as 0 ohm is a BOM
  change worth +4.84 dB for 0.337 dB.
- next: finish the ADR set and the design docs.

## 2026-07-28 12:40 — iterate 3 (the octagon is the connector's shadow)

- did: adapted pSemi Figure 21 (PDF p19, a ROUTED reference board) into this
  board's floorplan instead of copying it.
- result: **the EVK's OCTAGONAL outline is a consequence of EDGE-LAUNCH
  connectors** — an edge launch must sit on an edge, so nine of them force a
  nine-sided board. `KH-SMA-KE-Z` is a VERTICAL THT FLANGE jack that mounts on
  the board FACE. Dropping the polygon keeps the RADIAL STAR (the part that is
  the AoA requirement) and keeps the board inside the SHARED generic backend,
  which supports a rectangle + corner radius + notches and **has no polygon
  outline at all** — an octagon would have forced a bespoke
  `03_src/generate_board.py` and an ADR against the tscircuit-native pipeline.
  Geometry derived: ten slots at 30 deg over 270 deg on **R = 20.0 mm**, board
  **50 x 68 mm**, arms **17.85 mm** each (0.64 dB / 108.7 ps at 6 GHz),
  90 deg escape sector centred straight down off pins 7..12, **20.3 mm** of
  clear corridor width. R = 20 rather than 18 because the flange-to-flange gap
  is **2.39 mm vs 1.36 mm** (and 0.09 mm — touching — with axis-aligned
  flanges), and THAT GAP IS THE GROUND-VIA FENCE, i.e. the port-to-port
  isolation budget.
  **The angular assignment falls out of the pin-out with ZERO arm crossings**:
  rotate U_SW so its only RF-free side (pins 7..12) faces the corridor and every
  port exits toward its own slot.
- next: rules files, then the gates.

## 2026-07-28 13:30 — finish (stage-3 gate)

- did: replaced all three `03_src/rules/*.yaml` (they were still VERBATIM skill
  templates describing `cook_loadcell` and a 3S-LiPo board) and `floorplan.yaml`
  (same), wrote ARCHITECTURE / DETAIL_DESIGN / CHECKLIST, updated the BRIEF, and
  re-measured every gate.
- result, MEASURED:
  - `contracts_audit.py` **243 files, 0 violations**; `--projects` **0
    violations for this board** — after seeding `03_src/rules/contracts.md`,
    which the COMMISSION SCAFFOLD HAD MISSED. Every other board in the fleet has
    it and the skill template set ships it; this board's three `rules/*.yaml`
    had been C-ALLOW-failing since commission, invisible to the plain
    `contracts_audit` run because that mode does not grade `projects/`.
  - `policy_audit.py` **FAIL=1, HUMAN=6, N-A=26, PASS=7** (was FAIL=3 / PASS=6).
    **P-TIER PASS** — `all parts escape at declared fab_tier
    'jlc_4layer_advanced'`. P-ESC **4/4**, S-VER **4/4**, P-LAYOUT 2/2.
  - `electrical_invariants.py --adr-coverage` **E-ADR OK 4/4** protection/
    topology ADRs cited (0002, 0004, 0005, 0006) by 19 invariants.
  - `power_topology.py` **E-TOPO N-A, EARNED** — checked against `02_parts`,
    which declares no converter, not against the power tree's own say-so; it
    turns RED the moment the LDO dossier lands. `--off-control` **E-OFF N-A**
    on a declared `source_type: usb_bus_powered_5v`.
  - `status_beacon_check.py` **M-BEACON PASS 1/1**.
  - **`E-INV` FAIL is structural and expected**: `no exported netlist found`.
    It is a stage-4 artifact; the 19 assertions are written and unreachable
    until a schematic exists.
  - BRIEF prompt bytes byte-identical to `4caf0d6`; the recorded sha256
    reproduces with the trailing newline STRIPPED (the 01_docs contract's
    runnable line keeps it and yields `21708345f8ae...` — same bytes, different
    terminator, now documented in the BRIEF).
- next: stage 2 continuation — nine part dossiers, `U_LDO` first because it
  carries three DERIVED hard constraints (dropout <= 1.35 V at 0.15 A, V_IN abs
  max >= 10 V to sit above the TVS clamp, theta_JA <= 195 C/W which disqualifies
  a bare SOT-23-5 at the envelope). Then the two OWED footprints, then
  `03_tscircuit/` authoring.
