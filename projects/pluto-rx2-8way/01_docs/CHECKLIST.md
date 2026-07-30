# CHECKLIST — pluto-rx2-8way

The gate a revision must pass before release. **Every line names a command to
run or a file to inspect and the expected result** — "review the layout" is not
a checklist line. Run from the project root unless stated.

`$K` = `skills/kicad-pcb/scripts`, `$J` = `skills/jlcpcb-fab/scripts`
(repo-relative).

**Cutting a `07_releases/` directory while any BRIEF acceptance criterion is
`unmet` is a contract violation.**

---

## A. Source and structure

- [ ] `/usr/bin/python3 scripts/contracts_audit.py` → `0 violations`
- [ ] `/usr/bin/python3 $K/status_beacon_check.py projects/pluto-rx2-8way` →
      exit 0 (canon M-BEACON: seven fields, none twice, naming the LIVE release)
- [ ] BRIEF prompt hash: the bytes strictly between the two verbatim markers,
      final newline stripped, hash to the `prompt_sha256` in the header block
- [ ] `01_docs/journal/` carries a start / iterate / finish entry for every
      stage that ran; `01_docs/learnings/` written at stage completion (M-JRNL,
      M-LEARN)

## B. Design decisions still owed at stage 3 (must all be closed before order)

- [x] `02_parts/<MPN>/part.yaml` exists for **`U_LDO`, `U_MCU`, `U_FLASH`,
      `Y_XTAL`, `J_USB`, `D_TVS`, `F_IN`, `U_ESD`, `FB_IN`**
      (`02_parts/README.md` deviation 5) — **DONE 2026-07-28**
- [x] **`U_LDO` satisfies all three derived constraints** (`DETAIL_DESIGN.md`
      §5) — **DONE 2026-07-28, and TWO of the three MOVED during the stage-2
      merge**: dropout **≤ 1.23 V** at 0.15 A (not 1.35 — `F_IN` R_1max 0.75 Ω
      + `FB_IN` DCR 0.06 Ω drop 121.5 mV ahead of the pass element, which
      DISQUALIFIES AMS1117-3.3 at 1.3 V max); **`V_IN` abs max ≥ 10.3 V** (not
      ≥ 10 — the 5.0 V-standoff TVS the ADR derived 9.2 V from was rejected at
      selection; `SMBJ6.0A` clamps at 10.3 V, so a part rated exactly 10 V is
      now OUT of spec); **θ_JA ≤ 195 °C/W**. `MCP1755S-3302E/DB` clears all
      three at 500 mV / +17.6 V / 62 °C/W
- [x] `03_src/rules/power_tree.yaml` `rails:` is NO LONGER empty, and
      `$K/power_topology.py projects/pluto-rx2-8way` → **PASS 2026-07-28**
      (headroom 1230 mV vs dropout 500 mV; PD 307 mW vs a 968 mW derived
      package rating, 32 %)
- [x] **Stage-4 back-fill: the two parts the stage-2 sweep missed.** `02_parts`
      carries `KT-0603R` (C2286, the RED indicator — `LED_PWR`/`LED_ST`) and
      `TS-1187A-B-A-B` (C318884, the pushbutton — `SW_BOOT`/`SW_RUN`), both with
      the manufacturer document committed. **DONE 2026-07-28.** They were missed
      because the sweep's denominator was `DETAIL_DESIGN.md` §8's value index —
      which lists the BALLASTS `R_LED1`/`R_LED2` and never the indicators — and
      not the union of `floorplan.yaml` refdes with `nets.yaml` nets
- [ ] **Three LCSC codes need a row in the VETTED PASSIVES LEDGER**
      (`skills/jlcpcb-fab/references/lcsc_passives_ledger.yaml`), which is where
      commodity-passive identity lives fleet-wide — NOT a `02_parts` dossier,
      which would be a second home for the same fact. All three were read from
      the JLC catalog on 2026-07-28 (stock + library tier + describe string):
      **C137864** `RC0402JR-0747RL` 47 Ω ±5 % 0402, stock 86,783;
      **C274349** `RC0402FR-0727R4L` 27.4 Ω ±1 % 0402, stock 5,133;
      **C1548** `0402CG150J500NT` 15 pF 50 V **C0G** ±5 % 0402, **base**, stock
      2,388,330. Until they land, `bom_source_check --circuit-only` exits 1 with
      8 `UNVERIFIABLE-VALUE` findings and the board must not export a fab BOM
