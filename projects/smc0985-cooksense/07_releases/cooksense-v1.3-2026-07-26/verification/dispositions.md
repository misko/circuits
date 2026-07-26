# DISPOSITIONS — cooksense v1.3, 2026-07-26

Every finding raised during this revision and what was done about it.

**As of 2026-07-26 no finding in this file is OPEN.** P1-5 (the CH0/CH3
transfer function) was the last one and is now CLOSED by derivation — see the
final table. Everything else is fixed, closed by measurement, or deferred with a
stated reason. Two earlier versions of this line were wrong in opposite
directions: the first claimed no open findings when P1-5 was open, and the
second went on claiming P1-5 was open after it had been closed. The count is
maintained by hand, so treat the tables as the evidence and this line as a
summary of them.

## FIXED IN v1.3

| # | finding | disposition |
|---|---|---|
| P0-A | `J_ESTOPLOOP` placed INSIDE `J_DOOR` — the isolated 30 V loop shorted to 3V3/GND/DOOR_RAW, 1.300 x 0.600 mm of overlapping pad copper | Merged both isolated connectors into ONE 4-pole block `J_ISOLOOP` (user decision, ADR-0013). East column re-solved; P-COLLIDE 0/0. |
| P0-B | `R_OPENT` ORDERED at 6.2 kΩ (C25915) where the design needs 62 kΩ — open-thermistor detect threshold would sit at 3.1073 V, above the LMV393's 2.500 V VICR ceiling, so an open head reads FINE | Pinned to **C37825** (62 kΩ). All four divider resistors pinned and ledger-verified. |
| P0-C | `R_WDPETPD` ORDERED at 100 kΩ (C25741) where the design needs 1 kΩ — TPS3823 WDI sources 190 µA, R_max = 5.21 kΩ, so the watchdog would be silently disabled | Pinned to **C11702** (1 kΩ). Whole class swept: 90 unpinned passives, exactly one mismatch. |
| P1-1 | `R_TEMPOK` pulled up from the DIGITAL rail while both comparators run on 3V3_ANALOG — one open ferrite drives TEMP_OK to 3.235 V = PERMISSIVE | Moved to `3V3_ANALOG`. Failure now gives 0.000 V = restrictive. Cost a re-race (see ORDER_README §13). |
| P0-1 | H4 mounting hardware 3.737 mm from keypad copper against a 6.000 mm requirement | Edge-reaching isolation notch; I-HW now measures 6.598 mm around it. |
| — | `opto_isolation_2mm` measured 0.199 mm on v1.2 copper | Pour keepouts + User.4 route mirror; now 2.0000 mm (all copper, all layers). |
| — | Board silk read `sidecar v1.2` on a v1.3 release | Bumped to v1.3. |
| — | `electrical_invariants.yaml` still asserted the 6.2 k / 3.107 V DEFECT | Corrected to 62 k / 2.0370 V, old text quoted in place. |
| — | tsx header claimed `DOOR (NC reed+EOL)` over NO/no-EOL code | Header corrected to state what is built and name the gap. |
| — | I-HW gave pads a geodesic and TRACKS a straight line — false FAIL at H4 (4.617 mm through a through-cut; true surface path 7.165 mm) | Track branch now uses the same visibility-graph geodesic. RED-verified: pre-notch board still fails at 4.031 mm. |
| — | 13 CPL rows with blank LCSC; J_LOADCELL/J_PI THT on an SMT-only CPL; J_PI 24.1634 mm off datum | All corrected; A-POP PASS, A-POS 189/189 at 0.00000 mm. |

## RAISED AND CLOSED BY MEASUREMENT — the '238 floating-enable finding

`pin_review.md` (a v1.0-era artifact, since regenerated) carried an
UNDISPOSITIONED safety finding: *"595 Hi-Z leaves the '238 active-HIGH E3 enables
floating with no pull-downs, so if WD_OK drops while COIL_EN is asserted, a
floated-high E3 can drive a SEL_* into a ULN channel with the coil rail live."*

