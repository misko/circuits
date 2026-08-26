# pluto-rx2-8way-v2 — schematic & netlist lens (round 3, independent)

    subject: pluto-rx2-8way-v2 @ 9af663f0 (unsealed; no release version yet)
    date: 2026-07-31
    reviewer: redteam-agent (Opus 5, schematic & netlist lens)
    context-given: full-tree
    verdict: ORDER

    design_verdict: SOUND
    order_verdict:  ORDER

- **Scope of those keys.** `order_verdict: ORDER` is stated **on this lens's
  evidence only** — schematic, netlist, parity, pin maps, ERC. Layout, RF,
  fab-manufacturability and sourcing are other lenses' remit and this lens
  asserts nothing about them.
- **Nothing in this lens is blocking.** One non-blocking rendered-ink finding
  (§7) and four observations (§8) are recorded.
- Branch `main` @ `9af663f0`; `projects/pluto-rx2-8way-v2/` clean against HEAD
  at the time of measurement. `04_kicad/` and `07_releases/` opened READ-ONLY;
  every generated artifact went to scratchpad.

## Verdict summary — the six things this lens was asked to settle

| # | Question | Answer | Grade |
|---|---|---|---|
| 1 | Do two different nets share ink? | **No.** 0 collinear overlaps, 0 dotless Ts, 0 crossings | MEASURED |
| 2 | Do the label plates point at the right pins? | **Yes. 0 wrong-way** of 46; 43 discriminated, 3 perpendicular | MEASURED |
| 3 | The 32-of-44 vs 4-of-44 reconciliation | **SETTLED by controlled experiment.** Both were right; they differ by *signal magnitude*, 7.6x | MEASURED |
| 4 | Schematic-parity, node level | **0** over 24 nets / 114 nodes, by a method sharing nothing with `--schematic-parity` | MEASURED |
| 5 | Pin maps against datasheet FIGURES | PE42482 **25/25 exact**; RP2040-Zero vendor numbering correct | MEASURED |
| 6 | ERC | **0 errors.** 213 warnings, all in 2 fully-explained benign classes | MEASURED |

**The round-2 defect is gone and I re-measured it rather than inheriting the
claim.** The previous sheet drew `SW_V3` and `SEL_V4` as one conductor
(4.4450 mm of shared ink, 6 endpoint-in-interior events, 0 junctions over 49
wires). On the sheet at `9af663f0`: **39 wires, 5 junctions, zero shared ink of
any kind.** All five junction dots sit on genuine 3-arm same-net Ts.

**One question nobody had answered on this board is now answered (§6):**
`sch_occlusion.py:182-184` records that this project's S-OCCL waiver was
withdrawn because *"nobody had checked whether the two files agreed"* — the
graded `.kicad_sch` versus the tscircuit render a human actually reads. **They
agree: 24/24 nets, node-level symdiff 0 over 114 nodes.**

---

## 0. Method, and why it is independent (canon M1)

Everything below comes from instruments written from scratch in scratchpad. **No
repo code was imported** — not `sch_occlusion.py`, not `policy_audit.py`, not
the converter. Specifically:

- `sx.py` — my own s-expression reader (quoted-vs-bare atoms distinguished).
- `model.py` — my own schematic connectivity model: union-find over a 0.1 µm
  integer lattice, my own junction/T/overlap rules, my own power-symbol rule.
- `svgink.py` — reads **rendered ink** out of KiCad's own SVG: the glyph
  strokes inside `<g class="stroked-text">` and the 6-vertex label plates.
  Strict sequential scan, so no regex spans one element into the next.
- `ink.py`, `occl.py`, `parity.py`, `tsc_parity.py`, `diffexp2.py`.

Exact integer geometry throughout (collinearity by integer cross-product), so
no float epsilon can manufacture or hide a finding.

**Instrument bugs I found in my own work and fixed before trusting a number** —
recorded because each would have produced a confident wrong answer:

