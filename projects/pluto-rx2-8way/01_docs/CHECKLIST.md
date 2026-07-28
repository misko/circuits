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

- [ ] `02_parts/<MPN>/part.yaml` exists for **`U_LDO`, `U_MCU`, `U_FLASH`,
      `Y_XTAL`, `J_USB`, `D_TVS`, `F_IN`, `U_ESD`, `FB_IN`**
      (`02_parts/README.md` deviation 5)
- [ ] **`U_LDO` satisfies all three derived constraints** (`DETAIL_DESIGN.md`
      §5): dropout ≤ 1.35 V at 0.15 A; **`V_IN` abs max ≥ 10 V** so the TVS
      clamp (~9.2 V) is inside its rating; **θ_JA ≤ 195 °C/W** — a bare
      SOT-23-5 is DISQUALIFIED at the 0.15 A envelope
- [ ] `03_src/rules/power_tree.yaml` `rails:` is NO LONGER empty once that
      dossier lands, and `$K/power_topology.py projects/pluto-rx2-8way` → PASS
      (it currently reports an EARNED N-A; the moment a converter appears in
      `02_parts` the gate turns red until the rail is declared)
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

- [ ] `$K/tsx_preflight.py projects/pluto-rx2-8way` → PASS before the first
      `tsci build` (S-COUNT: tscircuit drops parts SILENTLY)
- [ ] `kicad-cli sch erc --severity-all` → **0 errors**
- [ ] `$K/count_parity.py projects/pluto-rx2-8way` → refdes sets agree with
      `03_tscircuit/manifest.yaml`
- [ ] `$K/net_label_survival.py projects/pluto-rx2-8way` → PASS (S-NETMERGE)
- [ ] `$K/electrical_invariants.py projects/pluto-rx2-8way` → **PASS, all
      assertions reached.** 19 invariants across ADRs 0002/0004/0005/0006
- [ ] `$K/electrical_invariants.py projects/pluto-rx2-8way --adr-coverage` →
      **4/4** protection/topology ADRs cited
- [ ] `$J/bom_source_check.py --circuit-only …` → PASS at the FIRST BOM export,
      not first at seal

## D. Placement gate

- [ ] `$K/placement_gates.py 04_kicad/pluto_rx2_8way.kicad_pcb --config
      03_src/placement_gates.json` → **P-OUT and P-CAP PASS** before any
      routing attempt
- [ ] **All nine radial arms measure within ±0.10 mm of each other.** Equal
      length is the AoA requirement (ADR-0006); a spread of 20 mm would cost
      ~1° of thermal phase drift at 6 GHz over 40 °C
- [ ] **`RX1_TAP_MID` pad-to-pad span ≤ 1.37 mm** (λg/20 at 6 GHz — the arm
      must stay a LUMPED element)
- [ ] **`R_T1` and `R_T2` at IDENTICAL rotation, not mirrored** — measured on
      the CPL, not asserted. It is invisible at export time
- [ ] **`U_SW` pin 1 (LS): ground via centre within 0.5 mm of the pad centre.**
      MEASURE IT — LS is on the GND net, so P-ADJ has no net to grade and
      SKIPS this budget silently (ADR-0005)
- [ ] `SW_VDD` span ≤ 3 mm, `SW_V4` span ≤ 4 mm (P-ADJ, from the part.yaml)
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

## E. Routing gate

- [ ] `$K/tier_preflight.py projects/pluto-rx2-8way` → **0 FAIL** before any
      KRT cycle (R-PREFLIGHT)
- [ ] **No via, and no layer change, anywhere on an `RF50` arm.** Grep the
      board, do not eyeball it
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
