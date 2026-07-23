# Journal — 03 schematic v1.2 (usb-hub-3s-v3)

Revises the sealed **v1.1** SOURCE. `07_releases/v1.1-2026-07-23/` + the sealed
`04_kicad/` are IMMUTABLE — untouched (a `SUPERSEDED.md` is added later). Board
internal name stays `usb_hub_3s_v2`. The working `04_kicad/` regenerates from
source. Edited this revision:
`03_tscircuit/src/usb_hub_3s_v2.tsx`, `03_tscircuit/manifest.yaml`,
`03_src/rules/{electrical_invariants,power_tree,policy_waivers}.yaml`,
`02_parts/{RT0603BRD074K12L,BZT52C3V9,BZT52C6V2}/part.yaml` (new).

## 2026-07-23 — v1.2 fix set (DO-NOT-ORDER red-team of v1.1: 2 order-blockers)

A fresh red-team of the sealed v1.1 returned **DO-NOT-ORDER** on two ELECTRICAL
blockers (plus assembly items). This revision fixes them at the SCHEMATIC level.
Architecture decided by the user: **LOCAL SENSE + FLT→EN**.

### GATE — GREEN (measured)
- **tsci build: 118 components** (was 115), 382 pins; 0 silently dropped.
- **GRID converter** (mandatory; layout mode net-merges BOOT_A/VCC_A): 118
  components (116 with FPID), 382 pins, 0 segs dropped cross-net.
- **ERC: 0 errors** (`kicad-cli sch erc --severity-error`), warnings baselined
  (lib_symbol env note + named-NC isolated labels).
- **count_parity (S-COUNT): circuit.json == kicad_sch == netlist == manifest == 118.**
  The 5th source `board` (sealed 04_kicad) is missing D5/D6/D7 — the EXPECTED
  schematic-ahead-of-sealed-board state (board is immutable; its regen is the
  downstream stage). The four schematic representations agree = the schematic-gate
  contract.
- **E-INV: 29/29 invariants hold** (was 16; added the v1.2 fixes as positive
  assertions). **E-TOPO / E-MARGIN / E-OFF all PASS.**

### Blocker 1 — POST-eFuse FB RUNAWAY  → FIX A: LOCAL-SENSE FB
- **Mechanism (v1.1):** buck-C FB-top (R12) sensed **VBUSC** (post-eFuse
  connector). If the eFuse current-limited or opened, VBUSC collapsed, the LM5116
  FB integrator wound UP driving **5VC toward VIN (12.6 V)** — a runaway that
  over-volts the 10 V output caps and (via the old SHDN divider) the eFuse SHDN
  pin, and pulses the Pi on eFuse auto-retry.