1. My first pin-direction formula was **sign-inverted**, which reported *36 of
   46 labels wrong-way*. Caught by an independent cross-check (direction from
   the pin's connection point toward its symbol origin) and by deriving the
   convention from the file's own geometry: `SYM_U_SW` pin 2 is `(at -13.970 … 0)`
   with `(length 5.080)` and the body rectangle starts at `x=-8.890`;
   `-13.970 + 5.080 = -8.890` exactly ⇒ **library angle 0 means the pin line
   runs +x from the connection point INTO the body.** After the fix the
   cross-check agrees on **every** pin (0 failures).
2. My first SVG reader missed the one rotated label (its invisible `<text>` is
   wrapped in a `rotate()` group) and read only the first vertex of the plate
   polygons (implicit linetos). Both fixed; the corrected reader finds
   **46 plates for 46 labels** and all 3 `SW_V3` texts.
3. My first differential experiment's angle-rewrite **silently failed** on
   `180`/`90` — a null experiment that would have "confirmed" the canon claim
   while mutating nothing. Fixed, and every arm now asserts the mutation landed.

**A rotation caveat, stated because it bounds a claim I could otherwise
over-sell.** The symbol-rotation convention is *undiscriminated by this sheet*:
all 53 rotated symbol instances are GND power symbols whose single pin sits at
the library origin, so both rotation senses give byte-identical pin coordinates
(**measured: 0 of 191 pins differ**). My model is therefore correct here
regardless of the convention — but this sheet does not test it.

---

## 1. Netlist integrity — my model vs KiCad's own netlister

`kicad-cli sch export netlist` (raw exit **0**) versus my geometric model,
compared as a **partition** (set of node-sets, names ignored), so agreement
cannot come from copying names:

```
kicad-cli partition blocks : 40   nodes: 130
my-model  partition blocks : 40   nodes: 130
PARTITIONS IDENTICAL       : True
named nets where my node set differs : NONE
node-level symdiff over named nets   : 0  / 114 nodes over 24 nets
```

This is a strong result because my connectivity **rules** are mine: I treat a
dotless T as *not* connecting and collinear overlap as *not* connecting, and
only junctions and coincident endpoints as merging. Reproducing KiCad exactly
under those rules confirms both the rules and the sheet.

Population: 89 symbol instances, 39 wires, 5 junctions, 46 global labels,
16 `no_connect`.

## 2. Does any ink belong to two different nets?

Exact-integer census over all 39 wires:

| class | count | disposition |
|---|---|---|
| `COLLINEAR_OVERLAP` (two wires sharing ink) | **0** | the round-2 defect class — gone |
| `T_VISIBLE_DOTLESS` (3+ arms, no dot) | **0** | — |
| `T_VISIBLE_DOTTED` | **5** | all 3-arm, **all same-net** — correct |
| `COLLINEAR_SPLIT` (emitter artifact, invisible in render) | **0** | — |
| `PROPER_CROSSING` (interiors cross) | **0** | no two wires even cross |
| `LABEL_ON_WIRE_INTERIOR` | **0** | no silent taps |
| `PIN_ON_WIRE_INTERIOR` | **0** | — |
| points where ≥3 wire **endpoints** coincide | **0** | no undotted endpoint-Ts |

All 5 junctions carry exactly one net each (`3V3`, `SW_V4`, `RX1_MAIN`,
`SEL_V1`, `SW_V1`). **No dot sits at a different-net T**, so the corrected
canon (task #68 — a dot at a different-net T *creates* a short and is never the
remedy) is not violated anywhere on this sheet.

`no_connect`: 16 flags, each on exactly one otherwise-isolated pin, **0
anomalies**, matching the 16 `unconnected-(U_MCU-…)` nets one-for-one.

## 3. THE CENTRAL QUESTION — do the label plates point at the right pins?

Measured from **rendered ink** (the plate polygon KiCad actually draws), against
a conductor direction taken from wire/pin geometry — **a source completely
independent of the label's own `angle`/`justify`**, so this cannot be satisfied
by cancellation between two direction bugs (the failure mode of `948ef54d`,
where ~155 of 1504 were right only by cancellation).

```
plates matched 1:1 to labels by exact anchor coincidence : 46 / 46
glyph groups reused by more than one label               : 0

OK    plate points AWAY from its conductor  : 43
WRONG plate lies OVER its conductor         :  0
PERP  conductor orthogonal, test is silent  :  3
pin-direction independent cross-check failures : NONE
```

**0 wrong-way of 46.** The 3 perpendicular cases —
`SEL_V3@(73.66,156.21)`, `3V3_MOD@(127.00,149.22)`, `SW_V3@(81.92,130.81)` —
are L-corner attachments where the only conductor leaves orthogonal to the
label axis. The test is silent there **by construction, not by instrument
weakness**: there is no "away" to be on. I inspected the rotated one
(`SW_V3`, the sole angle-90 label) in the render at 400 dpi: its plate stands
vertically above R_PD3's pin tip, clear of the body and clear of the `R_PD3`
reference text.

Per canon (instance 20), a green S-OCCL is **not** evidence for any of this —
which is exactly why the conductor direction above comes from geometry, not
from the label fields.

## 4. RECONCILIATION — 32-of-44 vs 4-of-44, settled by experiment

Prior round: one lens said 32 of 44 labels were anti-parallel-discriminating by
a plate-polygon method; an independent instrument reading KiCad's invisible
`<text>` anchors discriminated 4 of 44. Both said 0 wrong-way. 8x apart.

An instrument discriminates a label iff its reading **changes when the field it
claims to read changes**. So I mutated the sheet in scratchpad, re-rendered with
KiCad, and measured which readings move. Every arm asserts the mutation landed.

```
MUTATION CONTROL: justify rewritten on 46 labels; angle rewritten on 46 labels

                    JUSTIFY flipped              ANGLE flipped
PLATE    flipped 46 / same  0 / unreadable 0   flipped  0 / same 46
GLYPH    flipped 46 / same  0 / unreadable 0   flipped  0 / same 46
ANCHOR   flipped 45 / same  1 / unreadable 0   flipped  0 / same 46

magnitude of the AXIS component in the as-built sheet (mm):
  plate   min 2.421   median 3.630   max 6.805
  glyph   min 2.300   median 3.540   max 6.745
  anchor  min 0.159   median 0.476   max 0.476
```

**The settlement — neither prior lens was fabricating.**

1. **All three readings do carry the sense.** The invisible-`<text>` anchor is
   not sense-blind: it flips on 45 of 46. So "4 of 44" was *not* measuring a
   property of the sheet.
2. **They differ 7.6x in signal magnitude** (median 3.630 mm vs 0.476 mm). The
   anchor offset is a *constant* ±0.476 mm — `Counter({-0.476: 31, +0.476: 14,
   0.159: 1})` — independent of name length, and **smaller than the 0.635 mm
   grid the sheet is authored on**. Any instrument applying a de-noising
   tolerance above ~0.48 mm — an entirely reasonable choice when comparing
   against grid coordinates — reads the anchor instrument as non-discriminating
   on nearly every label, while the plate reading sails past. That is the whole
   8x.
3. **The one genuine anchor failure** (`same 1`, the 0.159 mm outlier) is the
   single angle-90 label `SW_V3@(81.92,130.81)`: for a rotated label the
   anchor's axis component is the baseline residue, not the justify offset. The
   anchor instrument is *structurally* wrong on rotated labels; the ink
   instruments are not.
4. **The denominators also differ because the sheet changed.** 44 labels then,
   **46 now** — the sheet was regenerated at `0a021353` and `9af663f0` between
   the two rounds. Any 44-vs-46 comparison across rounds is not like-for-like.

**Recommendation (proposed, not applied): direction must be read from the plate
polygon or the glyph strokes, never from the invisible `<text>` anchor.** The
anchor's signal is sub-grid and structurally wrong on rotated labels.

### 4a. Canon independently confirmed, with a positive control

Flipping **every** label's angle to its opposite (0↔180, 90↔270) produced a
render that is **BYTE-IDENTICAL** to the base SVG. Positive control: the
justify flip changed 62,228 tokens in the same comparison.

> **MEASURED:** the `angle` field's sense component has *zero* rendering
> effect. **`justify` ALONE selects the sense.** This independently confirms
> the canon recorded at `sch_occlusion.py:29-32`.

## 5. Parity, DRC and ERC — raw exit codes, unpiped

```
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity
  Found 0 violations
  Found 0 unconnected items
  Found 0 schematic parity issues
  DRC_RAW_EXIT=0
```

**Both halves clean** — including the unconnected half, which is the one that
gets summarised instead of classified.

**Independent parity, not sharing a method with `--schematic-parity`:** my own
connectivity model of the `.kicad_sch` against the `.kicad_pcb` pad net
assignments read with my own parser (KiCad 10 uses `(net "NAME")` with no index):

```
schematic nets (named, with pins): 24   nodes: 114
pcb nets       (named, with pads): 40   nodes: 130
nets only in schematic : NONE
nets with IDENTICAL node sets: 24 / 24
NODE-LEVEL SYMDIFF: 0   over 24 nets / 114 nodes
```

The 16 extra PCB nets are the `unconnected-(U_MCU-…)` autonames for the 16
NC-flagged pins. Pads with no net: `H1`–`H4` (mounting holes, correct) and the
nine unnumbered `U_SW` pads — **verified `F.Paste`-only stencil sub-apertures**
over the exposed pad, not netless copper. **Pad 25 (the EP) is on `GND`.**

**ERC — 0 errors** (`--severity-error --exit-code-violations`, raw exit 0).
213 warnings, classified rather than counted, in exactly two classes, both benign:

- **89 × `lib_symbol_issues`** — one per symbol instance: *"the current
  configuration does not include the symbol library 'elt'"*. An environment
  artifact: every symbol definition is embedded inline in the file. Not a
  design defect.
- **124 × `endpoint_off_grid`** — pins/wire-ends off KiCad's *default* 50 mil
  connection grid. **Root cause measured: the sheet is authored on a
  consistent 0.635 mm (25 mil) grid — 474 of 474 coordinates land on it
  exactly, zero stragglers.** Connectivity is unaffected (KiCad matches exact
  coordinates), and parity is 0. *Consequence worth recording:* a future
  **hand**-edit in the KiCad GUI at the default 50 mil grid cannot snap to
  roughly half the connection points, so a hand-drawn wire would silently fail
  to connect. Set the grid to 25 mil before hand-editing this sheet.

## 6. Do the two schematic files agree? (previously unchecked on this board)

`sch_occlusion.py:177-184` declares the scope limit that matters most here: the
gate grades the `.kicad_sch`, while under ADR-0002 Phase A the artifact a human
reads is tscircuit's own render — *"and the reason it was withdrawn was that
nobody had checked whether the two files agreed."*

Checked. `03_tscircuit/build/circuit.json` is the exact circuit the human PDF is
drawn from; compared against my model of the KiCad sheet:

```
tscircuit nets: 24  nodes: 114
kicad     nets: 24  nodes: 114
nets only in tscircuit : NONE      nets only in kicad : NONE
nets with IDENTICAL node sets: 24 / 24
NODE-LEVEL SYMDIFF: 0  over 24 nets / 114 nodes
```

**The two files agree exactly.** Supporting facts, all MEASURED:

- **Freshness (round-1 P0-4) is genuinely fixed.** `schematic.pdf` 11:35:43.465
  post-dates `circuit.json` 11:35:42.504 by ~1 s; the `.kicad_sch` is
  11:35:43.581 — one driver run, correct order.
- **The pin-reversal half of P0-4 is fixed.** The human PDF now reads
  `1 GP0`, `21 3V3 → N3V3_MOD`, `23 5V` — matching the netlist. The earlier
  reversed map (pin 1 = 5V … pin 23 = GP0) is gone.
- **`build/circuit.json` and `dist/src/…/circuit.json` are byte-identical** —
  the stale-copy defect is fixed.
- The human PDF names the rails `N3V3`/`N3V3_MOD` where every downstream
  artifact says `3V3`/`3V3_MOD`. This is a **documented authoring alias**, not
  a discrepancy: tscircuit's `net.` selector cannot author a digit-leading name,
  and `03_tscircuit/net_aliases.txt` maps both explicitly rather than relying on
  the strip-guard-N convention. Recorded as an observation (§8d), not a finding.

## 7. FINDING (non-blocking) — 4 plate-over-pin-text overprints in rendered ink

Measured from the SVG, after removing KiCad's duplicate emissions (§8a):

| label plate | overprinted by | overlap |
|---|---|---|
| `ANT2` | U_SW pin-name `LS` | 0.545 × 1.333 mm |
| `SW_V4` | U_SW pin-name `RF5` | 0.545 × 1.694 mm |
| `SW_V3` | U_SW pin-name `RF5` | 0.545 × 0.688 mm |
| `SW_V4` | U_SW pin-number `13` | 1.000 × 0.127 mm |

Visible at 400 dpi and confirmed by eye. **Root cause:** in `SYM_U_SW`, pins 1
(`LS`) and 13 (`RF5`) are emitted at **angle 270 with `length 1.270`** while
every other pin is at angle 0/180 with `length 5.080`. Those two pins are
therefore drawn on the body's top and bottom edges with 90°-rotated name/number
text, which lands on the neighbouring global-label plates.

**Disposition — NOT blocking, and not a new hole.** This falls exactly inside
`sch_occlusion.py`'s **declared and fixtured** vacuity (lines 154-166): *"PIN
NAME and PIN NUMBER text is not placed, so this gate PASSES a sheet whose
pin-name text is completely covered by a label plate."* That docstring records
*"4 unreported ink-overlapping pairs on pluto-rx2-8way-v2"* — **my independent
from-scratch instrument measured exactly 4, and they persist on the current
post-regeneration sheet.** Connectivity is provably unaffected (§1, §5).

Severity note, stated because it is not zero: one of the two affected pins is
**`LS`**, and the part's own gotcha says a floating `LS` silently selects the
complemented half of the truth table (RF1↔RF8, RF2↔RF3, RF4↔RF7, RF5↔RF6) — a
board that gets it wrong still sweeps eight antennas in a plausible order. So
this is legibility damage on the one pin whose mis-reading is undetectable
downstream. **The pin is correctly grounded** (§5, §9); only its *label* is hard
to read.

**Proposed upward, NOT applied (a `skills/` change):** the symbol emitter should
not place a pin on a body edge perpendicular to its neighbours' fan when a
global label occupies the adjacent tip — or, more cheaply, `sch_occlusion.py`
could place pin-name/number text for the *rotated* case only, where the
position is unambiguous. Either is a skill change and belongs outside this
board's partition.

## 8. Observations (no action required)

**a. 238 of 570 glyph runs are KiCad emitting identical ink twice.** Every one
is the *same content at the same bounding box* — invisible overprint of ink on
itself. A naive occlusion instrument reports **238 phantom collisions**; after
deduplication there are **0 true glyph-vs-glyph collisions** on this sheet. Any
future ink-based checker must dedup by (content, box) first.

**b. 12 label-plate pairs "overlap" by 0.0008 mm.** Plates are 2.5408 mm tall on
a 2.54 mm row pitch, so vertically stacked plates share a 0.8 µm boundary.
Hairline adjacency, visually zero — adjacent plates render as a contiguous
stack sharing a border line. Not occlusion. Recorded so it is not miscounted as
12 defects later.

**c. 52 of 60 GND symbols are rotated** (28 at 90°, 24 at 270°, 1 at 180°, 7 at
0°), so ground renders as a *sideways arrowhead* in most places rather than the
conventional downward bar stack. Legibility only: the GND pin sits at the
symbol origin with `length 0`, so rotation cannot move the connection point —
which is also why the rotation convention is undiscriminated here (§0).

**d.** The human-read schematic labels the power rails `N3V3`/`N3V3_MOD`; every
downstream artifact says `3V3`/`3V3_MOD`. Documented alias, mapped explicitly in
`03_tscircuit/net_aliases.txt` (§6).

**e.** `RX1_TAP_MID` is declared in the `RF50` (50 Ω) netclass, but it is the
node *between two series 220 Ω resistors* — a high-impedance interconnect, not a
50 Ω line. Harmless (width is width, and fan-consistent width is reasonable),
but the class name overstates what that node is. Flagged for the RF lens, which
owns the question.

## 9. Pin maps against datasheet FIGURES

**U_SW — PE42482A-X, QFN-24.** Every pad checked against `02_parts/PE42482A-X/
part.yaml`, which records a visual read of **Figure 22 'Pin Configuration (Top
View)', PDF p20, cross-checked pin-by-pin against Table 8**. Result: **25 of 25
exact**, no exceptions.

