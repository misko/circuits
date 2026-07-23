# Journal — 03 schematic v1.1 (usb-hub-3s-v3)

Revises the sealed v1.0 SOURCE (07_releases/ + 04_kicad/ IMMUTABLE — untouched).
Board internal name stays `usb_hub_3s_v2`. Edited: `03_tscircuit/src/usb_hub_3s_v2.tsx`,
`03_tscircuit/manifest.yaml`, `03_src/rules/{electrical_invariants,nets,power_tree}.yaml`,
`03_src/floorplan.yaml` (silk), `01_docs/ARCHITECTURE.md`, `02_parts/BSS138/part.yaml` (new).

## 2026-07-23 — v1.1 fix set (eFuse + FB-at-connector + master-off + caps + snubbers + relabel)

### GATE — GREEN (measured)
- tsci build: **115 components** (was 100), 376 pins; **0 silently dropped**
  (manifest 115 == circuit.json 115, symmetric diff empty).
- Converter (**--mode grid**, mandatory — layout mode net-merges BOOT_A/VCC_A):
  115 components (115 with FPID), 0 segs dropped as cross-net.
- **ERC: 0 errors** / 332 warnings (baselined: lib_symbol env note + named-NC
  isolated labels). `verification/erc_converter.rpt`.
- **count_parity (S-COUNT): manifest == circuit.json == kicad_sch == netlist == 115.**
  The 5th source `board` (04_kicad, sealed v1.0, 100 parts) shows missing the +15
  new parts — this is the EXPECTED schematic-ahead-of-board state (the board is
  immutable and its revision is the downstream stage); the four schematic
  representations agree, which is the schematic-gate contract (same shape the v1.0
  schematic gate reported before its board existed).
- **E-INV: 16/16 invariants hold** against the exported netlist (rewrote the
  ADR-0001 invariants for the protected-VBUS topology; added a `series_chain`
  proving 5VC -> Q6 -> EFINC -> U13 -> VBUSC).
- tsx_preflight: PASS. Topology re-derived from the netlist: 21/21 substantive
  net-membership assertions PASS (eFuse path, FB sense, master-off merge, OVP/SHDN/
  ILIM/dVdT dividers, snubbers, all NC pins isolated in `unconnected-*` nets).

### Fix 1 — PROTECTED VBUS (TPS26631 eFuse + reverse-current-block FET pair)
- Inserted between the 5VC buck output and J5 VBUS. New net **VBUSC** = eFuse OUT
  = the protected connector rail; J5 A4/A9/B4/B9, U12.VBUS, C49/C50, R28/R29 (CC Rp)
  and the buck-C FB sense all move from 5VC -> VBUSC. New net **EFINC** = eFuse IN
  (Q6 drain -> U13 IN).
