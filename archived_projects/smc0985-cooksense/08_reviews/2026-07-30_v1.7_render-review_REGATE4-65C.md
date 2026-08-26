# Render + paperwork review — cooksense MAIN v1.7, re-gate 4 (65 °C declaration)

- reviewer: fresh-context render reviewer, no prior design context, work class JUDGMENT
- subject: `06_build/staging/cooksense-v1.7/` (PRE-SEAL STAGING ARCHIVE)
- date: 2026-07-30
- lens: renders, twin CAD renders, PDFs, and `ORDER_README.md` **as a document a
  human must use** — read the way a technician unpacking the board reads them
- inputs read: the staging archive, `01_docs/BRIEF.md`, `01_docs/decisions/`,
  `02_parts/`. **Deliberately NOT read** (independence): `01_docs/journal/`,
  `01_docs/learnings/`, `01_docs/STATUS-*.md`, `RESUME.md`, all of `08_reviews/`,
  and the archive's own `*redteam*`, `pin_review.md`, `render_review.md`,
  `DISPOSITIONS.md`. `policy_waivers.yaml`, `policy_audit.md` and the mechanical
  gate outputs WERE read — they are machine config/output, not review opinion —
  and where I quote them I say so.

```
design_verdict: SOUND
order_verdict:  BLOCKED-SOURCING
```

**P0 count: 0.**

---

## What I actually see, in one paragraph

A 188 × 92 mm, 4-layer, top-populated-only board with a hard visual split. The
northern 40 % is a black, deliberately un-poured **keypad isolation comb** — 12
tall DIP-14 reed-relay outlines in a row, alternating 0°/180°, with twelve milled
slots threaded between them, and four lines of hazard silk across the top
(`J_ISOLOOP (SE CORNER) = ISOLATED 30V CONTACTOR LOOP -- NOT SELV -- POLES 1=C
2=LOOP 3=LOOP 4=E`, the nylon-hardware rule, the ADR-0012 plate warning, and
`KEYPAD ISOLATION COMB >=6mm creepage NO GND BOND`). The southern 60 % is a
dense red SELV pour carrying the LDO, the ADC/thermocouple front end, the
AND-chain and the expander, with every field connector on an outside edge:
`J_KEY_MATRIX` west, `J_PWR` / `J_MODE` / `J_ESTOP` / `J_ISOLOOP` on the west and
east edges, and `J_THERM_A`, `J_THERM_B`, `J_TC`, `J_PI`, `J_LOADCELL`,
`J_RH_AMBIENT`, `J_RH_EXHAUST` along the south edge. The bottom side (measured:
`bottom layer: []`, 0 footprints on B.Cu) carries a solid pour, no silk text, and
the same comb void. It is a legible, well-zoned board and the hazard silk is
present, large (h 0.80 / 0.60 mm, stroke 0.200 / 0.150 mm) and well placed.

The defects I found are all in the **legend and paperwork layer**, not in the
copper or the geometry. None of them blocks the release.

---

## Findings