`1 LS→GND · 2 RF2→ANT2 · 3 GND · 4 RF3→ANT3 · 5 GND · 6 RF4→ANT4 · 7 GND ·
8 VDD→3V3 · 9 V1→SW_V1 · 10 V2→SW_V2 · 11 V3→SW_V3 · 12 V4→SW_V4 ·
13 RF5→ANT5 · 14 GND · 15 RF6→ANT6 · 16 GND · 17 RF7→ANT7 · 18 GND ·
19 RF8→RX1_TAP · 20 NC→GND · 21 GND · 22 RFC→RX2_OUT · 23 GND · 24 RF1→ANT1 ·
25 EP→GND`

Datasheet obligations, each MEASURED as satisfied:

- **`LS` tied to GND** (1 MΩ internal pull-up; floating selects the complemented
  truth table). Pad 1 is on `GND`, and the gotcha's *layout* obligation — "a
  SHORT via to the ground plane at the pad, not a trace to a distant net" — is
  met: nearest `GND` via is **0.418 mm** from the pad centre (second at
  0.450 mm), out of 3433 GND vias.
- **`NC` (pin 20) tied**, per Table 8 fn 2, rather than left as an open stub
  inside the RF fan.
- **EP on GND** — "ground for proper operation", the RF ground return for all
  nine ports.