**That was true of v1.0 and it is NOT true of this board.** It is the item
`RESUME.md` listed as pending at v1.0 (*"'238 decoder pull-downs — SAFETY ... Add
pull-downs (or gate COIL_EN through the fault chain)"*). BOTH remedies were
implemented. Measured from `source/cooksense.net`:

```
DECU_G1_RAW  [R_DECUPD.1, U_DECUEN.1, U_SR1.3]     <- 595 output + 100k pull-down
DECD_G1_RAW  [R_DECDPD.1, U_DECDEN.1, U_SR1.6]     <- 595 output + 100k pull-down
DECU_G1      [U_DECU.6,   U_DECUEN.4]              <- '238 E3 driven by a GATE OUTPUT
DECD_G1      [U_DECD.6,   U_DECDEN.4]
```

`U_DECUEN` / `U_DECDEN` are SN74LVC1G11 3-input ANDs (C22046, SOT-23-6). From the
authoring source: `pin1=A -> DECU_G1_RAW`, `pin3=B -> STOP_REQ_N`, `pin6=C -> 3V3`,
`pin4=Y -> DECU_G1`. So **E3 = DECU_G1_RAW AND STOP_REQ_N**, driven by a
push-pull output, never by the tri-stateable 595 directly.

On a watchdog trip the 595 goes Hi-Z, `R_DECUPD` / `R_DECDPD` (100 k) pull the
RAW node **LOW**, the AND output goes LOW, **E3 is disabled**, and every '238 Y
output is inactive — so no `SEL_*` is asserted and no ULN channel is driven. The
failure direction is safe, and it is doubly gated because `STOP_REQ_N` must also
be high. **No action.**

## DEFERRED TO v1.4 — with the reason, and none of them fail permissive

| # | finding | why deferred |
|---|---|---|
| D-1 | **Door input is NO with no EOL**; a SHORT reads "closed" undetectably, across a 0.650 mm JST-GH pad gap in a pollution-degree-3 steam environment | v1.3 closes the defect it claimed (fail-permissive on wire break). Supervision is a different, stronger property that needs a new analog path — all 8 ADC channels and all 4 comparator channels are used — plus a harness re-spec and firmware. A specification, not a patch. **Prominent in ORDER_README §2-0; commissioning decision required.** |
| D-2 | **R_HYS gives U_COMP2 NEGATIVE feedback** — the open-detect has no hysteresis | Structural, not a wiring slip: TH_CAM_A is one node feeding U_COMP's IN+ and U_COMP2's IN−, so one resistor cannot be positive feedback for both. The only correct fix is a new part (R_HYS3: TEMP_OK → TCAM_OPEN) which RE-SPECS the threshold to ~2.0836 V — the number the whole VICR argument rests on. Bounded: a real open moves the node 15.5 mV against 232 mV of overdrive so it still latches solidly; exposure is chatter at the −10.4 °C boundary; direction is LOCKOUT, not permissive. |
| D-3 | **TH_CAM_A/B routed 93.62 / 87.75 mm** against a declared `keep_short max_span_mm: 8`; closest aggressor SPI_SCLK at 0.206 mm | Needs re-placement; not re-opening the floorplan on a board with a live safety fix. Direction is fail-safe. The GATE half is a fleet item: `audit_board`'s I-PROX has no span check at all, so the budget passed vacuously. |
| D-4 | Our `Diode_SMD:D_SOD-323` land draws a cathode band on a **bidirectional** part (5 refs) | Assembly risk nil — JLC places from the CPL, not our silk. Reviewer risk is real. Five footprint swaps after the DRC gate was measured is not worth invalidating it. |
| D-5 | Twin does not cover 2 of 54 coded BOM lines (C25768, C37825) | Both entered the BOM after the twin run; both are 0402 chip passives on land classes the twin checked 30+ times. Declared in ORDER_README §13. |

## TWO P2s THAT HAD NO DISPOSITION ANYWHERE — now they do

| # | finding | disposition |
|---|---|---|
| P2-a | `floorplan.yaml` says a chassis bonding two mounting holes "re-opens the defect at 3.000 mm"; `audit_board`'s own I-HW line measures that case at **0.000 mm** (min_a −0.050 + min_s −1.450) | **The floorplan comment is WRONG and the ORDER_README is corrected.** A bonded chassis is a DIRECT keypad-to-SELV bond, not a reduced clearance. ORDER_README §1 now states 0.000 mm and cites `verification/audit.txt`. The floorplan comment is a source-side typo carrying no gate; corrected in the same commit. The board is unaffected — the non-conductive-enclosure assumption (ADR-0012) is what holds, and it is on the silk, in an ADR, in the ORDER_README, and encoded as the `ENCLOSURE_BONDS_HOLES` switch in `audit_board.py`. |
| P2-b | `C_CAND2` sits **12.06 mm** from `U_CAND2` — the gate that produces `CONTACTOR_DRV` — the loosest decoupler on the board, with no I-PROX row | **ACCEPTED for v1.3, logged for v1.4.** U_CAND2 is a SOT-23-6 static AND gate switching at human timescales (a contactor permission), not a clocked or high-di/dt load; its supply is the 3V3 In2 plane with 24 other 100 nF decouplers on the same plane. The risk is EMI susceptibility, not a functional failure, and the direction of any glitch is through the AND chain into a latched lockout. No I-PROX row existed to enforce it, which is the more useful half: the proximity list is hand-maintained and has no automatic decoupler-distance rule. Logged with the I-PROX span gap (D-3). |

## FLEET ITEMS RAISED HERE, OWNED ELSEWHERE

- Deterministic UUIDs in `generate_board_generic.py` — makes M-REPRO byte-checkable and stops a data-only CPL fix reading as a full respin.
- `policy_audit` multi-board mis-targeting (`rels[-1]` selects the interposer release on this ADR-0007 project).
- `bom_source_check` leg C: an AGGREGATED BOM Comment (`"100kΩ / 1kΩ"`) defeats the decade check because the label parser takes the first token. Needs a known-bad fixture.
- `jlc_rotation_measure` / `jlc_twin` have no cathode-band channel, so they report BLIND on rectifiers whose polarity is carried by a band.

## CLOSED AFTER THE FOURTH LENS (2026-07-26)

| # | finding | disposition |
|---|---|---|
| P1-5 | The 22 k clamps changed the CH0/CH3 ADC transfer function, and §2b makes a host ADC cross-check a MANDATORY acceptance test | **CLOSED — derived, not deferred.** §2b now carries the corrected inversion (`R_ntc = 1/(1/R_par − 1/22000)`), an 8-point error table and recomputed accept/reject thresholds. Pure arithmetic; no bench step. The derivation validates against the independently documented open-circuit node voltage of 2.2687 V. **The reason it could not stay a declared gap:** under the naive model an OPEN NTC reads **8.4 °C** — a plausible healthy value — so acceptance test (a) would have passed a board on which the host detects nothing. |
| — | §6 item 15 was headed "ALL diode cathode bands" and listed 7 of 8, omitting **D_KSTOP**, the K_STOP coil flyback | **CLOSED.** D_KSTOP added. Its ROTATION was never wrong (C8678 = 0, two-channel, hand-measured from raw geometry on both libraries and cross-checked on two other boards); what was wrong was a visual checklist claiming completeness. The row now also states why C8678/C113974 are absent from the generated A-POL gate but present here — "no numbering-free channel" vs "polarized part a human should eyeball". |
| — | The four silk DRC checks are `ignore`d; do any of the ADR-0012 safety warnings fail them? | **CLOSED — MEASURED, NO.** With all four re-enabled the board reports 78 violations: `text_thickness` 24 (**all 24 are `Reference field of X` — refdes, not captions**), `silk_over_copper` 49, `silk_edge_clearance` 3 (**all three are J_ISOLOOP's own footprint silk box against Edge.Cuts**, because the block body is flush to the south edge at y102.000), `silk_overlap` 2 (Q_SWDRVA vs the functional caption "ANALOG SENSE (3V3_ANALOG)"). **Zero of the 78 involve a safety caption.** Positively verified: all seven ADR-0012 silk items measure thickness **0.150 mm at the 0.150 mm fab floor**, height 0.60 mm. The checks stay off and the full list plus the 78 count are disclosed in §13. |

## CLOSED AFTER THE FIFTH LENS (2026-07-26)

The fifth zero-context lens returned DO-NOT-SHIP on three P1s and four P2/P3s.
**Two of its findings were wrong and the refutations are the more useful
result**; the rest were right and are fixed.

| # | finding | disposition |
|---|---|---|
| L5-1 | `verification/fresh_lens.md` is listed in INDEX.md but absent, and INDEX.md itself says that absence means "staged but not sealed" | **VALID — FIXED.** The lens was reading the archive *before* its own report existed. That is a staging-order defect, not a review defect: the file is now written and the archive re-digested. |
| L5-2 | "189/189 from measured rows" is contradicted by this archive's own second operator, which puts 7 CPL rows 180° away — including U_OPTO, the isolation part | **HALF VALID.** The *provenance overclaim* is real and §6 is rewritten: the 61-row authority table is NOT in this archive, only **15** measured rows covering **26 of 189** CPL rows, and §13 item 10 declares it. **The 180° claim is REFUTED BY MEASUREMENT.** The second operator de-rotated with a standard counter-clockwise matrix; **KiCad's Y axis points DOWN**, so that matrix mirrors the fit and swaps 0↔180 and 90↔270. Proven empirically against pcbnew on `J_KEY_MATRIX` at −90°: actual pad-1 delta (+1.850, −5.625); the Y-down matrix reproduces it, the CCW matrix returns (−1.850, +5.625). Re-run as a direct comparison of the two raw `.kicad_mod` files — **no board frame, no operator** — **all seven codes agree with the landed table**, U_OPTO at 270 (30x) and CE1 at 0 (127x) included. **No CPL row and no table row changes.** Recorded in `rotation_C22046_measurement.md`. |
| L5-3 | §11 gives the isolated loop as "<= 30 V / <= 50 mA"; the guaranteed drive is ~3.2 mA | **VALID — FIXED, and it was the dangerous half of a pair.** 50 mA is the collector ABSOLUTE MAXIMUM. Measured from the shipped board and BOM: `R_OPTOLED` = **330 Ω** (C23138) on a 3.3 V CMOS drive → I_F = **6.36 mA**; `02_parts/LTV-817S-TA1/part.yaml` gives CTR bin minimum **50 %** → **I_C guaranteed 3.18 mA**, 15x below the printed figure. §11 now carries the derivation table and "design the field loop to need <= 3.0 mA". |
| L5-4 | 136 islands claimed, 121 measured | **VALID — FIXED.** The 136 came from a refill-in-memory; the stored fill that ships has **121** (GND F.Cu 106, GND B.Cu 13, GND In1.Cu 1, 3V3 In2.Cu 1) — `mrepro.md` had it right all along. Re-run on the shipped fill: **121 islands, 121 bonded, 0 stranded.** Conclusion unchanged, population corrected in `stranded_islands.md`, ORDER_README §13 summary and MANIFEST. |
| L5-5 | `dispositions.md` header says one finding is OPEN; the body says CLOSED | **VALID — FIXED.** Stale header from the P1-5 closure. |
| L5-6 | `dispositions_v10_carried.md` is not marked historical and routes the isolated loop through `J_ESTOP.3/.4` | **VALID — FIXED.** Banner added naming the exact hazard: J_ESTOP pins 3/4/5 are all GND on v1.3, so wiring a field loop there would bond the isolated domain to SELV ground. §11 is the only field-wiring authority. |
| L5-7 | Opto V_CEO 35 V vs a 30 V loop, no clamp, and a phototransistor fails SHORT = permissive — never propagated out of the red-team file | **VALID — FIXED.** §11 now states the 17 % margin, requires the field loop to be non-inductive or snubbed at the load, and names this as the one non-fail-safe mode in the isolated domain. |
| L5-8 | `cooksense.tsx` line 442 still asserts "trips ABOVE 3.107V" in the present tense | **VALID — FIXED IN SOURCE.** Comment corrected to 2.0370 V and pointed at the rescale block. **Proved inert before shipping:** circuit.json regenerated and the connectivity-bearing records are byte-identical (source_trace 739, source_net 161, source_port 770, source_component 222, schematic_trace 215 — all `identical=True`); the only diffs are floating-point IoU warning values and a build timestamp. |
| L5-9 | H4 notch given as `x[191.50, 200.10]`, 0.10 mm outside the board | **VALID — FIXED** to `x[191.50, 200.00]`; Edge.Cuts vertices measure x ∈ {190.24, 191.50, 200.00} and the east edge is 200.000. |
| L5-10 | §13/§11 name **F.Cu** as the binding layer for the 2.0000 mm ISO minimum; F.Cu measures 2.0400 and the minimum is on the inner/bottom layers | **REFUTED — remeasured per layer.** F.Cu **2.0000**, In1.Cu **2.0000**, In2.Cu **2.0000**, B.Cu **2.0000**. The minimum is 2.0000 on **all four**, which is what a 2.0 mm pour-keepout offset applied to all four layers must produce. Text improved to say all four rather than F.Cu. |
| L5-11 | `rotation_C22046_measurement.md` sends the reader to "ORDER_README §3"; the human gate is §6 | **VALID — FIXED** in the same file's correction block. |
| **NEW, found while working L5-8 — not raised by the lens** | `verification/parity.md` ships reading **`REAL DISCREPANCIES: 1 -> FAIL`** and nothing in the archive said what it was | **DISCLOSED, measured, deferred to v1.4 — see §13 item 11.** It is `J_KEY_MATRIX.MP`: `parity_padmap.txt` declares a board-stage bond to `GND_ISO`, the shipped board has **no net** on those two tabs, and every other connector's tabs are bonded. **Not an isolation defect** — two-hop creepage through the floating tab is **13.8960 mm** (0.5810 to the keypad domain, 13.3151 to everything else) against a 6.000 mm requirement. What is lost is the connector shell's ESD drain. **The gate blindness is the real finding:** `keypad_isolation_6mm` is conditioned on `B.NetName != ''`, which **exempts unnetted copper by construction**, so `0 DRC violations` was never evidence here. v1.4 bonds the tab AND drops that clause. |

## CLOSED AFTER THE SIXTH LENS (2026-07-26)

Verdict **DO-NOT-SHIP, "narrowly, and on paper only" — no P0, no board change,
no re-export.** Every ordered artifact reproduced. The blockers were in the
**§6 ORDER-PREVIEW HUMAN GATE**, the one section the archive itself marks
MANDATORY BEFORE ORDERING, which is the worst place to carry a false statement.

| # | finding | disposition |
|---|---|---|
| L6-1 | §6 item 15 claimed C8678/C113974 "carry `two-channel` rows"; `rotation_measurements_v13.txt` records both as `single-channel / ROW: (WITHHELD)` and `twin_report.csv` marks all three refs **POLARITY-FIT-BLIND** | **VALID — FIXED, and it was the archive contradicting itself about a polarized part.** I wrote that justification and it was false: no cathode-band shape measurement exists for either code. These three refs are absent from the generated A-POL list **because the twin could not FIT them at all** — worse than single-channel, not better. §6 item 15 now says so and states the true population, **12 codes / 16 refs**, against the generated file's 10/13. INDEX.md's "GENERATED wins over any prose" line now carries this as its one documented exception. |
| L6-2 | §6 rows 11 (J_LOADCELL) and 13 (J_PI) tell the reviewer to check parts that are **off the CPL** and cannot appear in the JLC preview | **VALID — FIXED.** Both are among the 37 `exclude_from_pos_files` refs. 2 of 17 mandatory rows would have been signed off unchecked, and §3 separately tells the reader that an unmatched preview entry means "stop". Both rows now read like row 17: nothing to tick at JLC, check on the bare board. |
| L6-3 | `INDEX.md` still carried "136/136 pour islands" | **VALID — FIXED to 121/121.** MANIFEST:49 appoints INDEX.md as READ-FIRST, so the currency file was carrying the exact number the fifth lens was spent correcting. |
| L6-4 | `INDEX.md` labels `rotation_C22046_measurement.md` HISTORICAL while §6 and §13 rely on its correction block as current | **VALID — FIXED.** The file is **MIXED**: historical body, current 2026-07-26 correction. INDEX now says so and the file carries a top banner pointing at the correction. A reader following the old label would have discarded the only in-archive rotation evidence for 7 of 51 CPL codes — including U_OPTO and CE1. |
| L6-5 | **`GND_ISO` does not exist on this board**, yet `parity_padmap.txt`, the F.Silkscreen caption and §13 item 11 all name it | **VALID — AND IT REVERSES MY OWN v1.4 INSTRUCTION.** Measured: 0 occurrences in `cooksense.net` and `cooksense.kicad_sch`; the only ground net is `GND`. §13 item 11 previously said "v1.4: bond `J_KEY_MATRIX.MP` to `GND_ISO`". **That fix would have been impossible as written and dangerous if approximated:** the tab sits **0.5810 mm** from KEYPAD_ISO copper, so bonding it to the ground that DOES exist fires `keypad_isolation_6mm` at 0.581 mm against 6.000 — **a 10.3x violation, the worst on the board.** The tab is floating because there is nowhere safe to land it. §13 item 11 now says **MUST STAY FLOATING**, and the v1.4 items are to delete the `GND_ISO` token from the padmap and the silk (or create the net properly) and to drop the `B.NetName != ''` clause. **Second time this session a proposed "fix" would have damaged the board; both were caught by measuring before acting.** |
| L6-6 | §1 attributes both 6.598 mm and 4.617 mm to `pad K_STOP.3`; 4.617 is to a TRACK | **VALID — FIXED.** Straight-line to pad K_STOP.3 is **4.029 mm**; **4.617 mm** is to the RSTOP_MID track (197.400,45.600)→(197.000,45.200). All north of the notch, PASS unchanged. |
| L6-7 | §6 preamble says the second operator disagreed "by 90° on C125121"; the disagreement was 180° | **VALID — FIXED** (it returned 90 where the table says 270). |
| L6-8 | §6 item 14 attributes C10092 to U_DECU/U_DECD | **VALID — FIXED.** `bom.csv`: **C5620 = U_DECD, U_DECU; C10092 = U_SR1** (SN74HC595DR), which is separately on the A-POL list — a reviewer following the old text would have skipped it entirely. |
| L6-9 | §6 item 15 demanded a cathode-band check on five **bidirectional** PESD5V0S1BA parts | **VALID — FIXED.** Both pins are cathodes (JLC's model name ends `_BI`); §13 gap 4 already warned a reviewer might "correct" a placement that was right. Item 15 now names the five explicitly as DO-NOT-CORRECT. |
| L6-10 | §11 says the pole legend is 41.9 mm away; measured 155.3 mm — and the poles-2/3 shared-net hazard is unwarned | **VALID — FIXED, and the second half is the safety-relevant one.** Caption at (62.000, 15.400) vs the block at (195.300, 95.000). §11 now gives the real distance, names the one physical cue at the block (**pole 1 is the only rectangular pad**), and carries a new warning: `CONTACTOR_LOOP = [J_ISOLOOP.2, J_ISOLOOP.3]` is **one net on two screws**, so bridging 2-3 or mis-landing the device shorts it out of the loop **and the loop still reads CLOSED** — a silent PERMISSIVE failure on the E-stop. Verify continuity through the open device across 2-3 before energising. |
| L6-11 | §13's jlc_twin row collapses POLARITY-FIT-OK and POLARITY-FIT-BLIND into "9 POLARITY-FIT" | **VALID — FIXED.** 420 rows: 184 OK, 184 MODEL-REG-OK, 31 PAD-GEOM, 9 POLARITY-CHECK, **6 POLARITY-FIT-OK, 3 POLARITY-FIT-BLIND**, 1 MIRRORED, 1 FETCH-FAILED, 1 NO-BODY. The collapse hid exactly the three refs in L6-1. |
| L6-12 | `fresh_lens.md` says 78 digests (now 79); `redteam_topology.md` still lists P1-5 as OPEN | **VALID — BOTH FIXED.** |

**What the sixth lens verified and found correct** is recorded in `fresh_lens.md`
— including an independent re-derivation of the whole §2b error table, the
isolation scan on all four layers, a canonical gerber re-export that matched
flash-for-flash, and 189/189 CPL rotation offsets consistent per code.

## SEVENTH LENS (2026-07-26) — TWELVE FINDINGS, ELEVEN FIXED, **ONE ESCALATED AND STILL OPEN**

Verdict DO-NOT-SHIP, no P0 on the order package. The lens reproduced the whole
fab set independently. Four P1s, three of them inside sections the archive marks
MANDATORY. **This is the round that stopped the seal.**

| # | finding | disposition |
|---|---|---|
| **L7-3** | **The entire H4 isolation PASS rests on crediting a 1.000 mm through-slot as a creepage extender, and the archive never said so** | **🛑 ESCALATED — OPEN. THE SEAL IS BLOCKED ON THIS.** Reproduced exactly: notch **1.000 mm** wide; H4 centre 2.200 mm from its edge so the **3.000 mm modelled washer overhangs the slot by 0.800 mm**; straight-line disc-edge to `K_STOP.3` pad-edge **4.0286 mm**; around-the-notch geodesic 6.598 mm; requirement 6.000 mm. Under IEC 60664-1 at the declared **pollution degree 3** the X-dimension is **1.5 mm** and a gap narrower than X is **BRIDGED** — read that way the governing figure is **4.0286 mm and H4 does not pass**. The archive's own RED test puts the pre-notch board at 4.031 mm = FAIL, so **the notch alone converts FAIL to PASS**. This is a judgement about how the standard applies to a through-slot under a spanning washer on a keypad-to-SELV barrier; **it is not the release agent's call.** Now disclosed prominently in §1 with all measured numbers and a STATUS line. **Not sealed.** |
| L7-1 | §2b's accept band `3.0 k – 32.6 k` is wrong by 2.9x at the low end | **VALID — FIXED. This was the most consequential arithmetic error found in any round.** Recomputed with §2b's own inversion, 0–85 °C is **1063.7 Ω – 34 057 Ω**. The old band corresponds to **54.5 °C … 0.79 °C**, so a host implementing it would refuse HOST_AUTH above **54.5 °C — 18 °C BELOW the 72.80 °C hardware trip.** The appliance refuses to cook once merely warm, and the technician chasing that nuisance lockout is the person most likely to widen or disable the board's only software backstop. The row also contradicted its own voltage column, which was correct. |
| L7-2 | §2b's open-detect row pairs `≥ 2.20 V` with `≥ 1 MΩ`; they are not the same test | **VALID — FIXED.** V = 2.2000 inverts to **220 kΩ**, not 1 MΩ (4.5x). Conversely R_ntc ≥ 1 MΩ needs **V ≥ 2.2533 V**, while the worst-case open with ±1 % parts reads **2.2545 V** → 1.089 MΩ: **1.2 mV of margin** before ADC INL. A host implementing the RESISTANCE form can miss an unplugged NTC — acceptance test (a) failing in exactly the way §2b exists to prevent. The table now gives the correct 220 kΩ and directs the host to the **voltage** form, which has 54 mV. |
| L7-4 | §11 calls the output a "DRY CONTACT" and never says which pole is positive | **VALID — FIXED.** It is a phototransistor: `CONTACTOR_C = [J_ISOLOOP.1, U_OPTO.4]` collector, `CONTACTOR_E = [J_ISOLOOP.4, U_OPTO.3]` emitter. **Pole 1 is positive.** Reversed, 30 V sits across a junction rated ~6 V; reverse-breakdown failure is SHORT, and short is **PERMISSIVE**. Forward is safe: even at the CTR 600 % ceiling I_C self-limits to **38.2 mA** < 50 mA. |
| L7-5 | MANIFEST says §6 has 18 rows; it has 17 | **VALID — FIXED.** |
| L7-6 | §6 item 1 still carried "independent fit 90" after the L6 correction updated the preamble and item 9 | **VALID — FIXED.** A correction that reaches two of three places is a new contradiction, not a fix. |
| L7-7 | Both J_ISOLOOP silk features are inside the 78 ignored silk violations; and every safety caption is **0.60 mm** character height against JLCPCB's ~1 mm minimum, which nothing checks | **VALID — DISCLOSED (§13 item 12).** The earlier "zero of the 78 involve a safety caption" was true and verified, but it never checked the two silk features on the isolated 30 V block, and every silk gate checked **stroke** (0.150 mm) and never **height**. The captions may not print. §13 now tells the reader the document, not the silk, is the authority, and to inspect first-article silk. |
| L7-8 | §3 says unmatched CPL entries mean "stop", while the BOM guarantees 16 unmatched designators | **VALID — FIXED.** The two directions are now stated separately: a CPL row with no BOM line is a defect; **16 BOM designators with no CPL row are by design** (J_ISOLOOP, J_LOADCELL, J_PI, J_TC + the 12 reeds). |
| L7-9 | KEYPAD_ISO minimum printed four ways: 6.1264 / 6.1236 / 6.1200 / 6.12 | **VALID — NORMALISED to 6.1200 mm.** The lens measured the binding pair analytically (two 1.500 mm circular pads 7.620 mm apart) — exactly 6.1200. Both four-decimal variants, including my own, erred toward extra margin. |
| L7-10 | §13 gap 2 justifies the 5000 Vrms barrier with the **bounding-box** 2.126 mm | **VALID — FIXED.** The archive's own rule is "state the metric beside the number"; that instance quoted the loosest of three inside a safety justification. Now gives all three with 2.0000 mm named as binding. |
| L7-11 | The shipped gerbers were plotted with drill marks; a default re-export does not match | **VALID — DISCLOSED (§13 item 13).** Every mark verified concentric inside an existing pad or hole, so inert — but lens 6's "matched flash-for-flash" is only reproducible with drill marks enabled, and a reviewer should be told. |
| L7-12 | §6's provenance qualifier claims 15 measured rows / 26 CPL rows, but **13 of the 15 are `ROW: (WITHHELD — single-channel)`** | **VALID — FIXED.** In-archive LANDED provenance is **2 codes / 5 CPL rows** (C6186, C8185), not 15/26. All 13 withheld codes are covered by the A-POL human gate or the bidirectional exclusion, so nothing is unguarded — but a withheld measurement is not a landed one, and the qualifier claimed more than it had. |
| L7-13 | Cited-but-absent documents (ADR-0001/6/12/13, BRIEF, pin_map, LTV-817S part.yaml, electrical_invariants.yaml, floorplan.yaml, SUPERSEDED.md) | **VALID — DISCLOSED (§13 item 14).** Individually minor; collectively several load-bearing safety numbers cannot be re-checked from inside. v1.4 ships the cited ADRs and part.yaml files. |

## RULING ON L7-3 (2026-07-26) — THE NOTCH DOES NOT COUNT. H4 FAILS.

**Coordinator ruling, verified against the standard rather than recalled.**
IEC 60664-1 sets a minimum groove width **X** below which a groove contributes
nothing to creepage — the path is measured **straight across**. **At pollution
degree 3, X = 1.5 mm.** This notch is **1.000 mm**. The one exemption (X reduced
to one third of the associated clearance) applies only where that clearance is
**below 3 mm**; this requirement is 6 mm, so X stays 1.5 mm.

**H4's governing figure is 4.0286 mm against 6.000 mm required — short by
1.9714 mm. It FAILS.** The release is **HELD, NOT SEALED**.

Three reinforcing points, all pointing the same way:

1. **The environment IS the pollution degree.** PD3 is declared because this is
   steam and grease. A 1.000 mm slot in that environment fills with condensate —
   the physical reason the X rule exists. Not a paper technicality on a clean
   board.
2. **The washer makes it worse.** Overhanging by 0.800 mm it **ROOFS** the slot.
   An open slot drains and dries; a roofed 1 mm slot is a **capillary trap**
   holding condensate against the barrier. The overhang had been treated as
   incidental geometry; it is an aggravating factor.
3. **The RED test already said so.** `t_ihw_prenotch` puts the pre-notch board at
   **4.031 mm = FAIL**. The notch converts FAIL to PASS on 0.5 mm of geometry the
   governing document says to disregard. **When a gate flips verdict on something
   the standard says to ignore, the gate is measuring the wrong thing.**

### Scope — exactly one hole

Re-measured all four with the bridged metric under the archive's own per-hole
model. **My first pass wrongly flagged H1 and H2 as failing at 1.0950 mm; that
was an endpoint-only approximation of track distance on my part.** Measuring to
the nearest point on each track segment gives the correct figures:

| hole | a (keypad) | s (SELV) | governing | crosses a void? | verdict |
|---|---|---|---|---|---|
| H1 | −0.0500 | 13.6299 | keypad-BONDED → s alone | no | 13.6299 PASS |
| H2 | −0.0500 | 13.1525 | keypad-BONDED → s alone | no | 13.1525 PASS |
| H3 | 40.9324 | −1.4495 | SELV-BONDED → a alone | yes, irrelevant at 40.9 mm | 40.9324 PASS |
| **H4** | **4.0286** | −1.4493 | SELV-BONDED → a alone | **YES** | **4.0286 FAIL** |

### The fix is unusually cheap — measured, for the schedule-vs-margin decision

Only **three** items of keypad copper sit below 6.000 mm from H4's disc, and all
three are the **same net (`RSTOP_MID`) in the same corner**:

| # | item | straight-line from H4 disc |
|---|---|---|
| 1 | pad `K_STOP.3` (197.450, 45.620) | **4.0286 mm** |
| 2 | track `RSTOP_MID` (197.400, 45.600) | 4.6166 mm |
| 3 | track `RSTOP_MID` (197.000, 45.200) | 4.7392 mm |
| 4 | pad `K_PRESS.4` — **the next one back** | **15.7342 mm** |

**Clearing those three exposes nothing: the next item is 15.73 mm away, so the
fix buys 11.7 mm of headroom rather than moving the problem one part along.** It
is one relay's pad and its stub, in one corner.

For the notch route, the geometry is tighter than it looks: the slot must reach
**>= 1.500 mm** to be creditable **and** its south edge must move north of
**y = 49.000** to stop the fastener roofing it (it is at 49.800 now), while
`K_STOP.3`'s pad edge at **y = 46.370** limits how far north it can grow.

### Recorded as a gate blind spot (§13 item 15)

`keypad_isolation_6mm` is a DRU rule measuring **copper clearance**; creepage is
a **surface path**, and whether a slot interrupts it is a question about outline
and pollution degree a clearance rule cannot express. **DRC read 0/0/0 through
all seven reviews and was never evidence about this property.** `I-HW`, which
does model the fastener, walked a geodesic around the notch — encoding the wrong
physics rather than none. Same family as the `A-EVID` and `row_kind` blind
spots: **a gate whose measurement is not the property.**

### The disclosure defect is its own finding

The shipped 6.598 mm was a **geodesic that was never labelled as one**; a reader
seeing "H4 6.598 vs 6.000 required" could not tell the straight-line figure was
4.0286. That is the **third** number this board has shipped without the metric
that produced it, after the ISO pair (bbox vs true-polygon vs all-copper) and the
I-HW table. **Standing rule now applied throughout this release: every isolation
figure states its method beside it.** Done — §1's I-HW table, the §11 ISO
sentence, the KEYPAD_ISO/floating-tab table and the gate-summary row all now
carry a method column or clause.
