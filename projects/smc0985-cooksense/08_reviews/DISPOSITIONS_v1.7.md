# v1.7 candidate — review battery dispositions (2026-07-28)

FOUR independent zero-context lenses, launched concurrently, input CURATED
(journal/, learnings/, STATUS*.md and 08_reviews/ withheld from all four).

| lens | verdict |
|---|---|
| topology / protection / ratings | **DO-NOT-ORDER** (P0-1) |
| render | **DO-NOT-ORDER** (P0-A, P0-B) |
| layout / thermal / PI | **DO-NOT-ORDER** (P1-b; no P0) |
| pin review (FRESH LENS) | **FAIL** — 1 blocking pin-map FAIL x12 instances, 1 blocking electrical |

**SEAL BLOCKED. v1.7 is NOT sealed. cooksense-v1.6-2026-07-27 remains LIVE — BUT SEE PIN-P0, WHICH IMPLICATES v1.0-v1.6 TOO.**

**CORRECTION, recorded rather than quietly edited:** the first cut of this file
said "pin review PASS". That was the main loop misreading
`2026-07-28_v1.7_pin-review_changed-and-safety-chain.md` — a DIFFERENT review,
committed earlier in `9a02c52` against an earlier v1.7 state — as the output of
this session's fresh lens. The fresh lens returned **FAIL**. Both files are kept;
neither supersedes the other.

## Blocking

| id | finding | disposition |
|---|---|---|
| **TOPO P0-1** | v1.7 added `R_WDOKSER` to `U_EXP.8` only; GPB1-GPB5 sit directly on MODE_AUTO_HW / ESTOP_OK / DOOR_OK / TEMP_OK / FAULT. One I2C transaction defeats four safety terms. Contention 0.863 V weakest / 2.055 V realistic vs LVC1G11 V_IL 0.8 V — no datasheet corner gives a guaranteed LOW. TEMP_OK worst: 2.48 V, feeds coil rail + contactor + fault-SET, and is the only term with no independent physical backup. | **ACCEPTED — FIX REQUIRED.** 10k (C60490, existing line) in series into U_EXP.2/.3/.4/.5/.6, consumers on the raw nets; plus matching pin_on_net asserts, RED-verified. |
| **RENDER P0-A** | J_ESTOP / J_DOOR inter-mateable C189896, labels discriminate by **0.069 mm**; `D_DOOR` (h 0.60, 33% taller) sits 0.353 mm from the E-STOP connector and 6.411 mm from its own diode. | **ACCEPTED — FIX REQUIRED.** Silk-only, respin-only. Extend `fix_silk_placement.py` to enforce label OWNERSHIP, not just void avoidance. |
| **RENDER P0-B** | `P-SILK-FN` matched `^(J|F|TP)[0-9]` -> exactly ONE ref (`F1`) of 35 touchpoints. The only machine gate on connector silk could not fail. | **FIXED 2026-07-28** in `skills/kicad-pcb/scripts/policy_audit.py`, default now `^(J|F|TP)([0-9]\|_)`. Measured: cooksense 1->31, interposer 0->23, pluto-rx2-8way 0->12, pluto-cal-switch 1->8, crow-rc-v2 30->32. Now FAILS on unlabeled test points — a real finding it could never previously report. Known-bad fixture OWED. |
| **LAYOUT P1-b** | `J_ISOLOOP` (the NOT-SELV connector) silk label printed 0.353 mm OUTSIDE its own courtyard and fully inside `J_RH_EXHAUST`'s; 4.900 mm to own pads vs 1.412 mm to the neighbour's — a 3.5x inversion. | **ACCEPTED — FIX REQUIRED.** Same silk pass as P0-A. **INDEPENDENTLY FOUND BY TWO LENSES** with no shared method (render measured 0.314 vs 0.373 mm from the other direction). |