- **V1–V4 external pull-downs MANDATORY** (no internal pull of any kind; a
  floating V4 with V1..V3 low is the all-ports-terminated state and would
  silently mute the receiver). Present: `R_PD1..R_PD4`, 10 kΩ each, on
  `SW_V1..SW_V4`. At 5 µA max input current the pull-down offset is ~50 µV.
- **Digital abs-max 3.6 V while VDD abs-max is 5.5 V.** Rail is 3.3 V — inside
  the digital limit; the board never presents 5 V logic.

**U_MCU — RP2040-Zero**, the part whose numbering was withdrawn and re-adopted
at `16c54169` (vendor walk is clockwise from top-right; `ours_n = 24 − vendor_n`
was the exact reversal). Verified on the released files: pads 1–16 → GP0–GP15,
then **pad 17 → GP26**, 18→GP27, 19→GP28, 20→GP29 — i.e. the divergence after
sixteen consecutive agreements is correctly represented, which is precisely the
trap the commit named. Pad 21 = `3V3` → `3V3_MOD`, pad 22 = `GND`, pad 23 = `5V`
(VBUS) left NC — correct under ADR-0002, which gives the board no power
connector of its own.

## 10. Every net reaching an RF port or a power rail

Full topology, from my model (24 named nets, 114 nodes):