- [x] Footprints `QFN-24_4x4_P0.5_EP2.7_PE42482` and
      `SMA_Vertical_5.08sq_D1.4` authored in this project. **Neither may be
      copied from a sibling board** — **DONE 2026-07-28**, both in
      `03_src/lib/pluto_rx2_8way.pretty/`, drawn from pSemi Figure 23's
      RECOMMENDED LAND PATTERN inset (DOC-75785-4 p21) and the Kinghelm
      sheet-2/2 PCB inset (2021.08.10). Verified 48 geometry properties +
      6 silk/courtyard clearances by an independent re-derivation from the
      emitted file text, plus a `pcbnew.FootprintLoad` of each
- [ ] `03_src/floorplan.yaml` `libraries:` lists `03_src/lib` **FIRST**. KiCad
      ships `Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.65x2.65mm` for the same
      package outline with 0.85 mm pads at r = 1.95 and a 2.65 mm EP against the
      vendor's 0.60 mm at r = 1.90 and 2.75 mm. Library ORDER decides which land
      is fabricated and no DRC, parity or netlist check can see the difference
- [ ] Every `03_src/lib/*.pretty` footprint's **F.SilkS stroke ≥ 0.15 mm** and
      text height ≥ 0.45 mm — the `jlc_4layer_advanced` floors in
      `references/fab_tiers.yaml`. Both footprints were first emitted at KiCad's
      0.12 mm default and corrected; **no pipeline gate grades this**, so it is
      a checklist line rather than a command
- [ ] **Re-confirm `RF50` = 0.36 mm against JLCPCB's own impedance calculator
      for the exact ordered stackup** (`JLC04161H-7628`). The width here is a
      closed-form Hammerstad-Jensen result, not a field solve, and Dk is quoted
      at 1 GHz for a band that runs to 6 GHz (canon M6 — ADR-0003)

## C. Schematic gate

- [x] `$K/tsx_preflight.py projects/pluto-rx2-8way` → PASS before the first
      `tsci build` (S-COUNT: tscircuit drops parts SILENTLY) — **13/13 part.yaml
      tsx-safe or mapped, 8 multi-pin, 2026-07-28**
- [x] `kicad-cli sch erc --severity-all` → **0 errors** (430 warnings, all three
      in the documented parametric classes: `endpoint_off_grid` 207 from the
      converter's 0.635 mm fidelity grid, `lib_symbol_issues` 163 from the
      embedded `elt` lib not being in the running kicad-cli config,
      `footprint_link_issues` 60). **The gate is 0 ERRORS; `--exit-code-violations`
      returns non-zero on warnings too, so read the classification, not the exit
      code**
- [x] `$K/count_parity.py projects/pluto-rx2-8way` → refdes sets agree with
      `03_tscircuit/manifest.yaml` — **3/3 source pairs over 64 refdes**
- [x] `$K/net_label_survival.py projects/pluto-rx2-8way` → PASS (S-NETMERGE) —
      **44/44 labels survive to the netlist, 74 nets. READ THE COUNT, not just
      the verdict**: a sibling board's rebuild silently merged `3V3_ANALOG` into
      `3V3` and was caught only because the count came back 161/162
- [x] `$K/electrical_invariants.py projects/pluto-rx2-8way` → **PASS, all
      assertions reached — 24/24, 2026-07-28.** (19 at stage 3 → 20 → 21 with
      the `FB_IN` series chain from the stage-2 merge → **24** with ADR-0008's
      three.) **This gate could not run at all before a netlist existed, and it
      was the project's ONLY `policy_audit` FAIL for two stages**
- [x] `$K/electrical_invariants.py projects/pluto-rx2-8way --adr-coverage` →
      **5/5** protection/topology ADRs cited (ADR-0008 added at stage 4)
- [ ] `$J/bom_source_check.py --circuit-only …` → PASS at the FIRST BOM export,
      not first at seal. **Currently 8 findings, all one class and all named**:
      `UNVERIFIABLE-VALUE` on C137864 (47 Ω ×4), C1548 (15 pF ×2), C274349
      (27.4 Ω ×2) — three LCSC codes the vetted passives ledger does not carry.
      Closes with the section-B back-fill above (a `02_parts` dossier resolves
      the code) or by appending the three catalog-verified rows to
      `skills/jlcpcb-fab/references/lcsc_passives_ledger.yaml`