| **PIN P0 (VERIFIED BY THE MAIN LOOP)** | The 12 DIP05 reed relays' footprint has 4 pads on DIP 1/7/8/14, but datasheet p.3 sub-figure **12** shows **EIGHT** leads with **1<->14 one contact node** and **7<->8 the other**, coil on the INNER pins. Netlist confirms: pad1=`5V_KEY_RELAY` and pad4=`U_SEL_BUS` are the SAME internal node; pad2=`COIL_U1_N` and pad3=`KP_U1` likewise. So `5V_KEY_RELAY` is hard-shorted to the select bus, every ULN2803 output is shorted to its keypad line, **the coil has no holes at all**, and the array is non-functional. The 1.5 kVDC coil/contact isolation boundary cited to ADR-0002 does not exist in pinout 12 — the split runs along the long axis, not between rows. | **ACCEPTED — FIX REQUIRED, and it is NOT v1.7-scoped.** The footprint predates v1.7 and ships in **sealed v1.0-v1.6**. Re-author against sub-figure 12 (8 pads), re-derive the isolation geometry, re-run placement/route. `part.yaml`'s prose matches sub-figure **13**, the 4-lead variant — the wrong sub-figure was read. |
| **PIN P0-b** | `U_EXP` pin 1 (GPB0) idles at **5.0 V** into a 3.3 V part (abs-max 3.6 V): `EFUSE_FLT_N` is pulled up to `5V_PROTECTED` through `R_PG` 100k. ~14 uA of continuous injection into 3V3. | **ACCEPTED — FIX REQUIRED.** Divider, or move the pull-up to 3V3. |

## Recorded, not blocking

- **LAYOUT P1-a — the moat's tightest point is confirmed by nothing.** KiCad DRC does not test zone-fill-vs-pad clearance; PROVED by raising the rule to 8/12 mm and observing 514 violations with `(Zone,pad) = 0`. The moat measures exactly **2.0000 mm** on all four layers and passes, but that number rests on a hand-typed keepout. Gate gap -> v1.8.
- **LAYOUT P1-c — the LDO's 45 C/W is not supported by attached copper** (~6 mm2 spreading, 2 tab vias, ~104 K/W). Failure direction SAFE (thermal shutdown collapses 3V3, every pull-down asserts). -> v1.8.
- **TOPO P1-1 — the power tree does not balance**: 3V3 declares 0.3 A then declares children summing to 0.45 A. At the file's own numbers both E-TOPO criteria invert (PD 128%, headroom short 24.5 mV). The E-TOPO PASS this revision obtained is arithmetic that contradicts its own child table.
- **TOPO P1-2 — `vin_min` omits every ohm of PCB copper.** Measured 89.9 mOhm J_PWR->LDO; 45.0 mV at 0.50 A = **82% of the declared 55 mV margin**, 53.8 mV at 70 C. The margin ADR-0021 was made to obtain does not survive the board's own copper. Owed: the bench dropout measurement.
- **TOPO P1-3 — `TEMP_OK`'s default is PERMISSIVE and ADR-0019 does not name it.** All eleven ADR-0019 directions re-derived CORRECT, including the two counter-intuitive ones. But TEMP_OK is a twelfth permission input and an open-drain wired-AND structurally cannot carry a restrictive pull-down.
- **TOPO P1-4** — the opto's published 30 V/50 mA is ~18x the guaranteed LED drive (Ic >= 2.8 mA). Fail-safe direction; a false published rating.
- **PIN — 4 QUESTIONs** open for adjudication (J_MODE harness-end circuit 1, U_ONESHOT, U_LATCHG, U_EXP) plus 3 process findings. No FAIL.
- **P2s**: 11 from topology, 9 from layout, 4 from render. See the individual archives.

## Refutations recorded (canon: record, do not delete)
Topology self-refuted `D_ESD_IN` upstream of F1 (correct practice) and the 7 ms
FLC window (largely). Layout withdrew via-in-pad (SKILL.md records 0.25/0.15 as
proven orderable), withdrew "J_MODE 0.0000 mm pad gap" as **its own bug**
(`GetSize()` is unrotated; true gap 0.80 mm, and the GH->ZH change WIDENED it
from 0.55), and withdrew the D_KSTOP flyback loop. Render refuted BOTH its own
overlay exits with an independent classifier. **All three lenses confirmed the
v1.7 J_MODE GH->ZH change is correct** — it cannot mate with any GH harness.

---

# 2026-07-29 — the three blockers closed, and a fourth that blocks instead

No new lenses were run. This section records the DISPOSITION of the carried
findings, with the measurement that closed each one.

