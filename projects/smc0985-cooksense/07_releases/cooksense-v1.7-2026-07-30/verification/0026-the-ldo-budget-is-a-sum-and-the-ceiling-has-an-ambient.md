# ADR-0026 — the 3V3 budget is a SUM over five rails, and the SOT-223 ceiling is
# a JUNCTION TEMPERATURE at a DECLARED AMBIENT, not a 25 °C constant

status: **accepted**
date: 2026-07-30
tags: power, thermal, sourcing-of-numbers, gates
relates: ADR-0004 (sensor I2C on the Pi 5 + the switched-rail rule N1),
ADR-0021 (the supply is a specification), ADR-0014 (OPEN item 2 — the board's
own thermal zone is undeclared)
amends: `03_src/cooksense/rules/power_tree.yaml`,
`02_parts/AMS1117-3.3/part.yaml` (`layout.source`, `layout.notes`)

## Context

Two numbers on the one rail with a hard package ceiling were wrong, in opposite
directions, for seven revisions. Both survived DRC 0/0/0, `policy_audit`
FAIL=0, four graded review lenses and eight sealing passes. Neither is copper.

**(1) The graded load was 43 % of this file's own declared load.**
`power_tree.yaml` graded the AMS1117 at `iout_max_A: 0.3`, whose comment
enumerated only logic families. Seventy-three lines lower, under a
`linear_rails:` key the file itself labels *"Documentation-only (ignored by
power_topology.py)"*, it declared four 0.1 A switched sensor rails. Nothing
summed them, because `rails:` means *"a CONVERTER produces this rail"* and a
P-FET load switch converts nothing — a correct statement that was read as
*"nothing else needs counting."*

MEASURED with `pcbnew` on the release's own board
(md5 `9f4fd5fae810f40a52b1035df727243c`), 2026-07-30: `Q_SWA` / `Q_SWB` /
`Q_SWRHA` / `Q_SWRHE` all have pad 2 on net `3V3`, and their drains reach
`J_THERM_A.1` / `J_THERM_B.1` / `J_RH_AMBIENT.1` / `J_RH_EXHAUST.1`.

**(2) `pdiss_max_mw: 1200` was a 25 °C figure used as an ambient-independent
ceiling.** ds1117 Note 2's 1.2 W is a bound on where LINE AND LOAD REGULATION
are guaranteed, and its own sentence ends *"Guaranteed maximum power
dissipation will not be available over the full input/output range."* The
datasheet states the real ceiling as a formula, and `BRIEF.md` line 117 puts
this board's enclosure at `<=50 / 55 / 65 / 75`.

**(3) The θ_JA justification cited a mounting this board does not have.** The
file claimed *"the tab is VOUT and is flooded with 3V3 copper … which is the
mounting Table 1 (p.5) characterises at 55-65 C/W."* MEASURED, every filled
zone on the board enumerated: `GND` on F.Cu (2701.43 mm²), `GND` on B.Cu
(7385.83), `GND` on In1.Cu (8465.52), `3V3` on In2.Cu (8420.03). **There is no
F.Cu `3V3` zone at all.** `U_LDO` pad 4 is 2.000 × 3.800 = 7.60 mm² of copper
sitting as an island in the F.Cu GND pour. Table 1's TOP SIDE column is *"tab
of device attached to topside copper"* and its smallest row is 100 mm² → 80 °C/W.

## Options

**A. Leave the load at 0.3 A and treat the four rails as documentation.**
REJECTED — this is the defect, stated as a policy. A budget written in a
section the checker is told to ignore is a check that cannot fail.

**B. Move the four switched rails into `rails:` so E-TOPO grades them.**
REJECTED, and not for taste: `power_topology.py`'s `resolve_converter` raises a
`LoadError` on a converter whose `part.yaml` `type:` does not normalize to a
topology, and `AO3401A` is `pfet_30v_4a`. Declaring a switch as a converter
makes the gate refuse the file rather than grade it.

**C. Declare a `theta_ja:` / `ambient_c:` pair as new keys in `power_tree.yaml`.**
REJECTED as unavailable, not as wrong — it is the RIGHT shape and it is the
subject of the owed skill patch below. G-ORPHAN fails any key a source file
declares that no gate provably reads, and the contract template that would have
to carry the row lives under `skills/`, outside this board's partition.

**D. Sum every rail into `rails[].iout_max_A`, and derate
`rails[].pdiss_max_mw` at a declared ambient.** CHOSEN. Both are keys
`power_topology.py` reads, and the rail-level `pdiss_max_mw` override is the
one `power_topology.py` documents for exactly this purpose — *"a board-specific
derating (a hot ambient, no copper under the part)"*.

**E. On the ambient: 50 (preferred), 55 (warn), 65 (stop) or 75 (hard)?**
CHOSEN **75 °C**, the BRIEF's HARD limit. ADR-0014's OPEN item 2 records that
this board's own thermal zone has never been declared, so the enclosure's hard
limit is the only reading that invents no fact — and the rail passes there, so
no weaker ambient has to be argued for.

**F. On θ_JA: 46 (best mounting), 55–65 (Table 1), or 90 (package figure)?**
CHOSEN **90 °C/W**, ds1117 ABSOLUTE MAXIMUM RATINGS, *"SOT-223 package
ϕ JA = 90 °C/W"*. The datasheet DOES bless this board's real mechanism —
*"the heat spreading copper layer does not need to be electrically connected to
the tab … the PC material can be very effective at transmitting heat between
the pad area … and a ground plane layer either inside or on the opposite side
of the board"* — and MEASURED plane coverage under the LDO body is In1 GND
98.6 % / In2 3V3 98.9 % / B.Cu GND 98.6 % at 0.2 mm of prepreg, so the true
figure is plausibly better than 90. **It is not measured, so it is not
claimed.**

