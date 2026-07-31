subject: pluto-rx2-8way-v2 v1.0 STAGED (06_build/staging/), git f6ec7ae4
date: 2026-07-31
reviewer: redteam-agent (Opus 5, lens 2 of 4 — manufacturability & orderability)
context-given: full-tree
verdict: DO-NOT-ORDER

> FILENAME NOTE. `08_reviews/contracts.md` allows `<date>_<subject>_<source>_<lens>.md`;
> this file is named `fab_manufacturability_audit.md` because the commissioning brief
> mandated a distinct basename (identical basenames shadow each other, which is how a
> family of reviews came to be graded by nothing). The REQUIRED header block above is
> present. The naming tension is reported, not silently resolved.

---

# Lens 2 — manufacturability and orderability

**One sentence: the copper is right and I can show it; the ORDER PAPERWORK is not,
and the board cannot be ordered from the tree as staged.**

Every number below is marked **MEASURED** (I ran it this session), **DERIVED** (I
computed it from a measured number), or **INHERITED** (I read it and did not
re-measure). Gates were run UNPIPED and the raw exit code read directly.

---

## VERDICT

| question | answer |
|---|---|
| Is the board's copper manufacturable at the declared tier? | **YES** — measured, with margin on every floor |
| Does any part exceed the D-TIER cost ceiling? | **NO** — 1 part at the ceiling, 5 below it |
| Is the BOM semantically correct (R30 class)? | **YES** — 11/11 verified against the LIVE catalog today |
| Is the CPL correct? | **YES** — 27/27 rows re-derived from the board |
| **Is this board ORDERABLE as built?** | **NO** — 3 blocking findings, all in the order paperwork |

The design gates are not what fails here. What fails is the set of documents a
human uses to *place* the order: the ADVANCED small-via option, the
impedance-controlled stackup, and the through-hole assembly line are all
**required by the copper and named nowhere in the ORDER_README**. Ordered at
JLCPCB's 4-layer defaults, this drill set is not buildable and every RF port
arrives loose.

---

## BLOCKING FINDINGS

### F1 (BLOCKING) — ORDER_README names no fab OPTION; the copper requires three

**MEASURED.** `grep -niE "thickness|1\.6|ENIG|HASL|surface finish|copper weight|impedance|stackup|advanced|option|JLC0416"` over
`06_build/staging/ORDER_README.md` returns exactly **two** lines, and only one is
substantive:

```
4:fab tier `jlc_4layer_advanced` (forced by PE42482A-X's QFN-24 escape).
130:## HUMAN GATES OWED BEFORE THE FIRST ORDER — both are A-POL, neither is optional
```

That is the tier's *name*. It is not an instruction to anyone at the order form.

**The exact line that is missing is already written down, twice.**
`03_src/rules/nets.yaml:36-41` carries it verbatim as a comment:

```
# ORDER_README line (exact):
#   "ADVANCED option REQUIRED: min via 0.25/0.15 mm (PE42482A-X QFN-24 at
#    0.50 mm pitch - at the standard-tier 0.30 mm drill the adjacent-pin
#    hole-to-hole gap is 0.50 - 0.30 = 0.20 mm against a 0.50 mm floor, so no
#    escape via fits). 4-layer JLC04161H-7628, IMPEDANCE CONTROL REQUESTED."
```

and `skills/kicad-pcb/references/fab_tiers.yaml:130` carries it as the tier's own
`order_readme:` field. `skills/pcb-design/SKILL.md:480` makes putting it in the
ORDER_README a *requirement* of the D-TIER decision.

**Why no gate caught it — MEASURED.** `grep -rn "order_readme" skills/` returns
three matches: the three `order_readme:` values in `fab_tiers.yaml` itself, plus
one prose sentence in `SKILL.md`. **No script reads the field.** There is no gate
here at all — not a green one that cannot see its subject, an absent one.

**What it costs, measured on the copper (`pcbnew`, staged board):**