| id | disposition | evidence |
|---|---|---|
| **PIN-P0-1 / TOPO P1-1** — U_EXP.1 readback dead at 0.833 V | **CLOSED** | ADR-0022: `R_PG` pull-up 5V_PROTECTED → 3V3, `R_FLTDIVT`/`R_FLTDIVB`/`EFUSE_FLT_DIV` deleted. `node_level` reports **3.300 V at U_EXP.1** vs V_IH 2.640. E-INV 136/136, 5 new asserts RED-verified |
| **RENDER-P0-1** — J_ISOLOOP no artwork | **CLOSED for the caption, PARTIAL for the legend** | `ISO 30V` at **0.085 mm** from the block body, `NOT SELV` at 7.892 mm, both h0.600/0.150. Pole legend does NOT fit at the terminal and rides the north-stack caption |
| **RENDER P1-1 / P0-A** — six designators at 0.130 mm, label ownership | **CLOSED** | 250 texts re-measured: 0 below the 0.1125 mm tier floor, 0 storing an unachievable stroke, 11/11 safety texts at h0.600/0.150. Ownership leads J_DOOR +3.087, J_ESTOP +0.659, J_MODE +10.685 mm |
| **RENDER P0-B** — P-SILK-FN could not fail | **already FIXED upstream**; the project's own waiver text is now corrected too |
| **TOPO P1-2** — coil pull-in margin | **CLOSED 2026-07-29 (was ESCALATED TO P0)** | ADR-0023: `U_ULNA`/`U_ULNB` ULN2803ADWR (C9683) → **TBD62083AFWG (C165895)**, a pin-identical DMOS array — pin map from the p.2 pin TABLE, land from the p.9 drawing at 300 dpi (TI's DW 11.50×7.50 sits dead centre of Toshiba's 11.35–11.68 × 7.37–7.62 band), COM clamp diode confirmed from the p.2 equivalent-circuit FIGURE because the coils have no external flyback. R_ON is a GUARANTEED EC-table max, 3.25 Ω, identical at all three published current points, so 7 mA × 6.50 Ω (2×, hot bound) = **46 mV** against the Darlington's 670–880 mV. Margin **+0.774 V at +50 °C and +0.424 V at +75 °C**, positive at every corner; ampere-turn cross-check **7.815 mA vs 7.00 mA required at +70 °C, +11.6 %** (was 6.81 mA, −2.7 %). DRC 0/0/0, E-INV 140/140, zero geometric change. The `node_level` assert that pins it measures **0.056 V vs a 0.540 V budget = PASS with the DMOS, 0.895 V = FAIL with the Darlington** — PROVEN, but NOT LANDED: `node_level` joins dossiers by LCSC code and the self-supplied relays carry an MPN, so it needs a 4-line checker patch (verify journal) |
| **PIN Q-1** — pad 1 called GPA0 | **CLOSED** | It is GPB0; GPA0 is pad 21 (`RAIL_EN_A`, an output). Copper was always right |

## Findings this session made, that no lens reported