## Decision

1. **`rails[].iout_max_A` = 0.15 A**, an ITEMISED SUM at datasheet maxima:
   on-board logic 3.913 mA + `3V3_ANALOG` 3.949 mA + off-board 2.068 mA + the
   four switched sensor rails 85.116 mA = **95.046 mA**, × a declared 1.5
   design margin for the terms that are not individually citable (CMOS dynamic
   current, the LVC ΔICC adder, MLCC leakage, harness leakage).
2. **`rails[].pdiss_max_mw` = 497 mW**, derived:
   `(125 − 75)/90 × 1000 − 5.250 × 11 = 555.6 − 57.8 = 497.8`, rounded down.
   The subtracted term is the AMS1117's own **Quiescent Current, max 11 mA**
   (ds1117 ELECTRICAL CHARACTERISTICS) burning `Vin_max × Iq_max` inside the
   same package — E-TOPO's `PD = (Vin_max − Vout_min) × Iout` cannot see it,
   so it comes off the ceiling instead.
3. **The SHT4x heater is declared.** The SHT45 carries a 200/110/20 mW
   on-package heater drawing up to **100 mA** at its top level, and the brief
   commissions the exhaust pod into a condensing duct — the case Sensirion
   §4.9 lists the heater FOR. It is budgeted at the manufacturer's own
   **≤10 % maximum duty cycle** (§4.9 / Table 9; `tHeater` long pulse
   0.9/1/1.1 s with automatic shutoff), i.e. 10 mA average per RH rail, with
   the coincident dual-pulse PEAK (275 mA for ≤1.1 s) carried as a junction
   excursion of `θ_JC × ΔP = 15 × 0.256 = +3.8 °C`.
4. **The Table 1 55–65 °C/W quotation is deleted, not re-argued**, from both
   `power_tree.yaml` and `02_parts/AMS1117-3.3/part.yaml`, and that dossier's
   *"the tab … is the ONLY heat path"* is corrected against the datasheet
   sentence that contradicts it.
5. **`vin_min` is deliberately NOT re-derived.** It stays at 4.754 V, derived
   at a 0.50 A whole-board current the new budget shows to be ~1.7× the real
   worst case. A conservative `vin_min` is the conservative direction for the
   DROPOUT check; re-deriving it downward would only make a check easier.

## Consequences

**The rail passes, and here is the whole result.**
E-TOPO, `RAW_EXIT=0`: headroom 1355 mV (unchanged) vs a 1300 mV dropout;
**PD 307 mW vs 497 mW → 62 %**. The junction temperature that actually matters:
`Tj = 75 + (0.3074 + 0.0578) × 90 = 107.9 °C`, **17.1 °C of margin to 125 °C**,
or 13.3 °C carrying the dual-heater excursion.

**The declared current went DOWN, 0.30 → 0.15, in the same pass that ADDED
four missing rails, and that must not pass unremarked.** The old 0.30 was never
derived from anything; the itemised on-board logic at datasheet maxima is
**9.93 mA**, roughly 30× less than the number that claimed to cover it. The
sensor rails it omitted are 8.6× larger than the logic it counted. Both errors
are now closed against citations rather than against each other.

**Still OWED, and one bench session retires all three** (canon M-OWED): θ_JA on
this mounting, the AMS1117 dropout at this rail's real load (ds1117 publishes
dropout only at 0.8 A and has no dropout-vs-load curve), and the `V_IN − V_OUT`
the file already owed. At G4 bring-up: load `3V3` to its real total, measure the
`U_LDO` tab rise against a known ambient, and sweep `V_IN` down until `V_OUT`
leaves 3.201 V.

**Next revision, not this one.** `02_parts/AMS1117-3.3/part.yaml`'s `layout`
block asks for a 3V3 flood under and around the tab and the board does not have
one — 7.60 mm² of pad against a requirement with no number on it. Either give
the tab a real F.Cu 3V3 pour (it must not touch the GND pour — that shorts the
rail) and re-measure, or state the pad-to-plane path as the design and put a
number on it. Both are copper changes and neither is affordable inside a seal.

**What breaks if reversed.** Restoring `pdiss_max_mw: 1200` re-grades a 75 °C
board against a 25 °C ceiling. Restoring `iout_max_A: 0.3` un-counts the four
sensor rails. Raising the ambient above 75 °C, or discovering θ_JA worse than
90 °C/W at bring-up, both eat directly into the 17.1 °C of junction margin —
at θ_JA 120 °C/W the margin is 6 °C, and at 137 °C/W it is gone.

**Owed skill patch — the class, not this instance.** `power_topology.py` must
REFUSE to grade a `power_tree.yaml` that carries rail-like keys it does not
read. G-ORPHAN already knows: it grades
`power_tree.yaml linear_rails[].iout_max_A` as **OWED**, and its own text says
*"also absent from the trunk-current sum `rails[]` feeds"* — the exact defect,
in the contract, in words, exiting 0 because OWED does not fail. Written up in
`06_build/staging/cooksense-v1.7/verification/owed_skill_patches.md`.