| property | measured | jlc_4layer_standard floor | jlc_4layer_advanced floor |
|---|---|---|---|
| via diameter / drill | **0.2500 / 0.1500 mm** — all **3446** vias, one size | 0.45 / 0.30 | 0.25 / 0.15 (**exact**) |
| via annular ring | **0.0500 mm** | — | 0.05 (**exact**) |
| min hole-to-hole (edge-to-edge, all 3500 drilled features) | **0.3016 mm** (a fence via ↔ `J_ANT3.3`) | 0.50 | 0.25 |
| min track width | 0.2000 mm (152 of 199 segments) | 0.127 | 0.09 |

The drill file confirms it independently: `pluto_rx2_8way_v2-PTH.drl` declares
`T1C0.150` and `T2C1.400`, 3496 hits total. Ordered on JLC's default 4-layer
process the entire `T1` tool — 3446 of 3496 holes — is below the process minimum,
and the minimum hole spacing is 40 % under the standard floor.

**The impedance half is worse, because it is silent rather than loud.** A too-small
drill gets the order queried. A substituted laminate does not: the board builds,
looks perfect, and every one of the nine RF arms is detuned. `nets.yaml` derives
RF50 = 0.36 mm ⇒ 51.25 Ω *for* `JLC04161H-7628` (0.2104 mm top prepreg, Dk 4.4);
the whole published deliverable is a degrees-per-millimetre phase table on that
laminate. **MEASURED: the staged `.kicad_pcb` carries NO `(stackup ...)` block at
all** (`grep -n "stackup" source/pluto_rx2_8way_v2.kicad_pcb` → no match; the
`(setup ...)` block goes straight from `pad_to_mask_clearance` to `tenting`).
So *nothing in the shipped archive* — not the board file, not the ORDER_README,
not the MANIFEST — states which laminate this board is solved for.

**This is a regression, not a fleet norm.** Two sealed siblings do it correctly:

- `crow-recorder-central-v2-v1.7/ORDER_README.md:303-307` — a fab-options table with
  **Stackup** (`JLC06161H-3313` (1.6 mm) — REQUIRED …), **Via/process tier**
  (`ADVANCED small-via option REQUIRED` or JLC rejects the drill set),
  **Impedance control**, **Surface finish**.
- `cooksense-v1.7/ORDER_README.md:1057` — "Via tier | **ADVANCED small-via option
  required** — 0.25 mm via / 0.15 mm drill … Do NOT order standard 0.45/0.30."

**FIX:** add the verbatim `nets.yaml:36-41` line plus a fab-options table
(stackup, thickness, copper weight, surface finish, impedance control) before the
MANIFEST is finalised. This is a text edit to a staged file; after seal it is a
superseding version.

---

### F2 (BLOCKING) — the through-hole assembly gate is missing from the document that declares itself its home