- **TOPOLOGY (datasheet SLVSE94G §8.3.5/8.3.6, fetched + text-verified this session):**
  reverse-current blocking needs **TWO** external FETs, not one —
  - **Q6 = AON6354** power blocking FET: SOURCE=IN_SYS(5VC), DRAIN=IN(EFINC),
    GATE=B_GATE(U13.4). Body diode blocks IN->IN_SYS reverse flow when off.
  - **Q7 = BSS138** fast gate-PULLDOWN (the datasheet's "Q2"): GATE=DRV(U13.5),
    DRAIN=B_GATE, SOURCE=IN_SYS. Yanks Q6's gate to its source in ~0.17µs on
    reverse detection. **The eFuse part.yaml note budgeted only Q6** ("DRIVES a
    blocking FET via B_GATE/DRV") — it under-specified. Without Q7 there is no
    sanctioned fast turn-off (DS Fig 8-7 is the only reverse-block config and shows
    both). Added Q7 = on-BOM **BSS138** (folder was an empty stub; wrote its
    part.yaml). BSS138 meets every TI Q2 requirement: VDS 50V≥15, VGS±20, Ciss
    ~24pF≤50, VGTH(min) 0.8V≤3.  ** flagged as the one deviation from the given
    part set — see OPEN QUESTIONS.**
- Set pins: R_ILIM **3.09k** -> I_OL = 18000/3090 = **5.83A** (min 5.42A > 5A load);
  C_dVdT **10nF** -> t ≈ 20.8e3·5.15·10n ≈ 1.1ms soft-start (inrush ≈ 0.1A);
  **MODE->GND** (auto-retry); **UVLO->GND**, PGTH->GND, EP/GND->GND; IMON/FLT/PGOOD NC.
- **OVP** = adjustable INPUT-OV cutoff, divider from IN_SYS(5VC): R31 47.5k / R32
  12.1k -> trip 1.2·(47.5+12.1)/12.1 = **5.91V**. Nudged up from the spike's 5.8V
  because option-a lets 5VC (the unregulated input side) float to ~5.39V @5A hot,
  so 5.8V would leave only 0.41V; 5.91V restores ~0.52V margin and still hard-trips
  the 12.6V buck-HS-short that threatens the Pi.
- **SHDN** (active-low enable): **divider** R33 100k / R36 150k from 5VC -> ~3.09V
  (>2V enable thr, and ≤3.4V << the 5.5V SHDN abs-max even when 5VC peaks ~5.6V).
  It CANNOT tie straight to 5VC (abs-max 5.5V, and 5VC floats to ~5.4V @5A). Ties
  the eFuse-enable to buck-C presence: master-off drops 5VC -> SHDN low too.
- C52 0.1µF local bypass on IN (DS-recommended; IN sits behind Q6 from the 5VC bulk).

### Fix 2 — FB / SETPOINT: chose **option (a) — sense at the connector**
- **Decision: (a).** Buck-C FB top (R12) senses **VBUSC** (post-eFuse); the loop
  holds the CONNECTOR at 1.215·(1+3.92/1.21) = **5.151V**, load-independent.
- **Why (a) not (b):** the target ">=5.0V @5A AND <5.25V no-load" is *physically
  unreachable* by option (b) (sense-before-eFuse, open-loop). The no-load ceiling
  5.25V minus the max hot eFuse+FET drop (~0.24V: RON 45mΩ + Q6 3.3mΩ @5A) = a
  5.01V floor at 5A with ZERO room for the LM5116 Vref ±1.5% — option (b) with
  3.92k delivers only ~4.91–4.98V @5A (measured-estimate), missing 5.0V and risking
  Pi low-voltage warnings. Option (a) regulates the connector to 5.151V, which sits
  inside [5.0, 5.25] across Vref ±1.5% (worst-low 5.07V ≥5.0 ✓, worst-high 5.23V
  <5.25 ✓), reuses the already-bought 3.92k 0.1% part, and is the external review's
  stated "sense at the connector" preference.
- **Connector @5A = 5.151V nominal (5.07–5.23V over Vref tol).** 5VC (buck output /
  eFuse input) then floats to 5.151 + I·R = 5.32V (typ) / 5.39V (hot) @5A.
- **Loop stability (analysis; bench Bode flagged):** in normal operation the eFuse
  + Q6 present a FIXED ~34mΩ series R (RON 31mΩ + 3.3mΩ). Its pole with the
  post-eFuse cap (C49/C50 ≈ 14–20µF eff + Pi caps) is 1/(2π·0.034·20µF) ≈ **234kHz
  — far above the ~20kHz loop crossover**, so the pre/post caps stay effectively
  lumped (~188µF) at crossover and the v1-proven Type-II comp is undisturbed. The
  eFuse non-linearities (current-limit foldback, dVdT, OVP) engage only in
  fault/startup. Fault behavior is SAFE: on a buck HS-short 5VC->12.6V trips OVP
  (senses 5VC) and the buck wind-up (5VC stays high) keeps OVP latched -> eFuse
  stays off -> NO auto-retry pulsing onto the Pi.
- **Buck-A "corresponding change":** R3 3.74k->3.92k too, but buck-A keeps sensing
  its own 5VA output (3 separate USB-A connectors can't share one connector-sense).
  5VA setpoint 5.151V -> USB-A ≈ 5.07V @2A after the TPS2557 ~43mΩ drop.

### Fix 3 — MASTER OFF (SS12D07 slide switch)
- SW1 COM(2) -> new net **ENKILL**; T1(1) -> GND; T2(3) -> NC. Both bucks' EN pins
  (U2.4, U11.4) and both 100k EN pull-ups (R8, R17) are MERGED onto ENKILL (the two
  100k now parallel = 50k -> VIN). Slide to T1 grounds ENKILL -> both LM5116 to ~9µA
  shutdown (kills the mA operating Iq) AND collapses 5VC -> the eFuse SHDN divider
  drops -> eFuse off. Verified ENKILL == {U2.4, U11.4, R8.2, R17.2, SW1.2}.

### Fix 4 — CAPS
- Buck INPUT MLCC C9-C12 / C24-C27: 10µF **25V->50V** = GRM32ER71H106KA12L (**C77102**).
- Buck OUTPUT MLCC C14-C17 / C29-C32: 100µF **6.3V->10V** = GRM32ER61A107ME20L (**C84455**).
- Scope note: C49/C50 (the USB-C VBUS bulk, now the eFuse OUT cap) stay 10µF/25V
  (C77100) — already 5×-derated at 5V, not among the red-team-flagged parts.

### Fix 5 — SNUBBERS (optional-populate)
- Per LM5116 SW node: R(2.2Ω 1206, C137327) SW->SNUB + C(1nF C0G 0805, C62774)
  SNUB->GND. Buck-A: R34/C53 (SNUB_A); buck-C: R35/C54 (SNUB_C). Added via the
  Buck cell so both rails get one. **DNP by default** (fit only if bench shows SW
  ring; R≈sqrt(Lpar/Cpar) tune) — schematic carries them so the footprints exist.

### Fix 6 — DOCS RELABEL
- Silk (floorplan.yaml): "PROTECTED 3S + BAL-CHG ONLY", "USB-A 5V CHG no-data" (×3),
  "USB-C 5A Pi-ONLY  NOT USB-PD", + "POWER-DIST BOARD - NOT A USB HUB". (Realized at
  board-regen; final de-collision is a board-stage step.)
- ARCHITECTURE.md: intro + block diagram + USB-C section rewritten to the honest
  framing (proprietary Pi-dedicated 5A, NOT USB-PD/standards-compliant; power-
  distribution board = 3× USB-A charging + 1× Pi-USB-C power, NO data hub;
  protected 3S pack + balance charger ONLY; eFuse now POPULATED not "optional").

### Refdes added (15): U13, Q6, Q7, SW1, R30–R36, C51–C54. (Q6/Q7/C51 reuse
### numbers freed when the PD cell left; they are FETs/caps now, not PD parts.)

### OPEN QUESTIONS / bench-verify (reported to caller)
1. **BSS138 (Q7) added beyond the committed part set** — required by the datasheet
   for functional reverse blocking; the eFuse part.yaml under-specified it. On-BOM,
   meets spec, isolated (easy to remove if the caller prefers a different Q2 or
   accepts degraded blocking).
2. **Loop stability with the eFuse in-loop** (option a) — analysis says stable
   (34mΩ pole ≈234kHz >> ~20kHz crossover); confirm with a bench Bode (inject at
   FB, ≥45° PM) before volume.
3. **OVP no-false-trip at 5A load steps** — 5VC floats to ~5.4V @5A so the 5.91V
   trip has ~0.5V margin; confirm load-release overshoot stays clear on the bench
   (if marginal, raise the trip toward ~6.0–6.1V — still under the Pi tolerance).
4. **Silk final placement** deferred to the board revision (de-collision is a
   board-stage step); new-part PLACEMENT (eFuse cell near J5, SW1) is board-stage.