- [ ] **Every commodity passive's LCSC code is PINNED in the TSX.** tscircuit's
      parts engine assigns one to any un-coded passive, and `tsci build` is
      non-deterministic — so an unpinned BOM line is a build-time choice, not a
      design decision (canon M3). Its unprompted 47 Ω pick was **C25118 at stock
      10, extended**, for a part used four times whose value ADR-0005
      machine-asserts. Grep: every `<resistor>`/`<capacitor>` in the TSX carries
      `supplierPartNumbers`

## D. Placement gate

- [ ] `$K/placement_gates.py 04_kicad/pluto_rx2_8way.kicad_pcb --config
      03_src/placement_gates.json` → **P-OUT and P-CAP PASS** before any
      routing attempt
- [ ] **The eight congruent radials hold a REALIZED COPPER spread ≤ 1.0 mm**,
      graded by `$K/copper_length_audit.py .` against
      `length_match: RF_RADIAL_STAR` in `03_src/rules/nets.yaml`, and the
      measured spread is PINNED there (`pin.spread_mm`, tol 0.05 mm) so a
      re-route cannot silently invalidate the published picoseconds.
      **THE ±0.10 mm VERSION OF THIS LINE IS WITHDRAWN, 2026-07-29**, with the
      reason rather than quietly: 0.10 mm is **1.3° at 6 GHz** on this stackup
      (13.19 °/mm, ε_eff 3.350, t_pd 6.105 ps/mm), i.e. inside PE42482A-X's own
      published **13.2° = 1.00 mm** part-to-part relative-insertion-phase window
      (Table 3, PDF p8) and below the ~2°/fillet mounting-inductance asymmetry
      of ADR-0006(d) — and KRT has no inter-net skew machinery to deliver it
      (its length matching is diff-pair shaped). 1.0 mm is a DRIFT ceiling
      derived from `Δτ = TC·ΔT·ΔL·t_pd`: 1 mm is **0.05°** over 40 °C, 20 mm
      (the rejected rectangular fan-out) is **1.05°**, comparable to the whole
      AoA budget. ADR-0006 rejected "match all eight to within X mm" from the
      start — what the board owes is CONSTANCY, not equality
- [ ] **The ninth radial (RF8 → `J_ANT8`) is REPORTED, not matched**, and its
      copper is stated beside the group's: it is three nets through the pickoff,
      `RX1_MAIN` is a T (it also carries `J_RX1.1`), and its phase is set by a
      LUMPED 2 × 220 Ω cell, not by length (ADR-0002; ADR-0006 "unequal by
      construction")
- [ ] **`RX1_TAP_MID` pad-to-pad span ≤ 1.37 mm** (λg/20 at 6 GHz — the arm
      must stay a LUMPED element)
- [ ] **`R_T1` and `R_T2` at IDENTICAL rotation, not mirrored** — measured on
      the CPL, not asserted. It is invisible at export time
- [ ] **`U_SW` pin 1 (LS): ground via centre within 0.5 mm of the pad centre.**
      NOW GRADED, by `03_src/audit_board.py` **I8** (added 2026-07-29) — and it
      grades the same way for `Y_XTAL` pads 2 and 4, which must each take their
      OWN distinct via (≤ 1.0 mm), the part of ABM8's sentence no pad span can
      see. The `SW_LS ≤ 2 mm` keep_short was **DELETED** rather than re-pointed
      at `GND`: the anchor metric would have read U_SW.1 → C_SW1.2 = **6.956 mm**
      and failed a budget about a barrel on a number about a pad (ADR-0005)
- [ ] `SW_V4` span ≤ 4 mm (P-ADJ, from the part.yaml). **`SW_VDD` IS NO LONGER
      A GHOST**: re-pointed 2026-07-29 to `{net: 3V3, anchor_pins: ["8"]}`, the
      node pin 8 actually sits on, which is gradeable because P-ADJ measures the
      ANCHOR PIN against its nearest partner rather than the whole rail. MEASURED
      **U_SW.8 → C_SW1.1 = 2.873 mm of 3.0** — the same number stage 5 moved
      C_SW1 to x 44.7 to get, now read by a gate instead of by hand
- [ ] `XOUT_XTAL` span ≤ 6 mm on **ABM8's** own budget, re-pointed 2026-07-29
      from the ghost `XOUT` (Y_XTAL carries no pad on the MCU side of R_XTAL).
      Split at the part boundary: the MCU leg stays on RP2040's `XOUT` at
      3.062 mm, the crystal leg is `{net: XOUT_XTAL, anchor_pins: ["3"]}` at
      **3.618 mm of 6.0**
- [ ] **`U_ESD` centre within 2.0 mm of `J_USB`'s D+/D− pad row** (ADR-0008,
      ST DocID11265 §2.2). **NOTHING GRADES THIS**: P-ADJ grades `keep_short`
      net SPANS only and ignores `adjacency:` refdes pairs, and the netlist is
      identical at 2 mm and at 8 mm. The arithmetic is 6 nH per 10 mm × 0.5 mm
      at dI/dt = 24 A/ns ⇒ **+144 V per leg**, turning a 17 V clamp into 305 V.
      The stage-3 floorplan had it at ~8 mm; measure the built board