| # | finding |
|---|---|
| 1 | `electrical_invariants.yaml` declared `supplies: {… N3V3: 3.3}` — the tsx author-prefix form. **No net `N3V3` exists in the netlist**, so the 3V3 rail was invisible to every `node_level` grade. Found by reading the netlist, not by a gate |
| 2 | `node_level` grades a LOGIC LEVEL, not an ABS-MAX. Moving `R_PG` back to 5 V leaves it PASSING at 5.000 V; only the `pin_on_net R_PG.2` assert catches it. Two different claims, and the RED-verification is what exposed the difference |
| 3 | The **6.46 mm** "ISO 30V fits here" re-run that the fix list inherited **does not reproduce** either — that site is blocked by `U_OPTO`'s body and `J_RH_EXHAUST`'s body; the clear band is 0.87 mm and a 0.45 mm text needs 0.92 mm. Third unreproduced "nearest site" number on this corner in three sessions |
| 4 | The real obstruction at the block was never geometry: it was `C_LATCHB`'s and `U_OPTO`'s **designators**, parked first-come-first-served. A 0402's reference does not outrank the only NOT-SELV warning on a 30 V terminal |
| 5 | A per-pole legend at J_ISOLOOP is **geometrically impossible**, stated precisely: the pads sit at the CENTRE of the KF350 body in x, so every square millimetre either side of a pole is under the moulding once the block is fitted |
| 6 | The **1.5 mm ownership margin is not affordable at 0.60 mm text** — it was measured at 0.45 mm and a 0.60 mm box needs 78% more area. `J_ESTOP` has ZERO qualifying slots and landed at a degraded 0.5 mm demand, measured lead +0.659 mm |
| 7 | `route.yaml` had **predicted its own next failure** ("a site legal by 0.00 mm is a site the next reroute takes away") and not reserved against it. The `U_TC.8` stub refused on the first race after the netlist changed |
| 8 | Deterministic plane-bond sites were being chosen by **proximity**; the nearest legal site for `Q_SWDRVB.2` and `U_TC.5` both scored **growth 0.00** — legal by nothing. Sites are now chosen by **max growth**. Slack survives a re-route; distance to the pad centre does not |
| 9 | **`C506653` (MCP23017-E/SS, `U_EXP`) is at ZERO LCSC stock**, where the same gate read 56/56 PASS last session. **CLOSED 2026-07-29** → `C558584` MCP23017T-E/SS, stock 7490: not an alternate but the SAME device, DS20001952C's PRODUCT IDENTIFICATION SYSTEM listing (f) `-E/SS` and (g) `T-E/SS` with the `T` as the tape-and-reel identifier only. jlc_stock_check **PASS 56/56** |
| 10 | **`02_parts/` IS THE MPN AUTHORITY FOR EVERY RELEASE, THE ALREADY-SHIPPED ONES INCLUDED — and this session broke that and got caught by the test suite, not by a review.** Deleting the superseded `ULN2803ADWR` dossier and moving the MCP dossier's `sourcing.lcsc` off `C506653` made the **LIVE sealed release v1.6 ILLEGIBLE**: `t1_fleet_regrade.py` went RED with "LCSC C9683 resolves NO MPN from any authority". The contract's "rejected candidates never get a committed PDF" is about candidates that were NEVER USED; a part that SHIPPED is a different class. Both restored, both recorded in the dossiers |
| 11 | **One field, two incompatible readings.** `bom_legibility_check.py` reads `sourcing.alternates` as `{lcsc:, mpn:}` MAPPINGS and SILENTLY SKIPS bare code strings; `electrical_invariants.py::_load_part_electrical` reads the same field as BARE STRINGS. The 02_parts contract's own example shows the bare form — i.e. the contract documents the form F-LEGIBLE cannot read. `C47023` had been latently unresolvable here for the life of the file |
| 12 | `status_beacon_check.py`'s `_SEALED_RE = re.compile(r"sealed", re.I)` is a SUBSTRING match, so a beacon reading `stage: NOT-SEALED-REVIEW-OWED` / "IS NOT SEALED" was graded as CLAIMING a completed seal and FAILED M-BEACON-REL. A beacon that explicitly disclaims a seal must not be read as claiming one |

## Verdict

**SEAL STILL BLOCKED, BUT NO LONGER ON A DESIGN DEFECT. `07_releases/` is
untouched and v1.0–v1.6 remain DO-NOT-ORDER.** As of 2026-07-29 every carried
P0 is CLOSED: the coil pull-in margin by ADR-0023 (driver technology — option
(b) of the three, with (a) the coil rail refuted arithmetically and (c) a
narrower envelope refused because the 45.7 °C crossover is BELOW the brief's own
≤50 °C normal band), and the `C506653` stock-zero by `C558584`. What remains is
process, not engineering: the fresh four-lens battery, two measured rotation
ledger rows that live outside this project's pathspec, the 4-line `node_level`
join patch, one manifest `not_assembled:` line, and the seal.

**A fresh four-lens battery is OWED, not skipped.** It was not run because a
confirmed P0 already blocks and closing it will change the power tree or the
coil driver — a material change that needs its own battery. Running four lenses
against a board that must change again would spend it twice.

---

# 2026-07-29 (third) — THE FRESH FOUR-LENS BATTERY, RUN AT LAST, AND IT BLOCKS