- **Fix:** buck-C FB now senses the **LOCAL 5VC** node (`fbsense` removed;
  R12 3.92k→**4.12k**). 5VC is unconditionally regulated — the loop's feedback IS
  5VC, so an eFuse limit/open can no longer starve it. R12.1-on-5VC asserted
  (E-INV #6). Two more layers back this: FLT→EN (Fix B) and the D7 5VC clamp.

**Setpoint math (LM5116 Vref 1.215 V, FB-bot R13 = 1.21k, Vout = 1.215·(1+Rtop/1.21)):**
- R12 **4.12k** → 5VC = 1.215·(1+4.12/1.21) = 1.215·4.405 = **5.352 V** (regulated).
- eFuse+FET series IR = RON (31 mΩ typ / 45 mΩ max@85 °C, SLVSE94G) + Q6 AON6354
  3.3 mΩ = 34.3 mΩ typ / 48.3 mΩ hot. Drop @5 A = 172 mV typ / 242 mV hot.
- **Connector @5 A** = 5.352 − 0.172 = **5.18 V typ** / 5.352 − 0.242 = **5.11 V hot**.
- Vref ±1.5%: 5VC worst-low 5.272 V, worst-high 5.432 V.
  - **Connector quadruple-worst @5 A (Vref-low + hot) = 5.272 − 0.242 = 5.03 V ≥ 5.0 V ✓.**
  - **No-load 5VC worst-high = 5.432 V < eFuse OVP 5.91 V (margin 0.478 V) ✓; < 10 V caps ✓.**
- WHY 4.12k not the ~4.06k nominal: 4.06k is not an E96 0.1% value; 4.02k→5.252 V
  (below the 5.30–5.35 V target), **4.12k→5.352 V (in target)**. Chosen.
- **buck-A R3 STAYS 3.92k (C728591) → 5VA 5.151 V** (USB-A ≈5.07 V @2 A). buck-A
  always sensed its LOCAL 5VA output (no eFuse), so the FB→local change is a no-op
  for it. Raising R3 "proportionally" to 4.12k would push 5VA no-load to 5.35 V,
  breaking the USB-A **+5% ceiling (5.25 V)** — so buck-A keeps 3.92k. The
  local-sense PRINCIPLE applies to both; the VALUE is set by each rail's window.
- **Margin trade-off (documented):** v1.1 connector-sense regulated the eFuse+FET
  IR OUT of the loop (only the cable was downstream → 104 mΩ budget). Local-sense
  leaves that ~34–48 mΩ in the un-regulated path; the +201 mV setpoint bump covers
  it. E-MARGIN (vout_min = 5.18 V delivered @5 A) = **110 mΩ cable budget > 100 mΩ
  floor, PASS** (better than v1.1). BUT the quadruple-worst connector is ~5.03 V →
  only ~80 mΩ cable budget: **FLAGGED for the red-team + bench (measure real cable
  IR).** Lever if marginal: R12 4.12k→4.22k (5VC 5.453 V) at the cost of a tighter
  eFuse-OVP no-load margin (5.535 V vs 5.91 V).

### Blocker 1 (cont.) — FIX B: eFuse FLT → buck-C EN fault shutdown
- **U13 FLT** (pin15, open-drain **active-low**, abs-max **67 V**, sink ≤10 mA —
  SLVSE94G Abs-Max table) → buck-C **EN_C**. FLT asserts on UV / OV / overload /
  power-limit / **reverse-current** / ILIM-short / thermal (DS 8.3.10, internal
  de-glitch) → pulls EN_C low → buck-C shuts down, so the buck can't keep sourcing
  5VC into a faulted/limited eFuse.
- **buck-C EN UN-MERGED** from ENKILL onto its own **EN_C** net (the `en` prop
  dropped; Buck defaults to `n("EN")`=EN_C) so a C-port fault shuts **only** buck-C
  — buck-A charging and the SHDN bias are undisturbed. The master switch still
  reaches buck-C via **D6** (1N4148WS, on-BOM): anode EN_C, cathode ENKILL. On
  master-off (ENKILL=0) D6 forward-pulls EN_C low; on an FLT fault (EN_C low,
  ENKILL high) D6 is reverse → fault isolated. E-INV: U13.15/U11.4 on EN_C,
  D6.1/ENKILL + D6.2/EN_C, U2.4/ENKILL.
- **FLT not PGOOD:** PGOOD de-asserts during every normal dVdT soft-start and would
  stall/oscillate startup; FLT only asserts on true faults.

### Blocker 2 — SHDN 7.56 V > 5.5 V ABS-MAX  → FIX C: divider + Zener CLAMP
- **Mechanism (v1.1):** SHDN was a bare 0.6-ratio divider from 5VC (R33 100k / R36
  150k). On a 12.6 V buck-HS-short, SHDN = 0.6·12.6 = **7.56 V > the 5.5 V SHDN
  abs-max** (SLVSE94G Abs-Max: OVP/dVdT/IMON/MODE/**SHDN**/ILIM/PLIM = −0.3…5.5 V)
  → destroys the pin.
- **Fix:** re-valued divider **R33 40.2k / R36 49.9k** (ratio 0.554) for the enable
  level + a HARD Zener **CLAMP D5 (BZT52C3V9)**, cathode on SHDN, anode on GND.
- **SHDN fault-voltage check (the required number):**
  - **Normal:** 5VC = 5.352 V → SHDN = 5.352·49.9/90.1 = **2.96 V** (> 2 V SHUTR
    rising-enable threshold, margin 0.96 V; below the ~3.7 V D5 knee → D5 OFF,
    stiff/low-Z divider so the ±10 µA SHDN leakage is negligible). Enables the eFuse.
  - **12.6 V 5VC fault:** bare divider would reach 12.6·0.554 = 6.98 V. D5 breaks
    down; node balance (I_R33 = (12.6−V)/40.2k, I_R36 = V/49.9k, I_D5 = diff) with
    BZT52C3V9 Vz≈3.7 V @~0.15 mA converges to **SHDN ≈ 3.7 V**. With the D7 5VC
    clamp also holding 5VC ≤ ~6.8 V, SHDN ≈ 6.8·0.554 = **3.8 V**. Either way
    **SHDN ≈ 3.7–3.8 V < 5.5 V abs-max (margin ≥ 1.7 V). BLOCKER FIXED.**
  - Master-off: 5VC collapses → SHDN → 0 (eFuse off), as before.
- **WHY no discrete NFET (deviation from the task's suggested "NFET pulldown driven
  by ENKILL"):** ENKILL is **active-HIGH-when-on** (grounded only to shut off), so
  an NFET pulldown gated by ENKILL would be ON in normal operation and DISABLE the
  eFuse — wrong polarity. A correct ENKILL-inverting stage needs two transistors,
  which buys nothing over the clamp (5VC-collapse already gives master-off). The
  task offered "**clamp SHDN**, or bias from a safe node" as the alternatives; the
  clamp is implemented and is the robust choice (biasing from ENKILL would need a
  low-Z divider that sags the 100k EN bus and drops SHDN below the 2 V enable at
  min-VIN). **FLAGGED for the red-team as a conscious deviation.**

### FIX D — LOCAL 5VC CEILING CLAMP (D7)
- **D7 BZT52C6V2** Zener, cathode on 5VC, anode on GND. Belt-and-suspenders: caps
  5VC ≤ ~6.8 V if the loop ever loses regulation (e.g. an FB resistor opens),
  protecting the 100 µF/10 V output caps (C29–C32) + the eFuse IN_SYS/OVP divider.
  WHY 6V2 not 5V6: 5VC no-load worst-high 5.432 V; BZT52C6V2 Vz(min) 5.8 V > 5.432
  V (no nuisance conduction) — a 5V6 (Vz-min 5.2 V) would conduct at 5.432 V.

### FIX E — OUTPUT CAP MPN DECISION: **KEEP 10 V (C84455)**
- 5VC rose 5.151→5.352 V. Output caps stay **C84455** (GRM32ER61A107ME20L,
  100 µF **10 V** X5R 1210). Rationale: 5.352 V on 10 V = **1.87× voltage margin**
  on a REGULATED rail (the eFuse isolates connector transients from the buck
  output — no reflected load dump), ≥ the 1.5× practice floor. The DC-bias delta
  vs v1.1 is only +0.2 V (+2–3% extra derating → negligible output-pole shift); the
  v1-proven Type-II comp was validated with these caps. **Bumping to 16 V** would
  raise effective-C at 5.35 V but needs a new part/sourcing and is unnecessary —
  it is the LEVER if the flagged bench Bode wants more output C. Input caps stay
  **C77102 (50 V)**; C49/C50 VBUSC bulk stay C77100 (10 µF/25 V, ~5.1 V rail).

### FIX F — STALE R-THERM WAIVER (03_src/rules/policy_waivers.yaml)
- Prose updated to the v1.2 FET set: ADDED **Q6** (AON6354 eFuse reverse-blocking
  FET — drain on EFINC, source on 5VC, NEITHER an internal-plane net, so the same
  "no plane to via into" false-positive as the buck-FET drains; Rds diss 3.3 mΩ·5² =
  0.083 W). Noted Q7 (BSS138 SOT-23 signal FET) is not R-THERM-relevant. Exact v1.2
  flagged-pad list is re-derived at the board regen (R-THERM is a board-stage check).

### New parts (part.yaml written; pin map / polarity / escape per schema)
- **RT0603BRD074K12L** — 4.12k 0.1% 0603, buck-C FB-top (R12).
- **BZT52C3V9** — SOD-123 Zener, SHDN clamp (D5), pad1=cathode.
- **BZT52C6V2** — SOD-123 Zener, 5VC clamp (D7), pad1=cathode.
- D6 reuses on-BOM **1N4148WS** (C2128). Net new refdes: **D5, D6, D7** (115→118).

### Refdes / net deltas
- Added: D5 (SHDN clamp), D6 (EN_C↔ENKILL coupling), D7 (5VC clamp).
- New net **EN_C** = {U11.4, R17.2, U13.15(FLT), D6.2}. ENKILL now = {U2.4, R8.2,
  SW1.2, D6.1}. R12.1 moved VBUSC→5VC. R33/R36 re-valued (100k/150k → 40.2k/49.9k).

### OPEN / FLAGGED for the verify stage (pre-order + red-team)
1. **v1.2 REQUIRES a fresh INDEPENDENT zero-context RED-TEAM** (not a
   fix-confirmation) covering the fault modes: eFuse limit/open, buck-HS-short,
   reverse-current, master-off ordering, FLT→EN hiccup, SHDN clamp, 5VC clamp,
   startup race (buck-C makes 5VC before SHDN enables the eFuse).
2. **SHDN "clamp not NFET" deviation** — see Fix C; assess the polarity argument.
3. **Connector quadruple-worst margin ~5.03 V / ~80 mΩ cable budget** — bench-verify
   real cable IR; lever = R12→4.22k.
4. **Unverified LCSC (sealed-env fetch unavailable) — CONFIRM AT ORDER:** R12
   (4.12k 0.1% RT0603BRD074K12L), D5 (BZT52C3V9), D7 (BZT52C6V2). Authoritative
   MPNs in 02_parts; codes intentionally NOT baked into the schematic (a wrong FB
   value/Zener voltage would defeat the fix). R33/R36/R30-R32 remain generic 0603.
5. **Loop stability** (Type-II comp with local sense) + **OVP no-false-trip @5 A**
   + **output-cap 10 V-vs-16 V** — bench Bode (carried from v1.1, re-confirm on the
   5.352 V setpoint).
6. **Board-stage:** new-part placement (D5/D6/D7 near U13/buck-C), silk, and the
   R-THERM flagged-pad re-derivation.