- [ ] **`C_ESD` within 2.0 mm of `U_ESD` pin 5**, and **`U_ESD` pin 2 has its
      OWN via to the L2 plane AT the pad** — not a shared neck, not a trace to
      the nearest stitch. Pin 2 is the single ground pin and carries the entire
      surge return; 10 mm of ground trace alone costs 144 V of clamp
- [ ] **`U_ESD` dressed IN-LINE**: the connector-side track lands on pin 1
      (D+) / pin 3 (D−) and the MCU-side track leaves on pin 6 / pin 4. Pins
      1+6 and 3+4 are internally the same node, so **no ERC, DRC, netlist or
      parity check can tell this dress from a stub** (ST Figure 7)
- [ ] **`SH` bonded to GND on all four legs, each with its own via**, and
      **`SBU1`/`SBU2` carry no trace, no via and no test point** — grounding SBU
      misdeclares the port to an accessory AND gives an ESD strike a path into
      the board
- [ ] **Bottom-plane antipad ≥ Ø3.5 mm under every SMA centre barrel.** Carried
      by the FOOTPRINT as a 0.80 mm local clearance on pad 1 (1.9 + 2 × 0.8 =
      3.5), so it opens in every ground plane by construction — MEASURE it on
      the filled board anyway, because a zone-fill setting can override a pad
      clearance and the failure is silent. Recomputed cost of getting it wrong:
      RL **14.5 dB (Ø3.5) vs 8.9 dB (Ø2.6)** at 6 GHz, i.e. **5.6 dB**
- [ ] **Each SMA ground post connects SOLID to plane copper, not through a
      thermal spoke** (`zone_connect 2` in the footprint) — and the 40 THT
      joints that creates are hand-soldered WITH PREHEAT. A cold post joint is
      worse for the launch than the spoke would have been
- [ ] Ground-via fence between every pair of adjacent SMA barrels, pitch
      ≤ 1.37 mm
- [x] **Every one of the ten SMA ports carries its own silk label, and each
      label is NEARER ITS OWN JACK than any other jack.** Ten near-identical
      barrels is a mis-mate risk by construction, so ownership is measured, not
      eyeballed. **MEASURED 2026-07-29**, own-jack vs nearest-other-jack:
      diagonals r = 10.85 (9.15 / 11.91), axis-adjacent r = 12.95 (7.05 /
      10.91), `RX2` r = 12.25 (7.75 / 11.21), `ANT8` r = 9.60 (10.40 / 12.63) —
      2.2–3.9 mm of discrimination on every port. The predecessor legend
      "RX2 → PLUTO RX2" measured **7.29 mm from `J_ANT1` against 7.85 mm from
      `J_RX2`**, i.e. it named the wrong connector, and nothing graded it
- [x] **The ten port labels are 0.95 mm text / 0.152 mm stroke, not 0.60/0.13.**
      The "≥ 0.60 mm text reaches a 0.15 stroke" corollary this board was handed
      is WRONG and the canon now says so: `fab_tiers.yaml` carries
      `published_stroke_min_height: 0.9375` as DATA, with G-SELFCON grading it
      against the generator in both directions. Board-silk stroke is
      `max(min_silk_stroke, 0.13, 0.16 × size)` clamped to ≤ 0.25 × size, so
      0.60 / 0.70 / 0.80 mm text all emit **0.130** and **0.9375 mm is the first
      height that reaches 0.15**. These ten are the only text on the board read
      under stress with a cable in one hand, and the only text that clears JLC's
      published 0.15
