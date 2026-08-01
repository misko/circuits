# ADR-0007 — Check the fact where it ENTERS, and make the claim executable

Status: accepted, 2026-07-29
Supersedes: nothing. **Extends ADR-0004** (gate integrity) and ADR-0005 (imported
facts). Read those first — this ADR deliberately adds no principle they already
state.

## Context

On 2026-07-28 the `cooksense` v1.7 pre-seal review battery found a defect that
had shipped in **six sealed releases**: the 12 reed relays' land carried 4 pads
on a part whose datasheet figure shows 8 leads with two pairs internally tied.
`5V_KEY_RELAY` was hard-shorted to the select bus, every ULN2803 output was
shorted to its keypad line, and the coil had no holes at all.

Nothing internal could see it. The netlist, the board, the BOM and the manifest
all agreed — they descended from one wrong fact in `part.yaml` and were
consistently wrong together. That is the D1 reverse-polarity failure mode again,
which ADR-0004's own context already names.

In the same session, five further findings shared one of exactly two causes.

### Cause 1 — a wrong fact entered upstream and every artifact agreed with it

- the relay pin map (read off the wrong datasheet sub-figure)
- `usb-hub-3s-v3` J5's land, taken from KiCad's library and never compared to
  the vendor drawing — **0.375 mm** off on the pad-row-to-alignment datum,
  confirmed against two vendor sheets AND JLC's own package

Both are invisible to consistency checking by construction. Only an EXTERNAL
authority — the datasheet figure — can break the tie. In this pipeline that
authority is the fresh-context PIN REVIEW, and the skill schedules it in
**stage 7, pre-seal**: after placement, routing and a full gate battery are paid
for.

### Cause 2 — a claim was written but never converted into a check

| the claim | where it lived | what checked it |
|---|---|---|
| "the divider gives a valid logic high at U_EXP.1" | a code comment | nothing |
| "the isolation boundary runs between the rows" | ADR-0002 | nothing |
| "P-SILK-FN grades connector silk" | the gate's own NAME | nothing (1 of 35 refs) |
| "the SE corner is saturated, nearest site 33.6 mm" | a prior session's measurement | nothing — it did not reproduce, a legal site sat 6.46 mm away |

The `U_EXP.1` case is the sharpest. `electrical_invariants.yaml` asserted that
the divider RESISTORS EXIST, at the right values, and passed **136/136** — while
the node it was written to guarantee sat at **0.833 V against a 2.640 V
threshold**, i.e. the fault readback was dead. The assertion described the
MECHANISM. Nobody asserted the OUTCOME.

### Why the existing canon did not prevent any of it

It should have. The principles are already on the books:

- **M-WIDTH** (ADR-0004): *"a rule is written at the width of its class, not its
  incident… the rule MUST name the category and enumerate its known members."*
  ADR-0020 identified the MCP23017 contention mechanism, computed the remedy,
  and applied it to **one of six** port-B pins. M-WIDTH was live and unenforced.
- **ADR-0004 shift-left**: *"part dossiers get executable facts."* Stated as an
  aspiration. **No dossier in the fleet carries V_IH, V_OL, R_on or an
  open-drain flag**, so no gate can compute a logic level.
- **M-COVER / the G- family**: yet FOUR gates this session reported green while
  grading almost nothing — `P-SILK-FN` 1 of 35, `count_parity` grading a
  different board entirely, `P-ADJ` 51% ungraded fleet-wide, `jlc_twin`
  translation-invariant by construction and therefore blind to a land-datum
  error it reported `fit=0.00mm` on.

**This ADR adds one new principle and makes three existing ones executable.**
That is the whole decision. A principle that is not machine-checked is a claim,
and this ADR is about claims.

## Decision

> **M-ENTRY — Check a fact where it ENTERS the pipeline, not where it SHOWS.**
> A fact imported from outside the repo (a pin map, a land pattern, a threshold,
> a rating) MUST be checked against its external authority at the stage it is
> first WRITTEN DOWN, not at the stage its consequences become visible. A check
> that runs downstream of the artifacts derived from the fact cannot distinguish
> "correct" from "consistently wrong".