`03_src/rules/assembly.yaml` contains a long, careful, *correct* `through_hole:`
block: ten `KH-SMA-KE-Z` jacks, **50 plated joints, F.Paste on none of them**, kept
ON the CPL because a live JLC assembly-catalog read found `C504007` with
`componentSpecificationEn: "Plugin"` (JLC's own word for through-hole) and 23,169
in stock. It then states, in its own words:

> "Selecting through-hole assembly is therefore an ORDER-TIME HUMAN GATE and it is
> on the FIRST SCREEN of ORDER_README, beside the rotation gate."

**MEASURED — it is not.** `grep -niE "through.hole|through hole|plug.?in|THT|C504007|surcharge|economic"`
over `06_build/staging/ORDER_README.md` → **RAW EXIT 1, zero matches.** The
README's `## HUMAN GATES OWED BEFORE THE FIRST ORDER` section lists exactly three
gates — `C5121458` rotation, `C2286` polarity, F-ECHO — and none is this one. (The
section header also says "**both** are A-POL" above a list of three.)

I independently confirmed the geometry from the staged board: **50 PTH pads at
1.400 mm drill** (10 refs × 5), NPTH only the four 3.2 mm mounting holes, and the
CPL carries all ten jacks as `top` placements. So the file uploaded to the
assembly step asks JLC to place ten parts that no reflow profile solders.

`02_parts/KH-SMA-KE-Z/part.yaml` (INHERITED) prices the consequence: "THT: this
part DISQUALIFIES the board from JLC Economic PCBA and adds a per-order THT
surcharge (~$3.50 setup + ~$0.0173/joint + $3.00 extended-component fee) … ~$0.87/board
of joint fee alone". None of that reaches the order paperwork either.

**Failure mode if this ships as staged:** the order goes in on the standard SMT
flow; JLC either drops the ten lines or the boards arrive with every RF port
loose — on a board whose entire product is ten RF ports. That is the exact
sentence `assembly.yaml` wrote itself to prevent.

**Second half of the same finding — the citation dangles. MEASURED:**
`assembly.yaml` cites two evidence files by path for the through-hole decision:

```
Raw record saved to verification/jlc_catalog_C504007.json.
… cross-checked by verification/stock_check.csv (pkg=Plugin, OK at 10 vs 23169)
```

`find projects/pluto-rx2-8way-v2 -name jlc_catalog_C504007.json -o -name stock_check.csv`
→ **empty**. Neither file exists anywhere in the project. The posture that keeps
ten RF ports on the CPL rests on a live read whose raw record is not in the tree.

(I re-ran the catalog myself — see the CLEARED section — and the claim is *true*:
`C504007` is `Plugin`, `expand`, stock 22,708 today. The finding is that the
release cannot show its own work.)

---

### F3 (BLOCKING) — the release fails its own contract on 10 artifacts, and two of them switch the sourcing gate off

**MEASURED, RAW EXIT 1:**

```
$ /usr/bin/python3 skills/kicad-pcb/scripts/release_required_check.py \
      projects/pluto-rx2-8way-v2/06_build/staging \
      --contract projects/pluto-rx2-8way-v2/07_releases/contracts.md
  MISSING required artifact: fab/bom.csv
  MISSING required artifact: fab/cpl.csv
  MISSING required artifact: verification/erc.json
  MISSING required artifact: verification/audit.txt
  MISSING required artifact: verification/bom_echo_gate.txt
  MISSING required artifact: verification/pin_review.md
  MISSING required artifact: verification/render_review.md
  MISSING required artifact: verification/redteam_topology.md
  MISSING required artifact: verification/redteam_layout.md
  MISSING required artifact: verification/parity.md
A-EVID FAIL: 10 required artifact(s) missing, 0 contract line(s) unparsed, 23 present
```

The board's own `07_releases/contracts.md:92-93` requires `fab/bom.csv` and
`fab/cpl.csv`. The staged tree ships only `bom_jlc.csv` / `cpl_jlc.csv`. Both
sealed siblings ship the contract names (cooksense v1.7 ships *both* pairs;
central-v2 v1.7 ships `bom.csv` + `cpl.csv`).

**The consequence is not cosmetic. MEASURED, RAW EXIT 1:**

```
$ /usr/bin/python3 skills/jlcpcb-fab/scripts/release_freshness_check.py \
      projects/pluto-rx2-8way-v2/06_build/staging
  note: A-STOCK: this release ships no fab/bom.csv + fab/cpl.csv pair — no coded, placed line to grade
  note: A-BUY: sourcing UNGRADED (no fab/bom.csv + fab/cpl.csv) — 0 line(s) measured, so no declaration is graded either way
  …
DESIGN: FAIL (2 finding(s))
SOURCING: UNGRADED
FRESHNESS: FAIL (2 finding(s))
```

**A-STOCK and A-BUY — the two checks that answer "is this orderable" — grade ZERO
lines, and they say so as a `note`, not a failure.** That is this session's
recurring class in its purest form: a gate that is honest, internally consistent,
and structurally unable to see its subject. `SOURCING: UNGRADED` is precisely the
question this lens was commissioned to answer.

**PROVEN BY CONSTRUCTION (RED → GREEN).** I copied the staging tree, added nothing
but two filename aliases, and changed no other byte:

```
cp staging/fab/bom_jlc.csv probe/fab/bom.csv
cp staging/fab/cpl_jlc.csv probe/fab/cpl.csv
$ release_freshness_check.py probe                       # RAW EXIT 1
  note: A-STOCK: grading verification/stock_check.json (11 graded line(s), verdict=PASS)
        against 11 coded+placed BOM line(s) x 5 boards
  note: A-BUY: measured SOURCING: CLEAR over 11 coded+placed line(s)
SOURCING: CLEAR
```

The filename **is** the cause: 0 lines graded → 11 lines graded, `UNGRADED` →
`CLEAR`, from two `cp`s. The two `DESIGN: FAIL` findings (see F5) survive.

That probe also surfaced a second, smaller blindness worth recording:
`note: A-STOCK: no assembly.yaml build_quantity — grading against the 5-board default`
— but `03_src/rules/assembly.yaml` **does** declare `build_quantity: 5`. The gate
did not resolve it from this path. The number is right **by coincidence** (the
declared value equals the default); a board declaring 50 would be graded at 5.

**Timing matters here.** The MANIFEST is bijective with the staging tree (62↔62 /
63↔63, per the handoff — INHERITED). Adding the two files changes the MANIFEST.
So this must be fixed *before* the MANIFEST is finalised, i.e. before seal —
after seal it is a superseding version.

---

## NON-BLOCKING FINDINGS (measured, recorded)

### N1 — the ten port captions LOST stroke between v1 and v2, on exactly the class canon names

**MEASURED**, both boards, straight from `pcbnew`:

| board | ANT1…ANT8 / RX1 / RX2 caption | height | stroke | vs JLC published 0.15 |
|---|---|---|---|---|
| `pluto-rx2-8way` (v1) | 10 items | **0.9500 mm** | **0.1520 mm** | **meets it** |
| `pluto-rx2-8way-v2` (this board) | 10 items | **0.9000 mm** | **0.1440 mm** | **below it** |

`fab_tiers.yaml` carries `published_stroke_min_height: 0.9375` for every tier —
the first height at which the generator's `0.16 × h` rule reaches JLC's published
0.15 mm stroke — and its header says in terms:

> "That threshold is the rule for anything a human reads under stress: connector
> and safety designators, polarity marks, terminal legends."

Ten identical SMA jacks in a ring is the canonical "which one am I plugging into"
problem, and these captions are the only thing that answers it. v1 cleared the
threshold; v2 sits 0.0375 mm under it. **The field exists to make this checkable
and nothing reads it** (`published_stroke_min_height` appears only in
`fab_tiers.yaml` itself).

Also measured, and NOT a v1→v2 regression (v1 has the same condition at
`J_ANT4`/`J_ANT5`): three refdes sit on the 0.45 mm / 0.1125 mm de-collision
fallback — **`J_ANT2`** (a connector), `R_LED`, `R_S4`. And the safety legends
`RX ONLY - NO TRANSMIT`, `PASSIVE ANT - 0 VDC MAX`, `U_MCU HAND-SOLDER ONLY`
print at 0.6000 / 0.1300 mm — legible, below published, unflagged anywhere.

None of this is a fab reject (0.45/0.1125 is the pipeline's proven-by-ordering
floor). It is a legibility risk on the one board in the fleet where legends are
the user interface.

### N2 — `verification/stock_check.csv` absent → F-MPN's in-archive authority is empty

**MEASURED.** `07_releases/contracts.md:150-165` marks `verification/stock_check.{txt,csv}`
REQUIRED and explains why the `.csv` specifically: it "is ALSO THE RELEASE'S OWN
code→MPN MAP … the ONLY MPN authority that lives INSIDE the archive", because
`02_parts/` and the passives ledger are outside the release and editable —
"cooksense v1.6 went FAIL, then PASS, on UNCHANGED sealed bytes inside one session
because the next revision's work removed and restored one dossier."

The staged tree has `stock_check.json` and `stock_check.txt`, **no `.csv`**. The
shipped `bom_legibility.txt` reports the hole in its own coverage line:

```
coverage F-MPN: 11/11 coded rows cross-checked against a HAND-VERIFIED authority;
  … (0 corroborated by the release's own sealed verification/stock_check.csv, …)
```

**0 of 11 corroborated from inside the archive.** The verdict is re-derivable only
from files outside it.

### N3 — two shipped evidence files grade a release directory that does not exist

**MEASURED.** `verification/bom_legibility.txt` and `verification/bom_source_check.txt`
both name `07_releases/v1.0-2026-07-30/fab/bom.csv`. `07_releases/` contains only
`contracts.md`. `release_freshness_check` calls both:

```
EVIDENCE PATH MISMATCH: verification/bom_legibility.txt names '07_releases/v1.0-2026-07-30/'
  but this release's directory is 'staging' (and no such sibling release exists)
EVIDENCE PATH MISMATCH: verification/bom_source_check.txt names '07_releases/v1.0-2026-07-30/'
```

These are the two `DESIGN: FAIL` findings. **Mechanism, measured from mtimes:**
the originals in `06_build/verify/` are dated **Jul 30 22:01**; the board was
regenerated **Jul 31 05:06**; `export_jlc_package` copied them into
`06_build/staging/verification/` at **Jul 31 05:08** without re-running them. They
are INHERITED evidence about a tree that no longer exists.

**I re-ran both against the staged BOM myself, UNPIPED:**

```
$ bom_source_check.py staging/fab/bom_jlc.csv 03_tscircuit/build/circuit.json --parts 02_parts
BOM SOURCE CHECK: PASS (every BOM LCSC == source)            RAW EXIT: 0
  coverage leg C: 7/7 R/C rows value-graded (11 BOM rows seen)
$ bom_legibility_check.py staging/fab/bom_jlc.csv --parts 02_parts
F-LEGIBLE OK: 13 check(s) passed                              RAW EXIT: 0
```

**So the conclusion survives and the shipped evidence does not grade the shipped
bytes.** Reported as the honest partial: the claim is true, its proof in the
archive is stale.

### N4 — the CPL's `Val` column is an LCSC code on 13 of 27 rows

**MEASURED.** `cpl_jlc.csv` carries `C504007` (×10), `C2286`, `C5121458`,
`C3716677` in `Val`, where `bom_jlc.csv` carries the human-readable
`KH-SMA-KE-Z` / `KT-0603R` / `PE42482A-X` / `BLM21SP601SN1D` for the same
designators. Canon F-WORDS ("the Comment column is a human-readable value, never
an LCSC code") grades the **BOM only**; the CPL is the file the placement
operator reads, and it is ungraded on this axis. The ADR-0006 measurement quoted
in `bom_legibility_check.py` — 470/1205 fleet BOM rows carrying a code where a
value belongs — is the same defect, one file over.

### N5 — `minPurchaseNum` is 779 on one line and nothing in the pipeline reads it

**MEASURED, live catalog 2026-07-31.** `C25744` (10 kΩ 0402, `R_PD1..R_PD4`,
20 pieces for a 5-board build) reports `minPurchaseNum: 779`. Every other line
reports `1`. `jlc_stock_check.py` keeps six fields (`code/type/stock/mpn/pkg/price`)
and `minPurchaseNum` is not among them. Cost only — a few cents — but it is an
order-form fact no gate surfaces.

Also measured on the same read: `lossNumber` is 10 on the seven basic passives
and 0 on the three extended/plug-in lines. Five of eleven lines are `expand`
(extended-part setup fee applies): `C137864`, `C137948`, `C3716677`, `C504007`,
`C5121458`.

### N6 — board thickness is declared nowhere, so the 0.15 mm drill's aspect ratio is unstated

**MEASURED / DERIVED.** No `(stackup ...)` in the `.kicad_pcb`, no thickness line
in the ORDER_README or MANIFEST. `nets.yaml` implies `JLC04161H-7628`, a 1.6 mm
stack. At 1.6 mm a 0.150 mm drill is a **10.67 : 1** plating aspect ratio
(DERIVED: 1.6 / 0.15). I am deliberately *not* asserting JLC's published limit
from memory — canon M6 says the fab's page governs at order time. The finding is
the **absence of the declaration**: nothing in the paperwork prompts anyone to
check the ratio against the capability page for 3446 holes.

### N7 — stock moved under the staged evidence

**MEASURED**, live re-query today vs the staged `stock_check.txt` (Jul 30 22:01):

| code | staged | today | Δ | needed (5 boards) |
|---|---|---|---|---|
| C25744 | 130,398 | **42,309** | **−67.6 %** | 20 |
| C137948 | 537,079 | 744,854 | +38.7 % | 5 |
| C504007 | 22,883 | 22,708 | −0.8 % | 50 |
| C5121458 | 1,294 | 1,284 | −0.8 % | 5 |

All 11 lines still clear the 5× floor; `PASS 11/11`, RAW EXIT 0. Recorded because
A-STOCK grades the world, and the world moved 67 % on one line in ten hours.
Thinnest headroom on the board: `C5121458` (PE42482A-X) at 1,284 — 256× the build.

---

## CLEARED — checked, measured, and nothing wrong

These are stated because a lens that reports only its findings hides its coverage.

**D-TIER cost ceiling — CLEAN.** `nets.yaml fab_tier: jlc_4layer_advanced`
(rank 2). Every `02_parts/*/part.yaml` `escape.tier_required`, read directly:

| part | tier_required | rank | vs ceiling |
|---|---|---|---|
| PE42482A-X | `jlc_4layer_advanced` | 2 | **at** the ceiling |
| 0402WGF2200TCE | `jlc_2layer_default` | 0 | under |
| BLM21SP601SN1D | `jlc_2layer_default` | 0 | under |
| KH-SMA-KE-Z | `jlc_2layer_default` | 0 | under |
| KT-0603R | `jlc_2layer_default` | 0 | under |
| RP2040-Zero | `jlc_2layer_default` | 0 | under |

**No part exceeds the ceiling.** `tier_preflight.py` — MEASURED, **RAW EXIT 0** —
`0 FAIL / 2 WARN`, both WARN being R-SCOPE clearance overrides (0.14 mm inside
`rf_launch` / `ctrl_escape`) that the gate explicitly defers to DRC.

**DRC configuration matches the tier exactly** (from `.kicad_pro`, MEASURED):
`min_track_width 0.09`, `min_via_diameter 0.25`, `min_through_hole_diameter 0.15`,
`min_via_annular_width 0.05`, `min_hole_to_hole 0.25`, `min_copper_edge_clearance 0.3`,
`min_text_height 0.45`, `min_text_thickness 0.1125`. Every one is the
`jlc_4layer_advanced` row of `fab_tiers.yaml`. A DRC 0/0/0 against this
configuration is a statement about the right floors.

**R30 semantic BOM — CLEAN, 11/11, verified against the LIVE catalog.** This is
the check the lens named, and the repo's own leg C is offline (MPN encoding →
`part.yaml` dir → passives ledger). I queried JLC's assembly catalog directly for
all eleven codes (canon M1: shares no line with any offline resolver), 2026-07-31:

| LCSC | BOM Comment | catalog MPN | catalog description (value) | pkg | agrees |
|---|---|---|---|---|---|
| C1525 | 100nF | CL05B104KO5NNNC | 100nF 16V X7R ±10% 0402 | 0402 | ✓ |
| C25744 | 10kΩ | 0402WGF1002TCE | 10kΩ 50V 62.5mW ±1% ±100ppm 0402 | 0402 | ✓ |
| C15849 | 1uF | CL10A105KB8NNNC | 1uF 50V X5R ±10% 0603 | 0603 | ✓ |
| C25091 | 220Ω | 0402WGF2200TCE | 220Ω 50V 62.5mW ±1% ±100ppm 0402 | 0402 | ✓ |
| C1779 | 4.7uF | CL21A475KAQNNNE | 25V 4.7uF X5R ±10% 0805 | 0805 | ✓ |
| C137864 | 47Ω | RC0402JR-0747RL | 47Ω 50V 62.5mW ±5% 0402 | 0402 | ✓ |
| C137948 | 680Ω | RC0402FR-07680RL | 680Ω 50V 62.5mW ±1% 0402 | 0402 | ✓ |
| C3716677 | BLM21SP601SN1D | BLM21SP601SN1D | 2.3A 600Ω@100MHz 60mΩ ±25% 0805 | 0805 | ✓ |
| C504007 | KH-SMA-KE-Z | KH-SMA-KE-Z | Coaxial Connectors (RF), SMA | **Plugin** | ✓ |
| C2286 | KT-0603R | KT-0603R | Red LED 1.8–2.4V 20mA 615–630nm 0603 | 0603 | ✓ |
| C5121458 | PE42482A-X | PE42482A-X | 10MHz–8GHz SP8T RF switch 2.3–5.5V | QFN-24 | ✓ |

Every catalog MPN equals the BOM MPN; every catalog description carries the
labelled value; every catalog package matches the footprint family;
`manufacturerBlackFlag` is `null` on all eleven (no lifecycle flag).
**The usb-hub v1.3 defect class — catalog 3.09k under a 100k label — does not
exist on this board.**

**CPL vs board — CLEAN, 27/27.** Re-derived every row from `pcbnew` (position,
rotation, layer, package), independent of `assembly_coverage.py`:
worst position error **≤ 0.0005 mm** against either the footprint origin or the
pad-array centre; rotation identical on all 27; layer `top` on all 27; package
string identical to the BOM on all 27; all 27 inside the Edge_Cuts bbox
(X 19.950–70.050, Y 19.950–93.050). The CPL frame matches the drill/gerber frame
(both emit Y negated — `NPTH.drl` `X23.8Y-23.8`, CPL `23.8,-23.8`).
Reverse direction: the 5 board footprints NOT on the CPL are exactly
`H1–H4` (attr 28 = exclude-pos + exclude-BOM + board-only) and `U_MCU` — the
declared `not_assembled` set, no more and no less.

**Silk over pads — ZERO, and this one nearly became a false finding.**
`F_Silkscreen.gto` contains **134 pad flashes** and `B_Silkscreen.gbo` contains
**54 flashes and no draws at all** — which reads as "print white ink on every pad,
including the QFN's 2.75 mm thermal pad and all 50 SMA barrels". It is not.
MEASURED: the polarity switches are at lines 11 (`%LPD`), 4964 (`%LPC`), 5197
(`%LPD`); all **4842 dark draws** precede the switch and all 134 flashes follow
it. They are **clear (knockout) apertures** — correct clip-silk-to-mask output.
`B_Silkscreen` is 54 knockouts on an empty layer, i.e. no bottom silk, which is
right for a `sides: [top]` build. **No ink lands on any pad.**

**F-PAYLOAD (the bytes that actually ship) — RAW EXIT 0.**
`fab_payload_census.py` on the staged tree: F-POUR 4/4 zone-bearing copper layers
carry real G36 regions (F.Cu 10, In1 1, In2 1, B.Cu 1); F-IDENT 4/4 copper
gerbers distinct. The usb-hub v1.6–v1.8 "no copper pour in any gerber" defect is
not present. Zip contents verified: 4 copper + 2 mask + 2 paste + 2 silk +
Edge_Cuts + PTH + NPTH = 13 files, all present.

**SMA through-hole fit — CLEAN, and it is the vendor's own number.** I checked the
1.400 mm holes against the 0.9 mm square posts before finding that `part.yaml`
had already done it: 0.9 mm square ⇒ 1.273 mm diagonal ⇒ **0.064 mm radial
clearance** at D1.4, and the dossier records that D1.3 would leave 0.014 mm,
"inside JLC's plated-hole tolerance". The 5-D1.4 pattern is the drawing's own PCB
inset, not a derived land. No finding.

**Mask dam — CLEAN.** Tightest aperture-to-aperture gap on the board is
**0.2000 mm** at `U_SW` pads 1↔2 (QFN-24, 0.5 mm pitch, `pad_to_mask_clearance 0`);
next is 0.3400 mm at `C_SW1`. Comfortable for any JLC mask process. Vias are
tented front and back (`(tenting (front yes) (back yes))`), so none of the 3446
0.15 mm holes opens a mask sliver or wicks solder.

**jlc_twin (independent vendor geometry) — RAW EXIT 0**, re-run with
`--adjudications` and `--cpl`: **26 OK, 0 CRITICAL**, bodies mounted 27/27,
`MODEL-REG-OK` (body on courtyard, 0.00 mm) on all 27. The `C2286` /
`ROT-DB-SUGGEST 180` line is present and is explicitly refuted by the recorded
adjudication, not silenced. The two A-POL human gates (`C5121458` rotation,
`C2286` polarity) are correctly carried in the ORDER_README.

**E-MARGIN 934 mV vs 1384 mV — NOT a contradiction; I chased it and it resolved.**
The staged `verification/policy_audit.md:41` says "headroom 934 mV" while
`ORDER_README.md:49` says "headroom 1384 mV vs 250 mV dropout". Re-ran
`power_topology.py` — **RAW EXIT 0** — and the same tool prints **both**:
`headroom 1384 mV (Vin_min 4.75 - Vout_max 3.366) vs dropout 250 mV` and the
brownout leg `headroom 934 mV (Vout_min 3.234 − load_UV 2.3)`. Two sub-checks,
two numbers, both true. The only defect is labelling: the README's row is titled
`E-TOPO / E-MARGIN` and carries the dropout number while the audit row under the
same ID carries the brownout number. Recorded, not a finding.

---

## COVERAGE — what this lens did NOT grade

Stated so the absence is a declaration, not silence.

- **I did not re-run DRC.** The 0/0/0 claim is INHERITED. I verified instead that
  the *rule set* DRC was run against is the correct tier (see CLEARED), which is
  the part a wrong answer would hide.
- **I did not open the PDFs.** `pdf/assembly.pdf`, `pdf/pcb_layers.pdf`,
  `pdf/schematic.pdf` are present and hashed; whether the assembly drawing is
  legible and current is the render lens's subject.
- **I did not verify JLC's published capability numbers against their live page.**
  Canon M6 says the page governs at order time. Every tier floor I compared
  against is `fab_tiers.yaml`'s recorded value, and `jlc_4layer_advanced`'s
  provenance ("usb-power-3s v1.0–v1.3 ordered with exactly this line") is
  INHERITED. The advanced-tier `min_hole_to_hole: 0.25` even carries "verify at
  order time" in its own comment, and this board's 0.3016 mm sits 0.0516 mm above
  it — the thinnest tier margin on the board.
- **F-ECHO is not runnable here** and is correctly carried as a human gate. Stock
  PASS is LCSC catalog stock; JLC's assembly uploader allocates from a different
  pool. A PASS is necessary and not sufficient — the uploader is the only
  instrument that answers "will it clear".

---

## WHAT WOULD MAKE THIS ORDERABLE

Four edits, none of which touches copper, all of which must land **before** the
MANIFEST is finalised:

1. **F1** — add the verbatim `nets.yaml:36-41` ADVANCED/stackup line plus a
   fab-options table (stackup `JLC04161H-7628`, thickness, copper weight, surface
   finish, impedance control) to `ORDER_README.md`. Model: central-v2 v1.7:303-307.
2. **F2** — add the through-hole assembly selection to the ORDER_README's first
   screen, beside the two A-POL gates, where `assembly.yaml` already says it is;
   and either ship `verification/jlc_catalog_C504007.json` or stop citing it.
3. **F3** — write `fab/bom.csv` and `fab/cpl.csv` (and the other 8 contract-required
   artifacts), then re-run `release_freshness_check` and confirm `SOURCING: CLEAR`
   rather than `UNGRADED`.
4. **N1/N2** — lift the ten port captions to ≥ 0.9375 mm (v1 shipped 0.95) and
   emit `verification/stock_check.csv` so F-MPN has an in-archive authority.

The copper is right. The paperwork is what stops the order.