The battery deferred twice — correctly, both times, because a confirmed P0 was
open and closing it changed the driver — was run here against the pre-seal
staging archive. Four zero-context lenses, launched concurrently, input CURATED
(`journal/`, `learnings/`, `STATUS*.md`, `CHANGELOG.md`, `08_reviews/` and
`07_releases/` withheld from all four; no `git log`).

| lens | verdict |
|---|---|
| render / silk (FRESH LENS) | **DO-NOT-ORDER** — 2 P0 |
| topology / protection / ratings | **DO-NOT-ORDER** — 0 P0, 7 P1, 13 P2 |
| layout / thermal / power integrity | **DO-NOT-ORDER** — 7 P1, one of them the order-blocker |
| pin review (FRESH LENS) | **FAIL** — 0 pin-map FAILs, 2 evidence-grade FAILs; connector group OWED and requested |

**v1.7 IS NOT SEALED. `07_releases/` IS UNTOUCHED. v1.0-v1.6 REMAIN
DO-NOT-ORDER.** Nothing was staged into `07_releases/`; the archive sat in
`06_build/staging/cooksense-v1.7/` throughout, where it could not make itself
the live release.

## The two order-blockers

| id | finding | disposition |
|---|---|---|
| **RENDER P0 — LABEL OWNERSHIP ON CROSS-MATEABLE SAFETY CONNECTORS. This is the SAME defect v1.7's battery raised as RENDER P0-A and marked FIX REQUIRED; the fix landed and DOES NOT REACH THESE REFS.** Measured by the main loop on the current board, box EDGE-to-EDGE, independently of the lens: the string **`J_ISOLOOP` is printed 0.161 mm from `J_RH_EXHAUST`** and 2.739 mm from J_ISOLOOP — the 30 V NOT-SELV terminal's own designator labels a humidity-sensor header. **`J_ESTOP`'s designator is 0.161 mm from BOTH `J_ESTOP` and `J_DOOR`**, an exact tie, and those two are the SAME part (`JST_GH_SM05B-GHS-TB_1x05`, C189896) — physically cross-mateable, two of the four such headers being safety inputs. `J_DOOR`'s own designator is 5.66 mm from J_DOOR and 4.23 mm from `D_DOOR`. The generator states it itself: the rebuild log prints `WARN silk ownership ... no owned slot in the 4x84 search` for J_DOOR, J_ESTOP, J_ISOLOOP, J_MODE and 52 others and then places them anyway — **179/241 owned, 56 degraded, 6 unplaced.** | **ACCEPTED — BLOCKS. NOT FIXED HERE, AND DELIBERATELY NOT ATTEMPTED.** The cause is PLACEMENT DENSITY: J_ISOLOOP + J_DOOR + J_RH_EXHAUST + U_OPTO + R_OPTOLED inside ~15 mm of the SE corner. No silk-only pass can create space that does not exist — this one already evicts three foreign labels to fit `ISO 30V` at 0.561 mm. A floorplan change re-races the router, which would spend this battery a third time, so it belongs to the next revision as one deliberate pass. **Consider that the honest fix is partly a PART change:** four identical 5-pin GH headers on one board, two of them safety inputs, is the defect underneath the silk. |
| **LAYOUT P1-PI-2 — NO CAPACITOR ANYWHERE ON THE eFUSE INPUT SIDE, and the layout rule written to protect it names a net that does not exist.** `5V_IN` / `5V_FUSED` / `5V_RPP` carry **zero** capacitors; `C_IN1`/`C_IN2` are on the eFuse OUTPUT. The `keep_short` budget meant to hold the input cap local is addressed to net **`5V_SELV`**, which is not a net on this board. | **ACCEPTED — BLOCKS.** The lens's own reasoning is adopted verbatim: a missing input capacitor on the protection stage of a mains-adjacent board cannot be added to a fabricated panel. Everything else it found is a document fix, a fabricator question, or characterisable at bring-up; this one is copper. |

## Confirmed by the main loop, generalising a lens finding

