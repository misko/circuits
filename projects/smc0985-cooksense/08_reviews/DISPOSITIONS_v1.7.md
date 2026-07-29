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