| # | finding | sev | image / page | disposition |
|---|---|---|---|---|
| F1 | `ANALOG SENSE (3V3_ANALOG)` board caption prints across `Q_SWDRVA` (SOT-23, `C8545`, **in the CPL**); **34.5 % of pad 3 (`SWG_A`) is silk ink**. It is 1 of the 49 `silk_over_copper` hits the board declares as a COUNT — and the only one on a reflow-assembled part | **P1** | `render_top_bare.png` @ (30.7, 84.1); my crop `z_analog.png` | **CARRY for v1.7, OWED for next silk revision.** JLC's DFM strips silk off mask openings, so the physical pad arrives clean and the caption arrives notched. Fix = move the caption ~2 mm south; silk-only, no copper/BOM/CPL. Add it to the §6 order-preview tick list in the meantime |
| F2 | `pdf/assembly.pdf` **cannot distinguish the 16 hand-fitted parts** from the 206 JLC-placed ones. MEASURED: **no footprint on this board is DNP** (`IsDNP()` true for 0 of 243), so no plot, drawing or 3D view can mark them. All 12 relays + `J_PI` + `J_TC` + `J_ISOLOOP` + `J_LOADCELL` are drawn identically to placed parts, with no hatch, no note block and no legend | **P1** | `pdf/assembly.pdf` p.1 | **CARRY.** §4 of `ORDER_README.md` states the 16 exhaustively with a substitution column, and §3's CPL row states the BOM⊅CPL asymmetry and says explicitly *"do not 'fix' it"*. Paper covers it; the DRAWING does not. Recommend a `not_assembled` annotation pass on the assembly plot for v1.8 |
| F3 | `pdf/schematic.pdf` is **unattributable**: zero occurrences of `cooksense`, `SMC0985` or `v1.7` in its text; no sheet frame, no title block, no revision, no date. One 900 × 450 pt sheet for 239 components, auto-placed, with net-label boxes overprinting pin-name text (e.g. across `U_EXP`, `U_ONESHOT`, `J_PI`) | **P1** | `pdf/schematic.pdf` | **CARRY, declared.** `policy_audit` row **S6 = HUMAN, "schematic readability graded in render review"** — this is that grading, and the answer is: legible only at ≥600 dpi zoom, traceable only with effort, and **identifiable as this board only by its net names.** Not order-blocking. Owed: a title block, minimum |
| F4 | **`J_ESTOP` carries no pin-function and no bridge legend in copper or silk.** MEASURED pads: 1=`GND`, 2=`3V3`, 3=`ESTOP_RAW_IN`. The plug must bridge **2–3**; a **1–2** bridge is a bolted short of the main 3V3 rail (pad 2's net is literally `3V3`, no series element). Silk within 8 mm of `J_ESTOP`: refdes only. Nearest board-level caption is `NOT SELV` at **8.637 mm** — and it belongs to `J_ISOLOOP` | **P1** | `render_top_bare.png` @ (196.6, 70.9); my crop `z_estop.png` | **CARRY for v1.7.** `policy_audit` **P-SILK-FN** flagged `J_ESTOP` by name and was WAIVED on "the designator IS the functional label" — true for *identity*, silent on the *2–3 vs 1–2* decision the plug forces. The paper mitigation is the strongest in the archive (see "What the paperwork gets right"). Owed: a `2-3` token beside the connector at the next silk revision |
| F5 | `1C2L3L4E` — the 30 V **NOT-SELV** pole legend — sits **0.085 mm** from `J_ISOLOOP` and **0.161 mm** from `J_RH_EXHAUST` (a 5-pin SELV sensor header). Both text baselines are `y = 101.000` with the four south-edge connector refdes (`J_THERM_A` 28.0, `J_THERM_B` 50.0, `J_RH_AMBIENT` 172.0, `J_RH_EXHAUST` 182.0, token 189.1), same 0.60 mm height. On the fabricated board the south edge reads `… J_RH_AMBIENT   J_RH_EXHAUST   1C2L3L4E` on one line | P2 | `render_top_bare.png` SE; my crop `z_isoloop.png` | **CARRY.** The `P-SILK-OWN` waiver states this exact defect was fixed and that the token *"reports DOES NOT FIT … instead of being printed on the wrong part"* — **it is printed, at the same 0.161 mm the waiver cites as the defect.** The gate's nearest-wins rule is satisfied by **76 µm**, which is not a human-perceptible ownership. The information is carried correctly and self-identified by the north caption, so the risk is confusion, not mis-wiring. Owed: move the token inside the `J_ISOLOOP` silk box, or delete it |
| F6 | The 12 relay silk body outlines print on **all 48 of their own THT pads**, 8.2–9.1 % of each pad (MEASURED on `K_U1`/`K_U2`: pads 1–4 at 8.2/9.0/9.1/9.1 %). Cause is structural: `Relay_StandexDIP_1A_pinout13` draws a 6.50 mm-wide body against pad columns at ±3.810 mm with 1.50 mm pads | P2 | `render_top_bare.png`, relay row; `z_relay.png` | **ACCEPT.** These are the hand-soldered relays; an iron burns through silk. 48 of the declared 49 `silk_over_copper` hits are this |
| F7 | `pdf/pcb_layers.pdf`: **`Title:` and `Rev:` are EMPTY on all 11 pages** (MEASURED via `pdftotext` on each page). Only page 5 (F.Silkscreen) identifies the board, and only because the board's own silk says `cooksense SMC0985KS sidecar v1.7`. `pdf/assembly.pdf` has the same empty title block on both pages | P2 | `pdf/pcb_layers.pdf` 1–11, `pdf/assembly.pdf` 1–2 | **CARRY.** No order exposure (gerbers carry their own filenames and the zip is hashed), but 10 printed copper plots that cannot name their own revision is a real hazard in a repo whose whole discipline is not confusing revisions |
| F8 | 4 refdes are **not on silk**: `R_MODEPD`, `R_REF4`, `R_SER2`, `R_SER3`. `policy_audit` reports `P-SILK-REF PASS — all refdes on visible silk` | P2 | board data | **ACCEPT — declared, not hidden.** MEASURED: `04_kicad/refdes_waiver.json` contains exactly `["R_MODEPD","R_REF4","R_SER2","R_SER3"]`, so the PASS is a waived PASS. Measured totals: 235 of 243 refdes visible on `F.Silkscreen`; the other 4 are `H1`–`H4`, covered by four `NYLON HW` captions |
| F9 | Silk clipped by the board edge: `J_MODE`'s outline reaches x = **200.120** (edge 200.050, **+0.070 mm**) and `J_ISOLOOP`'s keepout box reaches y = **102.075** (edge 102.050, **+0.025 mm**); 6 items total. Footprint bounding boxes overhang by 0.425 mm (`J_MODE`, east) and 0.275 mm (`J_ISOLOOP`, south) | P2 | `render_top_bare.png` E/SE edges | **ACCEPT.** Sub-0.1 mm silk, clipped at fab. No **copper** overhang: `placement_gates.txt` measures tightest pad-to-outline **0.62 mm at `J_ESTOP.MP`** against a 0.15 mm floor. The two body overhangs are the intended side-entry mating faces |
| F10 | `ORDER_README.md` §0-T and §7b — the two things that changed on 2026-07-30 and voided every prior verdict — are **not findable from the first screen.** MEASURED: lines 1–300 contain **zero** occurrences of `65 °C`, `ambient`, `bench` or `ADR-0029`. First mention of `§7b` is line **505**, of `§0-T` line **579**. There is **no table of contents** in 2837 lines, and the first screen's own change summary is *re-gate **3*** (ADR-0026/0027), which predates the change under review | P2 | `ORDER_README.md` | **FIX (cheap, doc-only).** Once findable, both are excellent — see below. One banner line at the top plus a TOC closes it |
| F11 | `ORDER_README.md` §13 — the section that tells a buyer *"judge the silk visually … before ordering"* — says the nine DRC checks *"remain off for **v1.3**"* and titles its gap list *"NOT fixed in **v1.3**"*, in a v1.7 document | P2 | `ORDER_README.md` §13 (L2308, L2332) | **FIX (doc-only).** Stale revision token in the one section that hands silk grading to a human |
| F12 | 15 refdes across 13 LCSC codes carry **single-channel rotation evidence** and an undischarged obligation: *"EACH MUST PASS THE JLC ORDER-PREVIEW HUMAN GATE BEFORE THE FIRST ORDER."* Separately, `jlc_twin` marks 4 parts **POLARITY-FIT-BLIND** (`D_COILEN`, `D_KSTOP`, `D_REVCLAMP`, `D_TVS`) — no usable polarity marking on one side, so only the human gate stands between them and a 180° flip | P2 | `verification/rotation_human_gate.txt`, `twin_overlay.md` §"36 flagged" | **CARRY as an ORDER-DAY condition.** `ORDER_README.md` §6 exists precisely for this and is a per-row tick list. It cannot be discharged before order day, so it does not change the design verdict |
| F13 | `jlc_twin` flags `J_PI` **MIRRORED** (mirror fit 0.00 mm vs non-mirror 2.54 mm) | P2 | `twin_overlay.md` | **NO ACTION — closed by measurement.** `J_PI` is off the CPL (hand-soldered THT), so JLC never places it. I re-derived the numbering against the real Pi 40-pin header: pad 3 = `I2C_SDA`, 5 = `I2C_SCL`, 6/9/14/20/25/30 = `GND`, 1/2/4/17 unconnected — an exact match to Pi pinout. The flag is about JLC's 3D model, not our numbering. Pad 1 is rectangular (pin-1 convention) |

---

## The four things I checked hardest, with the measurements

### 1. Does the board TELL a technician about the `J_ESTOP` plug? — **No, and that is F4**

MEASURED from `source/cooksense.kicad_pcb` (this archive's own copy, read-only):

```
J_ESTOP  C160403  JST_SH_SM03B-SRSS-TB_1x03-1MP_P1.00mm_Horizontal
         pos (196.60, 70.88) rot 90, F.Cu
  pad 1  net=GND            (194.60, 71.88)
  pad 2  net=3V3            (194.60, 70.88)
  pad 3  net=ESTOP_RAW_IN   (194.60, 69.88)
  pad MP net=GND  x2
```

So the paperwork's claim is exactly right and I re-derived it independently:
**2–3 bridges `3V3` to `ESTOP_RAW_IN` (asserts `ESTOP_OK`); 1–2 bridges `3V3`
straight to `GND`.** Pad 2's net is the raw rail — no series element, no fuse, no
FET. The only limit is the AMS1117's own protection.

What the board carries at that connector, measured exhaustively:

- the refdes `J_ESTOP`, h 0.60 / stroke 0.150 mm, rotated 90°, at (198.60, 76.38);
- the stock JST pin-1 tick — a 0.99 mm silk stub at y = 72.44, 0.56 mm beyond
  pad 1 on the far side from pad 2. **So the board says which end is circuit 1
  and says nothing else.**
- nearest board-level caption: `NOT SELV` at **8.637 mm**, `ISO 30V` at
  **9.401 mm** — both `J_ISOLOOP`'s.

By contrast `J_ISOLOOP`, whose plug is *not* user-crimped and *cannot* be
mis-mated (3.50 mm screw terminal, square pad 1), carries a 96-character
board-top caption **and** an adjacent `1C2L3L4E` pole legend. The board proves it
knows how to say this; it says it for the connector that needs it less.

This is the same finding `policy_audit`'s **P-SILK-FN** raised — it names
`J_ESTOP` in its failing list — and the waiver's answer ("this board's designator
IS the functional label") answers a different question. `J_ESTOP` tells you *what
the connector is*. Nothing on the board tells you *which two circuits to join*.

I am not calling it P0 because the failure is **loud and non-destructive**: a 1–2
plug leaves `ESTOP_RAW_IN` floating (`R_ESTOPPD` 470 Ω to GND), so `ESTOP_OK`
goes LOW and the board is inert *and* the LDO is in current limit — nothing
works, conspicuously. And because the paper mitigation is the loudest object in
the archive (below).

### 2. Silk on solderable copper — the count is declared, the classification is not

The DRC in this archive has **nine checks in `ignored_checks`**, four of them
silk: `silk_overlap`, `silk_over_copper` ("Silkscreen clipped by solder mask"),
`silk_edge_clearance`, `text_thickness`. §13 of `ORDER_README.md` declares this
and publishes the counts it gets with them re-enabled: **`silk_over_copper` 49**,
`text_thickness` 24, `silk_edge_clearance` 3, `silk_overlap` 2.

**49 is a count. Classified, it is two unrelated things and only one of them
matters** (canon: violations are CLASSIFIED, never counted):

| class | n | population | consequence |
|---|---|---|---|
| relay body outline over its own THT pads | 48 pads / 12 refs | **hand-soldered**, off the CPL | none — iron burns through silk (**F6**) |
| `ANALOG SENSE (3V3_ANALOG)` over `Q_SWDRVA` | 1 ref, 2 pads | **`C8545` SOT-23, in the CPL, reflow-placed** | pad 3 (`SWG_A`) is **34.5 % ink** (**F1**) |

Method, stated because the first one misled me: `pcbnew`'s
`TransformShapeToPolygon` on a `PCB_TEXT` returns per-glyph boxes, not strokes,
and inflated my first pass to a false "100 %". I re-measured from
`render_top_bare.png` **pixels** — classifying pale-yellow silk vs magenta pad
inside each pad's known bounding box, at 15.949 px/mm calibrated against the
`J_PI` pad array. That method reports **0.0 %** for the 16 pads of `U_ADC` and
both pads of `R_CLMPA` (it can return zero), **34.5 %** for `Q_SWDRVA` pad 3, and
**8.2–9.1 %** for the relay pads. The caption's own bbox is x[27.974, 44.026],
y[83.283, 84.717]; `Q_SWDRVA` sits at (30.700, 84.100) — the caption runs
straight over the part, and you can see the letters `A N A L O G` crossing its
pads in the render.

### 3. Are the twelve relays orientable by hand? — **Yes, checked and clean**

The 12 relays alternate `rot=180 / 0` down the row so that contact columns pair
across the milled slots (the silk says `(contact columns face pockets)`), which
means half of them are installed "upside down" relative to their neighbours. That
is the kind of thing that gets a hand-assembly wrong, so I measured every one:

- all 12 carry a filled 0.3 mm silk pin-1 dot;
- MEASURED offset dot−pad1 is **(−0.79, −4.12) mm for every `rot=0` relay** and
  **(+0.79, +4.12) mm for every `rot=180` relay** — i.e. the dot tracks the
  rotation correctly on all twelve, no exceptions;
- pad 1 is rectangular, pads 2–4 round;
- the dot marks the DIP-14 **package** pin-1 corner (there is no pad there), which
  is the right marker for a technician aligning the part's own notch.

The footprint's own description also reconciles: pads 1/2 = DIP2/DIP6 (coil, west
column), pads 3/4 = DIP8/DIP14 (contacts, east column), 7.62 mm between columns.
No finding.

### 4. Twin-render coverage — read the coverage line, not the verdict

```
COVERAGE: 52 measured / 208 refs with an expected body
          (156 unresolvable, 0 resolvable but NOT measured, 0 with no JLC model at all)
calibration 15.2259 / 15.2117 px/mm, anisotropy 1.0009 — orthographic, projection valid
bodies mounted 206/206 (missing_models.txt: "none — every CPL designator resolves a 3D body")
```

**25 % pixel coverage, and every one of the 156 gaps is NAMED with its reason** —
each is a body under the 2.0 mm resolvability floor (0402s at 7.6 px, SOD-323s at
19.8 px). That is honest and structural, not a hole in the evidence. Critically,
the graded 52 are **11 connectors, 44 IC-class, 21 diodes, 18 transistors, `F1`
and `CE1`** — *no connector and no polarised or many-pin part is in the
unmeasured set.* Worst centre delta among the connectors is `J_KEY_MATRIX` at
0.948 mm (tolerance 1.00 mm), with 0.000 mm outward excursion — a model-shape
disagreement with no board exposure, since gerbers and CPL derive from pads.

A note the brief asked for: the twelve empty relay outlines and the empty `J_PI`,
`J_TC`, `J_ISOLOOP`, `J_LOADCELL` footprints in `twin_top.png` / `twin_iso_se.png`
are **NOT "not placed"**. They are the 16 self-supplied refs; the CPL is
population truth and contains 206 rows, none of them these.

---

## `ORDER_README.md` as a document a human must use

**What it gets right, and it is unusual.** The first thing on the first screen,
before anything else, is:

```
# ⚠️⚠️ THE BOARD DOES NOT FUNCTION WITHOUT THE `J_ESTOP` SHORTING PLUG. ⚠️⚠️
# ⚠️⚠️ THE PLUG BRIDGES CIRCUITS 2–3. NEVER 1–2. ⚠️⚠️
```

followed immediately by the sourcing blocker with its section pointer, then
`v1.7 IS NOT SEALED. THIS IS A CANDIDATE, NOT A RELEASE`, then *"There is still
no orderable cooksense board."* **The first screen is honest and unambiguous
about what blocks an order.** It also carries a recorded correction — an earlier
version of the 1–2 warning said it shorted "a sensor rail behind an AO3401A" and
the file says out loud that this was wrong *in the reassuring direction*. That is
exactly the right way to move a hazard statement.

§4 lists all 16 self-supplied refs exhaustively with a substitute column and
calls the shorting plug *"the one self-supplied item whose absence is
indistinguishable from a dead board."* §3 pre-empts the BOM/CPL asymmetry a JLC
order desk will raise: *"A CPL row with no matching BOM line is a real defect:
stop. The REVERSE is expected and must NOT stop the order."* I verified that
asymmetry independently — BOM 222 designators / 61 rows, CPL 206, difference
exactly the 16 of §4, and **0 CPL rows without a BOM row.**

**§0-T (thermal envelope) — actionable: YES.** It states the declared 65 °C and
the 75 °C survive corner, the reason 65 was chosen over 75 (the BRIEF's own
`stop` rung; the board is thermally not dropout limited), a two-column margin
table at both ambients, the full `Tj` derivation from cited constants only, the
honest form carrying the board's other 0.958 W, and — the part most reviews
would omit — *"One thing in `power_tree.yaml` will look wrong and is not"*,
explaining why `pdiss_max_mw` is deliberately held at the 75 °C derating so that
narrowing a declaration cannot loosen a machine gate.

**§7b (mandatory bench gate) — actionable: YES.** Six measurements B1–B6, each
with the instrument, the method, and *what it retires and why no paper substitute
exists*. B3 is correctly marked as the one that dominates: the whole dropout
argument is a 1300 mV figure ds1117 publishes only at 0.8 A applied to a 0.2 A
rail. It says where to record the result (an ADR, raw numbers not conclusions)
and that a worse-than-assumed result is also an outcome.

**Findable: NO — that is F10.** Lines 1–300 contain no occurrence of `65 °C`,
`ambient`, `bench` or `ADR-0029`. The first cross-reference to `§7b` is line 505
and to `§0-T` line 579. There is no table of contents in 2837 lines. The change
under review — the one the brief says voided every prior verdict — is invisible
to a reader of the first screen, whose change summary is still re-gate 3's three
ADR-0026/0027 closures. Two lines of banner and a TOC fix it.

---

## Why no P0, and why the two verdicts differ

**`design_verdict: SOUND`.** Every finding above is in the legend or the
paperwork. Nothing I measured touches copper, geometry, netlist or population:
DRC 0/0/0 with `unconnected_items: []` and `schematic_parity: []`; tightest
pad-to-outline 0.62 mm against a 0.15 mm floor; A-POS worst CPL deviation
0.00050 mm; 0 courtyard findings; no copper overhang; relay pin-1 marking correct
on all twelve; connector pinouts re-derived and correct (`J_ESTOP` against
ADR-0025, `J_PI` against the real Pi header). The heaviest finding, F1, is one
SOT-23 pad under silk that JLC's DFM strips.

**`order_verdict: BLOCKED-SOURCING`.** One BOM line cannot be bought:
`C265111` (JST `SM08B-GHS-TB`, `J_THERM_A`/`J_THERM_B`) reads stock 5 with
**minPurchaseNum 21** (INHERITED — measured 2026-07-30 by the archive, not
re-measured by me; my brief supplied it). 21 exceeds the stock, so the line is
unbuyable at any quantity today. This is a **sourcing** fact and I have kept it
out of the design verdict entirely. Two further order-day conditions exist and
are correctly scheduled rather than blocking: §6's per-row JLC order-preview
human gate (F12, 15 refdes with single-channel rotation evidence plus 4
POLARITY-FIT-BLIND parts), and §3a's open DFM query on the 0.850 mm web at `H4`.
Neither can be discharged before order day. The archive's own header also
declares v1.7 NOT SEALED — a process state, not a design defect, and not the
basis of my verdict.

## Owed, in priority order (all doc/silk, no copper)

1. Move the `ANALOG SENSE (3V3_ANALOG)` caption clear of `Q_SWDRVA` (F1).
2. Add a `2-3` bridge token beside `J_ESTOP` in silk (F4).
3. Move or delete `1C2L3L4E`; a 76 µm ownership margin is not an ownership
   test, and the waiver's prose says it was not printed (F5).
4. First-screen banner + TOC for §0-T / §7b; fix the two `v1.3` tokens in §13
   (F10, F11).
5. Title/Rev in the KiCad page settings so the 11 layer plots, both assembly
   sheets and the schematic can name themselves (F3, F7).
6. Annotate the 16 not-assembled refs on the assembly plot (F2).

---

```
design_verdict: SOUND
order_verdict:  BLOCKED-SOURCING
```