**TEN net names referenced by this board's rule files and part dossiers DO NOT
EXIST IN THE NETLIST** — measured by walking every `net:` / `nets:` /
`vdd_net:` key in `03_src/cooksense/rules/*.yaml` + `02_parts/*/part.yaml`
against the 412 nets in `06_build/netlists/cooksense.net`: 10 of 123 referenced
names (8%) are ghosts. `5V_SELV` (TPS259573DSGR) is the one that hid the missing
input capacitor; the others are `+5V`, `3V3_DIGITAL`, `HS_GATE`, `LED_DRIVE`,
`N3V3`, `OPTO_LED`, `RCEXT`, `T_MINUS`, `T_PLUS`. Some are generic
datasheet-side placeholder names rather than board claims — **and that is the
point: nothing distinguishes a placeholder from a ghost, so a dead budget is
indistinguishable from a satisfied one.** Third instance of this class in two
sessions (`supplies: {N3V3: 3.3}`, `GND_ISO` on the silk and in the padmap, now
these ten). Proposed as a gate upstream.

## Closed by this pass — do not re-open

| id | disposition | evidence |
|---|---|---|
| **The 0.600 mm comb slots — FOURTH sighting, and it was a real P0** | **CLOSED, FIXED** | JLCPCB's own capability page: **"Min. Non-Plated Slots: 1.0mm"**, read twice and corroborated independently. Twelve unplated internal slots were 40% under it. Widened to **1.000 mm** (y25.8-26.8 / y49.1-50.1) after measuring it free: nearest copper on any of four layers with pours filled **2.8500 mm** north (2.5500 at r11r12), **2.7300 mm** south, against the 0.200 mm JLC asks. Verified in the board's Edge_Cuts horizontals. DRC 0/0/0. Cost stated: refdes-on-silk 235/241 with 6 waived to F.Fab (was 5) |
| **The ADR-0023 coil-margin assert — proven but ungated** | **CLOSED, LANDED** | Eleven `node_level` asserts, one per DMOS-driven reed. **E-INV 140/140 -> 151/151.** RED-verified in place at BOTH Darlington corners (95.7 ohm -> 0.714 V, 125.7 ohm -> 0.895 V, 11 FAILs each against the 0.540 V pull-in budget, exit 1), restored byte-identical. Landing it found that only pad "18" carried the hot-corner 6.50 ohm, so ten of eleven asserts would have graded at the 25 C 3.25 ohm default — all eleven driven channels now declare it (M-WIDTH). **The relay count is TWELVE, not the thirteen three files say**; eleven on the arrays, K_STOP excluded BY NAME |
| **`J_PI` (C35165) / `J_LOADCELL` (C157991) — coded but on no CPL row** | **CLOSED — the first branch, with evidence already in place** | `assembly.yaml` declares both `process_incompatible` with a MEASURED justification (5 and 40 plated DRILLED pads, F.Paste on none, against a `service=standard sides=[top]` reflow-only order). They are correctly OFF the CPL (0 rows) and stay in the BOM as self-supplied lines so the order sheet still says what to buy. The MANIFEST `not_assembled:` line is computed — 16 refs — and closes A-POP's one FAIL |
| **`GND_ISO`, in two places** | **CLOSED, both corrected** | The SILK printed "GND_ISO ONLY" and `parity_padmap.txt` claimed J_KEY_MATRIX's MP tabs are "reflowed to GND_ISO". `grep -c GND_ISO` = **0**. The board was right and both documents were wrong: those tabs are netless BY DESIGN because J_KEY_MATRIX is the only connector on the isolated side of the reed barrier. Measured: **19.407 mm** to the nearest SELV copper against >= 6.000 mm. Caption now reads NO GND BOND |
| **The `1C2L3L4E` pole legend** | **CLOSED, FIXED AT THE ROOT** | It sat **0.161 mm from J_RH_EXHAUST** against 5.512 mm from its attributed owner, because `fix_silk_placement.py` bounded a caption's distance to its OWN part and tested nothing about the others. It now refuses an unowned site and reports DOES NOT FIT (no owned site exists at that corner). Found by the new P-SILK-OWN row and by the render lens, two methods, no shared code |
| **A-RENDER, never run on this board before** | **CLOSED — PASS, and its two FAILs were its input's resolution** | At jlc_twin's hard-coded 1600x1000 (**8.34 px/mm** on a 188 mm board) it FAILED on `U_LDO` (centre delta 1.248 mm) and `Q_SWDRVRHA` (13 body px). Re-rendered at **15.3961 px/mm**: exit 0, 53 measured / 210, **zero** resolvable-but-unmeasured, U_LDO **0.111 mm**, Q_SWDRVRHA **0.086 mm** (872 px). A gate whose verdict flips with the resolution of its input must say so — reported upstream |
| **`kicad_sch_parity` FAIL 1/169** | **DISPOSITIONED, not waived** | The single `('J_KEY_MATRIX','MP')` no-connect, and the IDENTICAL finding appears against **sealed v1.6** (1/161) — inherited, not new. It is a checker gap: a mechanical pad unbonded BY DESIGN has no way to say so |
| **`W-FOREIGN` on this board's own S-OCCL waiver** | **CLOSED** | `derived_from: [crow-recorder-central-v2, crow-mic-pod-v2]` DECLARED, with the note that only the waiver CLASS is inherited and the 77-site measurement is native. Scoped verdict **PASS, 12/12 independently reasoned** |
| **The 2N7002 datasheet** | **DEVIATION DECLARED, not closed** | LCSC serves HTML, not the PDF (two URL forms tried, both 200-with-HTML). K_STOP's margin re-derived from the rail rather than inherited: 5V_STOP `vout_min` **4.754 V**, so +70 C margin is **+0.454 V** at the estimated 0.10 V V_DS and still **+0.054 V** at 0.50 V. Not load-bearing; K_STOP is excluded BY NAME from the coil-assert family |
| **The west comb slot's web** | **CARRIED as a DFM query, with the reason it is not a respin** | 1.000 mm web to the board edge while the same file skips the east pocket for "<3mm ... too fragile" — a self-contradiction, INDEPENDENTLY found by the layout lens (P1-MECH-2). JLC publishes no remaining-wall minimum; their own Q&A asking it is UNANSWERED. Extending the slot through the edge would change the mechanical outline of a board whose enclosure interface is specified |