- [ ] **ORDER-DAY DFM, and it is a SECOND formula that the 0.9375 figure does not
      cover: refdes de-collision uses `max(min_silk_stroke, 0.09, 0.20 × size)`,
      not the board-silk pair.** MEASURED off the generated board, every silk
      text classified: 10 captions at 0.95 / **0.152**, 7 prose captions at
      0.60 / **0.130**, 44 refdes at 0.60 / **0.120**, 17 refdes at 0.45 /
      **0.1125**. So under the refdes formula 0.60 mm emits 0.12 (not 0.13) and
      the first height reaching 0.15 is **0.75 mm** — 61 of this board's refdes
      are therefore BELOW JLC's published 0.15 stroke, at the 0.1125 floor the
      tier declares it will emit. Raising refdes text to 0.75 mm was NOT done at
      stage 5: the ownership-first search already fails to seat two refdes at
      0.60/0.45, so a taller glyph would strand more. Carried as a fab-review
      item with its numbers rather than silently accepted
- [ ] **`Y_XTAL` pads 2 and 4 each take their OWN via to the L2 plane AT the
      pad.** REWRITTEN 2026-07-29: the crystal's `GND ≤ 3 mm` budget is NO LONGER
      waived and never was unsatisfiable — the 67.24 mm "span" was the board
      diagonal, an artifact of P-ADJ measuring whole nets. Graded against the
      anchor pin it read 3.233 mm (`Y_XTAL.4 → C_XTAL1.2`), a real 0.233 mm miss,
      and rotating both load capacitors so their GND pad faces the can made it
      **2.457 / 2.291 mm — PASS**. This per-pad via is still owed, because it is
      the part of the sentence ("each GND pad takes its own via to L2 at the
      pad") that no pad-span metric can see
- [ ] **`XOUT_XTAL` gets its own 6 mm `keep_short` declaration in
      `03_src/rules/nets.yaml`.** `R_XTAL` splits the XOUT node in two and the
      ABM8 part.yaml predicted in writing that the crystal-side half would
      "inherit this same 6 mm budget and currently has nowhere to be declared".
      It is now P-ADJ-UNREACHED and waived with both legs hand-measured
      (`U_MCU.21 → R_XTAL.1` 3.062 mm, `Y_XTAL.3 → R_XTAL.2` 3.618 mm). The fix
      is a SOURCE declaration, not a rename of the existing budget
- [ ] **`DVDD_1V1` from `U_MCU` pin 45 to `C_VREG_OUT` is a direct wide trace,
      not a daisy chain through the decoupling row.** The mandatory 1 µF
      (RP2040 §2.10.1) sits **8.65 mm** from `VREG_VOUT` because the sub-MCU row
      is eight parts at 2.2 mm pitch in a 1.92 mm band and cannot host a 0603
      (measured: best legal alternative 6.22 mm, which does not clear the budget
      either). The 100 nF are at 1.11 and 3.90 mm, so the HF return is short and
      this is the reservoir path only — route it as such
- [ ] **Re-check the four deliberately-starved thermals after the stage-6
      refill**: `C_MCU7.2`, `C_MCU8.2`, `C_MCU9.2`, `C_ESD.2`, all GND on F.Cu,
      all blocked by their neighbours in the 2.2 mm row rather than by anything
      about the parts. They were NOT converted to solid because a two-pad
      passive with one solid plane pad and one unpoured pad is thermally
      asymmetric at reflow (the tombstoning class). Tracks and stitch vias will
      change the local copper, so the set is re-measured, not assumed

## E. Routing gate

- [ ] `$K/tier_preflight.py projects/pluto-rx2-8way` → **0 FAIL** before any
      KRT cycle (R-PREFLIGHT)
- [ ] **No via, and no layer change, anywhere on an `RF50` arm.** Grep the
      board, do not eyeball it
- [ ] **`SW_BOOT` and `SW_RUN` each need TWO short traces the router will not
      ask for.** `Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A` gives ONE pad
      NUMBER to TWO physical feet — pad `1` at (±3, −1.875) and pad `2` at
      (±3, +1.875) — and KiCad's `duplicate_pad_numbers_are_jumpers` is **no**
      on this footprint (MEASURED 2026-07-28 on a scratch board: nets attached,
      no copper between the feet ⇒ `kicad-cli pcb drc --severity-all` = 0
      violations but **2 unconnected items** per switch). So the left and right
      foot of each node must be joined in copper, ~6 mm each, **four traces
      total across the two buttons**. The netlist cannot express this and the
      schematic gate cannot see it
- [ ] **L2 solid and unbroken under every RF arm and under the USB pair** —
      no split, no slot (R-PLANE)
- [ ] `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity` →
      **0 violations / 0 unconnected / 0 parity**

## F. Fab and assembly gate

- [ ] `$J/export_jlc_package.py …` → exit 0 (A-ROT is BLOCKING and cannot be
      skipped; F-LEGIBLE is blocking at exit 3)
- [ ] `$J/jlc_stock_check.py fab/bom.csv --json …` → the VERDICT line says
      PASS. **A missing or unparseable verdict is a FAIL, not a skip**
- [ ] `$J/jlc_twin.py …` → exit 0, zero unadjudicated MIRRORED / PAD-MISMATCH
      / PAD-GEOM; `A-BODY bodies mounted: N/M` read, not skimmed
- [ ] `$K/twin_overlay.py …` on both populated sides — read the COVERAGE line
- [ ] `$K/part_facts_check.py …` → every declared `asserts:` REACHED
- [ ] **ORDER_README.md carries this line VERBATIM** (D-TIER, ADR-0003; the
      `order_readme` string from `fab_tiers.yaml` with its reason filled):

      ADVANCED option REQUIRED: min via 0.25/0.15 mm (PE42482A-X QFN-24 at
      0.50 mm pitch — at the standard-tier 0.30 mm drill the adjacent-pin
      hole-to-hole gap is 0.50 − 0.30 = 0.20 mm against a 0.50 mm floor, so no
      escape via fits). 4-layer JLC04161H-7628, IMPEDANCE CONTROL REQUESTED.

- [ ] **ORDER_README.md carries the RF PORT CONTRACT**, and the silkscreen
      does too: `RX ONLY · PASSIVE ANTENNAS · 0 VDC · NO BIAS TEE · NO
      TRANSMIT`. There is **no ESD device and no DC block on any of the ten RF
      ports** (ADR-0004), `V_RFDC(max)` is 0 V and hot-switching is bounded at
      20 dBm — the contract is the protection
- [ ] ORDER_README states **MSL 1** for `U_SW` (unlimited floor life; no bake
      obligation) and the THT surcharge expectation for 10 SMA jacks

## G. The release artifact P8 depends on (ADR-0006)

- [ ] Per-path **routed electrical length (mm)** and **delay (ps at
      6.09 ps/mm, with `JLC04161H-7628` named in the artifact)**, per path and
      as a delta vs RF1
- [ ] Per-path **|S21| and ∠S21, 70 MHz – 6 GHz**, per path and as a delta —
      or the artifact states plainly that they are **UNMEASURED** (no VNA). A
      partial result honestly reported beats a passing claim
- [ ] The measured phase deltas fall inside the vendor windows
      (Table 3, PDF p8) after the routed-length term is removed. Outside them
      is a FINDING
- [ ] **The 8 × 8 leakage matrix** at the six datasheet band rows, and the
      **dark-state floor** (`V4 = 1, V1..V3 = 0`) — the T3 subtraction and the
      OWED ten-barrel SMA isolation both depend on it
- [ ] The artifact **names the unit measured**. Amplitude and phase deltas are
      unit-to-unit, so a design-level figure is a lie for every other board

## H. Review gate

- [ ] Both red-team lenses (topology/protection, layout/thermal) return
      **ORDER** with zero unresolved P0, archived verbatim in `08_reviews/`
- [ ] Fresh-context pin review: zero FAILs
- [ ] Fresh-context render review: every finding fixed or ADR-dispositioned
- [ ] `/usr/bin/python3 $K/policy_audit.py projects/pluto-rx2-8way` →
      **zero FAIL**, every WAIVED entry evidence-backed