### 1. A `node_level` invariant kind — assert the OUTCOME, not the mechanism

New assertion kind in `03_src/rules/electrical_invariants.yaml`:

```yaml
- kind: node_level
  net: EFUSE_FLT_DIV
  receiver: U_EXP.1          # the pin whose thresholds decide the verdict
  driver_state: released     # or: asserted / driven_high / driven_low
  must_be: logic_high
  adr: 0022
```

The checker resolves the DC network around the net — pull-ups and pull-downs,
series elements, open-drain vs push-pull, source and sink impedance — from the
netlist plus a new `electrical:` block in `02_parts/*/part.yaml`, and grades the
resulting level against the RECEIVER's `v_ih_min` / `v_il_max`.

This single kind covers three of the session's findings with one mechanism:

| finding | what node_level computes |
|---|---|
| `U_EXP.1` divider dead | 5.0 × 22/132 = **0.833 V** vs V_IH 2.640 → FAIL |
| five MCP23017 pins win contention | 233–50 Ω source vs 82.5 Ω sink → **0.863–2.055 V** vs V_IL 0.8 → FAIL |
| reed coil pull-in margin at 70 °C | coil R, V_CE(sat), tempco → margin < 0 → FAIL |

It lives inside `electrical_invariants.yaml` deliberately: intent already lives
there, so E-ADR coverage and the RED-verification discipline come for free, and
no new tool has to earn its own G-family contract.

### 2. `02_parts` dossiers carry the electrical facts the check needs

Discharging ADR-0004's own shift-left item. New optional block:

```yaml
electrical:
  pins:
    "8":  {drive: open_drain, i_ol_ma: 4.0, v_ol_max: 0.33}
    "1":  {kind: input, v_ih_min_frac_vdd: 0.8, v_il_max_frac_vdd: 0.2}
  defaults: {drive: push_pull, r_on_ohm_max: 82.5}
```

Populated on DEMAND — a part needs it only when a `node_level` assertion names
it. No fleet-wide back-fill; the denominator is reported, per M-COVER.

### 3. The PIN REVIEW moves to the SCHEMATIC gate, and becomes incremental

The highest-yield lens in the pipeline runs last. It found the relay defect that
six sealed releases, three other lenses and every machine gate missed.

It ran late for a cost reason (54 datasheet reads), so the fix is to the cost,
not the placement: each dossier's `verified:` block gains the **sha256 of the
datasheet file and the figure/page it cites**, and the review re-reads only
dossiers whose hash or citation changed. Unchanged parts carry their prior
verdict forward with its provenance. That is the campaign's own "pay once"
principle applied to the one lens that most needed it.

Stage 7 keeps a pin review, scoped per canon "Verification scoping" to parts
whose dossier changed since the schematic gate.

### 4. M-WIDTH becomes machine-checked, via `class_sweep:`

An ADR that fixes a defect MUST enumerate its class:

```yaml
class_sweep:
  defect_class: "MCP23017 port-B readback pin sharing a net with a push-pull driver"
  members: [GPB0, GPB1, GPB2, GPB3, GPB4, GPB5, GPB6, GPB7]
  covered:  [GPB7]
  excluded: {GPB6: "TC_FAULT_N, not a safety term", GPB0: "see ADR-0022"}
```

`electrical_invariants.py --adr-coverage` fails an ADR whose `members` are not
each either `covered` or `excluded` with a reason. ADR-0020's gap — five pins
silently outside the fix — becomes visible **on the page, at authoring time**.

### 5. Config self-consistency

`fab_tiers.yaml` declares `min_silk_text_height: 0.45` AND `min_silk_stroke:
0.15`, while KiCad clamps stroke to ≤ 0.25 × height. **0.45 mm text can never
reach a 0.15 mm stroke.** Two floors that cannot both be met, and the board that
tripped it shipped six safety designators below the floor.