## Carried to the next revision, each with its number

- **The LDO thermal story, now measured twice and worse than carried.** Carried
  as "13.96 mm2 against ~645 mm2"; the layout lens measures **~3.1 mm2** of
  top-layer 3V3 at the tab, 2x0.15 mm vias, 44.8 K/W tab-to-plane, theta_JA ~75
  against the cited 55-65, **Tj 110-122 C at Ta 70 C** — and **no operating
  ambient is declared anywhere on this board**, so no junction temperature can
  be closed at all. That last item is owed regardless of everything else.
- **The 3V3 rail's own arithmetic, re-derived by the main loop from the file.**
  `3V3` declares `iout_max_A: 0.3` and annotates it "logic:
  595/238/HC14/1G-family/MCP23017/watchdog/one-shot" — its DECLARED CHILDREN
  (`3V3_ANALOG` 0.05 + four `3V3_SW_*` at 0.10) draw a further **0.45 A from
  it**. At the true 0.75 A: **PD = (5.250-3.201) x 0.75 = 1.537 W against a
  1.200 W budget = 128%**, and dropout headroom **fails by 24 mV**. E-TOPO
  reports PASS on the understated denominator, so this is a GATE defect as well
  as a rail defect. Third battery in a row to report it.
- `D_ESD_IN` (PESD5V0S1BA, V_BR 5.5 V min) is upstream of F1 and becomes the
  ONLY clamp in circuit once the eFuse opens: 630 mW at 9 V, 1.56 W at 12 V.
- The contactor opto delivers **~2.4 mA** against a declared "<=30 V / 50 mA",
  and the 30 V inductive loop has no snubber against V_CEO 35 V.
- The brief's **Ioff buffers and 22-100 ohm series resistors DO NOT EXIST** on
  the BOM, while `ARCHITECTURE.md` states they do.
- The TPS3823 watchdog is **0.9 / 1.6 / 2.5 s fixed** against a commissioned
  300-500 ms, with no ADR waiving it.
- **Door EOL supervision is unimplementable as built**: `J_DOOR` pins 2 and 4
  are ONE net and the receiver is a single HC14 threshold, not a window.
- External I2C runs carry no ESD and no series damping; pull-ups are fixed 2.2 k.
- **P1-MECH-1**: the declared max conductive fastener OD (6.000 mm) lands on
  keypad copper at H1/H2 — copper at 2.950 mm radius, overlap 0.050 mm, max safe
  OD **5.900 mm**; it would bridge `KP_U2` to `KP_U6`, two matrix rows.