- **RF star.** `RF1..RF7 → ANT1..ANT7 → J_ANT1..J_ANT7` (2 nodes each).
  `RFC(22) → RX2_OUT → J_RX2`. `RF8(19) → RX1_TAP → R_T2.2`.
- **The 8th throw is the RX1 pickoff, not an 8th antenna.** `RX1_MAIN` carries
  **three** nodes — `J_RX1.1`, `J_ANT8.1`, `R_T1.1` — so RX1 passes straight
  through from `J_RX1` to `J_ANT8`, and a 220 Ω + 220 Ω series tap
  (`R_T1 → RX1_TAP_MID → R_T2`) samples it into `RF8`. Coherent with the
  `RF50` class list in `nets.yaml`, which names exactly these eleven nets.
- **Truth table consistency.** The gotcha gives `RF_n` selected where
  `n−1 = 4·V1 + 2·V2 + 1·V3` (V1 MSB, V3 LSB, V4=0). With `RF1→ANT1 … RF7→ANT7,
  RF8→RX1_TAP`, the binary sweep order is monotonic ANT1→ANT7 then the RX1 tap.
  The board wires `V1←GP0 … V4←GP3`, so **firmware must treat GP0 as the MSB** —
  the gotcha warns that getting V1/V3 backwards silently reverses the sweep and
  nothing on the board can detect it. Wiring is self-consistent; the constraint
  is on firmware and is recorded here, not defective.