A cross-field consistency check on the rule files themselves, run by
`tests/run_tests.sh`. Cheap, and it catches self-contradiction anywhere in the
config rather than only this instance — M-WIDTH applied to this ADR's own fix.

### 6. The board-silk threshold is a regenerated bound

The first hand derivation said 0.60 mm text reaches JLC's published 0.15 mm
stroke. That used KiCad's upper clamp and omitted the board-silk emitter's
actual lower rule. The generator emits
`max(tier floor, 0.13, 0.16 × height)` before the KiCad clamp, so the first
height that reaches 0.15 mm is 0.9375 mm. This declaration deliberately names
the board-silk emitter; the refdes emitter has a different rule and threshold.

<!-- bound: BOARD_SILK_PUBLISHED_STROKE_HEIGHT -->
```yaml
id: BOARD_SILK_PUBLISHED_STROKE_HEIGHT
claim: >-
  Minimum board-silk text height at which the exact generator emitter reaches
  JLC's published 0.15 mm stroke. The command loads the generator's own
  silk_stroke function through G-SELFCON's AST reader and reads the published
  stroke and tier floor from fab_tiers.yaml; it does not restate the formula.
relation: ">="
value: 0.9375
unit: mm
corner: nominal
command: >-
  /usr/bin/python3 -c "import sys,yaml;sys.path.insert(0,'skills/kicad-pcb/scripts');from gate_contract_audit import load_stroke_model;f,n=load_stroke_model();d=yaml.safe_load(open('skills/kicad-pcb/references/fab_tiers.yaml'))['tiers']['jlc_2layer_default'];print(round(float(d['published_silk_stroke'])/n['SILK_STROKE_OVER_SIZE'],4))"
governs:
  evaluate: >-
    /usr/bin/python3 -c "import sys,yaml;sys.path.insert(0,'skills/kicad-pcb/scripts');from gate_contract_audit import load_stroke_model;f,n=load_stroke_model();d=yaml.safe_load(open('skills/kicad-pcb/references/fab_tiers.yaml'))['tiers']['jlc_2layer_default'];print(f({value},float(d['min_silk_stroke'])))"
  budget: ">= 0.15"
  unit: mm stroke
standard_value:
  explicit: [0.95, 1.00, 1.20]
  series_why: >-
    Text height is an authored board dimension, not an E-series component.
    These are the practical caption heights used by this pipeline at and above
    the threshold; 0.95 mm is the smallest available authored value that
    clears the regenerated 0.9375 mm minimum.
chosen: 0.95
chosen_why: >-
  The smallest practical board-caption height above the threshold. At 0.95 mm
  the exact emitter produces a 0.152 mm stroke, clearing the published floor.
grade: CITED
requires:
  - skills/kicad-pcb/scripts/gate_contract_audit.py
  - skills/kicad-pcb/scripts/generate_board_generic.py
  - skills/kicad-pcb/references/fab_tiers.yaml
```

## Consequences

**What this would have caught before a track was laid:** the relay pin map, the
J5 land, the `U_EXP.1` divider, the five MCP pins, the coil margin, and the four
gate-blindness defects. Four of the six v1.7 blockers.

**What it would NOT have caught:** the two silk findings (`J_ESTOP`/`J_DOOR`
label ownership, `J_ISOLOOP` artwork). Those need geometry and stay at stage
5-7. Recording that plainly, because a proposal that claims to catch everything
is the kind of claim this ADR exists to make executable.

**Cost:** items 4 and 5 are small. Item 2 is schema plus on-demand population.
Item 1 is a real checker with known-bad fixtures. Item 3 is a scheduling change
plus a hash cache.

**Risk, named:** `node_level` computes a DC operating point from datasheet
corner values. It is not SPICE and must not be read as one — it grades whether a
level is GUARANTEED by the published limits, which is the question the three
findings above turned on. Where a part publishes no limit, the check reports
UNREACHED rather than assuming one, per M-COVER.