- `power_tree.yaml`'s series budget contains **no PCB copper at all**: 96.939
  mOhm measured against a 190.5 mOhm device-only budget, headroom **+18.7 mV not
  the declared +55 mV**, and the file's own 0.60 A stress case inverts to
  **-4.3 mV FAIL**.
- The LDO compensation cap is **9.200 mm** away against a 5.0 mm budget, reached
  through three 0.15 mm vias and the plane; `EF_OVLO` is **8.473 mm** against
  5.0 mm; and **no gate measures `keep_short` at all** — 7 of 11 budgets
  violated.
- All 1052 vias are 0.25/0.15 with a 0.050 mm ring while the netclasses declare
  0.60/0.30 — and the DRC floors were set to the values used.
- **Two evidence-grade FAILs from the pin lens.** 26 of 54 dossiers point at NO
  committed datasheet PDF, and `SN74LVC1G00DCKR`'s `doc_id` (SCES214)
  contradicts the real document (SCES212AB) which the same file's
  `layout.source` names correctly. And **`pin_audit.py` silently emits
  content-free dossiers for 16 of 54 parts, including ALL TWELVE RELAYS** — the
  one land pattern whose predecessor was drawn against the wrong datasheet
  sub-figure is exactly the one the dossier generator blanks, so a reviewer
  working only from the dossiers, as the protocol instructs, could not have
  performed the check at all. A CHECKER defect; reported upstream.
- **Silk legibility, with the emitter named.** 249 texts: 173 at h 0.600 /
  stroke 0.150 (all 11 safety texts among them) and 71 at h 0.450 / stroke
  0.1125 — the REFDES de-collision emitter's floor at that height. Against
  JLC's published `Minimum Line Width >=0.15mm` and `Minimum text height 40 mil
  (1.0mm)` this is the order-day DFM judgement canon G-SELFCON already records
  (61 of pluto-rx2-8way's 64 refdes sit below the published stroke), NOT a new
  P0: the tier's 0.45 mm height is annotated *proven by ordering*, and taller
  glyphs strand more refdes off silk entirely. Recorded with both numbers.
- **4 silk-to-pad gaps below JLC's published 0.150 mm**, three of them 0.0000:
  two PINNED captions print over `Q_SWDRVA` pads 1/2/3 and over `TP_RKEY.1`.
  Cheap to fix (a coordinate nudge) and deliberately deferred into the same pass
  as the P0, because a placement change moves silk again.

## Refutations recorded (canon: record, do not delete)

The layout lens validated its own resistance solver against a hand-computable
net (21.549 vs 21.741 mOhm, the difference being a parallel stub), reproduced
DRC independently at 0/0/0, reproduced ADR-0015's H4 creepage at **4.029 mm vs
its 4.0286 mm by a different construction**, and KILLED ITS OWN BEST P0
CANDIDATE: `HS_GATE_COIL` crosstalk at 10.169 mm delivers ~3 pC where V_GS(th)
needs 250 pC — two orders short. It could not break the isolation work: keypad
comb **6.2344 mm** on its worst layer pours-filled, the 30 V moat **2.0005 mm**
on all four layers, the opto barrier **7.530 mm** pad-to-pad, In1.Cu ground one
**8476.6 mm2** island. Topology refuted 16 of its own hypotheses including the
P-FET orientation, the crowbar's position, the coil freewheel path, the
open-thermistor detect (which WORKS), the `J_MODE` 3-4 short, and **E-OFF, which
passes with its off-control traced as a real series element** — and found no
permissive default anywhere in the seven-term chain, the fault latch, the re-arm
or the STOP path. Render refuted five of its own, including the claim that the
1.00 mm comb web breaks the ">=6mm creepage" silk (min straight-line F.Cu gap
straddling the comb is **6.53 mm**), and confirmed **all nine diodes and CE1
polarity-correct two independent ways**. The pin lens found **zero pin-map
FAILs** across 41 graded parts, re-derived the relay land from the datasheet
figure without reference to the footprint (**PASS x12**), and confirmed
`01_docs/pin_map.md` against all 40 Pi header pins with zero mismatches.