- **Power tree, two nets by construction.** `U_MCU.21(3V3) → 3V3_MOD →
  {C_BULK.1, FB_3V3.1(IN)}`; `FB_3V3.2(OUT) → 3V3 → {C_SW1.1, C_SW2.1,
  U_SW.8(VDD)}`. The ferrite is a **series** element, so each side is its own
  net — exactly as `nets.yaml` insists, and the v1 `VBUS_LDO` lesson is applied.
  Decoupling: 4.7 µF bulk module-side, 100 nF + 1 µF switch-side, against a
  120 µA typ / 200 µA max load.
- **Control path.** `U_MCU GP0..GP3 → SEL_V1..SEL_V4 → R_S1..R_S4 (47 Ω) →
  SW_V1..SW_V4 → U_SW V1..V4`, each with its 10 kΩ pull-down. **No shunt
  capacitance anywhere on the class**, as `nets.yaml` requires (a 1 k + 1 nF RC
  would be 4.6 µs, more than the entire 4.267 µs blanking allowance).
- **Status LED.** `GP4 → LED_STAT → R_LED(680 Ω) → LED_STAT_A → LED_ST.2(A)`;
  `LED_ST.1(K) → GND`. Polarity correct — anode to the ballast, cathode to
  ground, GPIO sourcing.
- **GND** — 60 nodes: all 10 SMA shells (4 each), all 11 U_SW ground/tie pads
  incl. the EP, `U_MCU.22`, the four pull-downs, three capacitors, LED cathode.

## 11. What this lens did NOT verify

Stated so the gap is a declaration, not an omission:

- **RF performance** — impedance, phase matching, stitching pitch, the tap's
  loading of `RX1_MAIN`. Netlist-correct is not RF-correct; §8e is flagged for
  that lens.
- **Layout/placement, silk, courtyards, keepouts** beyond the single `LS`
  ground-via measurement, which I took only because the datasheet makes it an
  electrical obligation.
- **Fab, assembly posture, sourcing and stock.** `order_verdict: ORDER` above is
  scoped to this lens and asserts nothing about `BLOCKED-SOURCING`, which is the
  fab/sourcing lens's call.
- **The symbol-rotation convention** — undiscriminated by this sheet (§0).

---

### Provenance

All numbers MEASURED on `9af663f0` unless tagged otherwise. Gates run unpiped
with raw exit codes reported. Instruments in scratchpad, none imported from the
repo. `04_kicad/` and `07_releases/` were opened read-only; the differential
experiment (§4) wrote its mutated sheets and renders to scratchpad only.
