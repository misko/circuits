subject: pluto-rx2-8way-v2 v1.0 (staged), board at git 9af663f0
date: 2026-07-31
reviewer: redteam-agent (Opus 5, fab-orderability lens — one of four independent lenses, fresh context)
context-given: full-tree
verdict: DO-NOT-ORDER

```
design_verdict: DEFECTIVE
order_verdict:  DO-NOT-ORDER
```

**THE TWO KEYS ARE HERE, AT LINE 8, ON PURPOSE.** `M-REV` parses only the first
`_REVIEW_HEADER_LINES = 40`; last round both lenses stated theirs at lines
211 and 77 and scored `REVIEW-NO-VERDICT` — a true refusal with a false reason.

**WHAT THE KEYS DO AND DO NOT SAY.** The copper is sound and I did not find a
defect that would make the board come back wrong. `DEFECTIVE` is about the
ARCHIVE'S MANUFACTURABILITY CASE, and it rests on one measurement no gate in
this repo takes: **the archive's stated hole-to-hole margin is a NOMINAL margin,
and JLC's own published pad-hole tolerance (+0.13/−0.08 mm) consumes 126 % of
it on 8 sites** (§3). `DO-NOT-ORDER` follows from four unresolved order-time
items, none of them sourcing. **`BLOCKED-SOURCING` would be FALSE and I am
saying so explicitly**: A-BUY measures `SOURCING: CLEAR` over 11/11 lines and I
re-measured every one live on two independent channels (§5). M-REV forbids
BLOCKED-SOURCING when every coded, placed line clears its build quantity.

**SCORE ON THE FIVE THINGS I WAS SENT TO CHECK — all MEASURED, all RAW:**

| # | question | answer |
|---|---|---|
| 1 | fab tier / §0 prose vs the board | every geometric claim in §0 verifies EXACTLY (§2). Its *premise* does not (§4) |
| 2 | THT assembly + §2a's cited evidence | both files REAL with `_provenance`; JLC's own page confirms Thru-hole placement is a SELECTABLE option (§6) |
| 3 | BOM/CPL denominators | **11 graded, not zero** — A-STOCK 11/11, A-BUY 11/11, F-LEGIBLE 11/11, A-POP 27/27 (§5, §7) |
| 4 | M-BOM semantic, R30 precedent | **11/11 catalog value == schematic label, 11/11 catalog MPN == BOM MPN. No R30-shaped defect** (§5) |
| 5 | fleet `(stackup` = 0/34, impedance order | verified 0/34 sealed AND 0/442 project boards. Does NOT block the order (§8) |

**THE ONE FINDING THAT IS NEW.** §3. Nobody has classified this board's
hole-to-hole population by PAIR CLASS. Done here: the 3446-via fence is *not*
the tight class — **54 of the 57 sub-0.45 mm pairs are a stitching via against
an SMA jack's own ground barrel, on all ten launches**, and JLC publishes no
floor for that mixed class at all.

---

## 0. Method, and what I did not do

Every number below is MEASURED by me from the artifact named, with `pcbnew`,
the vendor's API, or a vendor product-page read — never from the archive's
prose, and never from a search snippet (`Q-SNIPPET`). Gates were run UNPIPED
with `echo $?` read directly. `04_kicad/` and `07_releases/` were opened
read-only; `07_releases/` holds only its `contracts.md` — **this board has never
sealed**, and the order package under review is `06_build/staging/`.

Claims are graded **MEASURED** (I ran it), **DERIVED** (arithmetic on measured
inputs), **INHERITED** (I am repeating the archive without re-measuring).
Nothing here is INHERITED except where it says so.

---

## 1. IS THE STAGED ORDER PACKAGE THE BOARD THAT IS IN `04_kicad/` TODAY?

I checked this first because HEAD (`9af663f0`) rewrote **14 852 lines** of
`04_kicad/pluto_rx2_8way_v2.kicad_pcb` *after* the staging tree was assembled,
and `06_build/staging/source/pluto_rx2_8way_v2.kicad_pcb` has a different md5.
A stale fab payload would end the review.

**IT IS NOT STALE. The two boards are the same board in every plotted
respect.** MEASURED, four independent comparisons:

| comparison | 04_kicad | staging/source | verdict |
|---|---|---|---|
| track segments (start/end/layer/width) | 199 | 199 | **0 only-in-A, 0 only-in-B** |
| vias (position + drill) | 3446 | 3446 | **0 only-in-A, 0 only-in-B** |
| footprints (ref/pos/rotation/layer) | 32 | 32 | **identical** |
| zones (net/layer/corner count) | 6 | 6 | **identical** |
| board-level drawings (class/layer/text/bbox) | 55 | 55 | **identical** |
| footprint graphics + Reference/Value fields | 527 | 527 | **identical** |

The 14 848-line diff is **UUID churn and S-expression token reordering**, which
is what a full `rebuild_all.sh` re-emission produces. Cross-checked from the
other end: `fab/pluto_rx2_8way_v2-PTH.drl` carries exactly **3446 hits on
T1 C0.150 and 50 hits on T2 C1.400** — the board's own via and PTH census to the
unit — and `NPTH.drl` carries 4 × T1 C3.200.

**A METHOD WARNING, so a later agent does not mistake my scratch work for a
finding.** I also re-exported gerbers from `04_kicad/` with `kicad-cli` and got
`DIFFERS` on 8 of 11 layers. That is **entirely my plot options, not the
board**: the pipeline's exporter plots drill marks (KiCad `SMALL_DRILL` =
0.35 mm, clamped; vias plot at their true 0.15 mm) and my invocation did not.
Resolved by aperture function, the staged copper carries `C,0.150000 × 3446` +
`C,0.350000 × 54` with no `AperFunction` attribute — drill marks — under a
single `%LPD*%` (DARK) block, so they are **redundant positive flashes inside
their own pads and remove no annular ring**. Every one of the 34 sealed fleet
releases carries the same 0.35 mm small-drill aperture. **FLEET NORM, proven by
ordering. Not a finding.**

**WHAT *IS* STALE IN THE STAGED ARCHIVE — and it is the schematic half only:**

| staged artifact | state |
|---|---|
| `source/*.kicad_sch` | md5 `dec79f06` = the sheet at commit `c0e21fa7`, **two commits back** |
| `pdf/schematic.pdf` | md5 `5b4731ef` vs the current `03_tscircuit/build/schematic.pdf` `4430aa8c` — **pre-fix render** |
| `verification/policy_audit.md` | reports **`S-OCCL FAIL, 13 occlusions`**; re-run today: **`S-OCCL PASS, 0`** (HEAD fixed it) |
| `MANIFEST.txt` `git_sha:` | `c0e21fa7`, i.e. HEAD~2 |
| `ORDER_README.md` §7 item 1 | describes the S-OCCL FAIL as open. It is closed. |
| `ORDER_README.md` §4 `policy_audit` row | says **FAIL=2**; re-run today, RAW EXIT 1: **FAIL=1** |

**No fab file is affected.** Gerbers, drills, BOM and CPL are a correct export
of the board that is in `04_kicad/` right now. But the archive ships a
schematic that is not its board's schematic and an audit that misreports its
own board — `M-SHIP` says grade the shipped bytes, and the shipped bytes here
disagree with the tree in the archive's own `source/`. **That is a re-stage, not
a redesign**, and it is the cheapest item on this page.

---

## 2. §0's GEOMETRY — EVERY NUMBER VERIFIES EXACTLY

MEASURED with `pcbnew` off `04_kicad/pluto_rx2_8way_v2.kicad_pcb`. I am
reporting agreement as carefully as I would report a discrepancy, because §0 is
the part of the document a fab order cannot be placed without.

| §0 claim | my measurement | |
|---|---|---|
| 3446 vias, **every one** 0.2500 mm pad / 0.1500 mm drill | 3446 vias, **one geometry class**: `(0.2500, 0.1500) × 3446` | ✓ |
| 50 PTH pads at 1.400 mm across 10 refs | 50 PTH, **one drill class** `(1.4, 1.4)`, refs `J_ANT1…J_ANT8, J_RX1, J_RX2` | ✓ |
| 4 NPTH at 3.200 mm | 4 NPTH `(3.2, 3.2)`, refs `H1…H4` | ✓ |
| 3496 plated / 3500 total holes | 3496 plated / 3500 total | ✓ |
| **3446 of 3496 plated holes under 0.30 mm** | 3446 | ✓ |
| min hole-to-hole **0.3016 mm**, "a via against `J_ANT3.3`" | **0.3016 mm**, 0.1500 via @ (29.4000, 63.8000) ↔ **`J_ANT3` pad 3, net GND, 1.400 mm drill** @ (29.2000, 62.7421) | ✓ **including the named pad** |
| 50.10 × 73.10 mm, 4 copper layers | 50.1000 × 73.1000 mm, `GetCopperLayerCount() = 4`, thickness 1.6000 mm | ✓ |
| no `(stackup` block | `grep -c '(stackup'` = **0** | ✓ |

**F.Paste on none of the 50 PTH pads — CONFIRMED, and it is exact.** Per-ref
paste census: all ten `J_*` refs read `Fpaste=0, pads=5, PTH=5, PTHpaste=0`.
`U_MCU` reads `Fpaste=0` over 23 pads and carries `EXCLUDE_FROM_POS_FILES`.
The CPL lists all ten jacks as `top`. **The §2a premise is real.**

**`U_SW`'s stencil is CORRECT, and I am reporting it because the raw count
reads alarming and is not.** The census says 33 paste apertures over 34 pads,
and the pad without paste is **pad 25 — the 2.750 × 2.750 mm GND exposed pad**,
which on an RF switch is the ground return. That is not a missing aperture: the
34 pads are **24 signal pins + the EP + 9 unnumbered paste-only sub-apertures**
(0.750 × 0.750 mm, `F.Paste` only — no copper, no mask) on a 3 × 3 grid at
±0.950 mm centred on the EP. It is the textbook windowpane pattern, and the
EP is deliberately excluded so the part does not float on a solid paste slug.
DERIVED coverage: 9 × 0.750² / 2.750² = **66.9 %**, inside IPC-7093's 50–80 %
band for a QFN thermal pad. **No finding.**

**Margin against the DECLARED tier** (`fab_tier: jlc_4layer_advanced`,
`03_src/rules/nets.yaml:30`), DERIVED from the measurements above against
`skills/kicad-pcb/references/fab_tiers.yaml`:

| parameter | board | advanced floor | margin |
|---|---|---|---|
| via pad diameter | 0.2500 | 0.25 | **0.0000 — AT THE FLOOR, ×3446** |
| via drill | 0.1500 | 0.15 | **0.0000 — AT THE FLOOR, ×3446** |
| hole-to-hole | 0.3016 | 0.25 | +0.0516 (+20.6 %) — **see §3** |
| min track width | 0.2000 | 0.09 | +0.1100 (2.22×) |
| min clearance (scoped DRU, `rf_launch` / `ctrl_escape`) | 0.1400 | 0.09 | +0.0500 (1.56×) |

The board sits **exactly on** the tier floor in both via dimensions, on its most
numerous feature by three orders of magnitude. That is by construction — the
generator emits the tier's floor — and JLC's advertised combination is
inclusive, so it is orderable. It is stated because a fab that reads its own
floor as exclusive rejects 3446 features at once, and nothing in the archive
says the margin there is zero.

**D-TIER — the cost ceiling — PASSES.** `tier_required` across `02_parts/`:
`PE42482A-X` → `jlc_4layer_advanced` (rank 2); `KH-SMA-KE-Z`, `KT-0603R`,
`BLM21SP601SN1D`, `0402WGF2200TCE`, `RP2040-Zero` → `jlc_2layer_default`
(rank 0). Max required rank 2 == declared rank 2. **No part exceeds the declared
tier.** Independently confirmed by `policy_audit`: `P-TIER | PASS | all parts
escape at declared fab_tier 'jlc_4layer_advanced'` and `P-ESC | PASS | 6 parts`.

---

## 3. **THE FINDING: the tight hole class is the RF LAUNCH, not the fence — and it is graded against a floor the vendor does not publish, without the vendor's own tolerance**

The archive states one hole-to-hole number, 0.3016 mm, against one floor,
0.25 mm, and reports +20.6 % margin. **CLASSIFY, NEVER COUNT.** Classified by
pair class over all 3500 holes (MEASURED, brute-force with a 4 mm spatial grid):

| pair class | pairs under 0.45 mm | minimum gap | tightest pair |
|---|---|---|---|
| **VIA ↔ PTH pad** | **54** | **0.3016 mm** | via ↔ `J_ANT3.3` |
| VIA ↔ VIA | **2** | 0.3785 mm | via ↔ via |
| VIA ↔ NPTH | **1** | 0.3768 mm | via ↔ `H4` |
| PTH ↔ PTH | 0 | 1.6934 mm | `J_RX2.5` ↔ `J_ANT8.3` |
| NPTH ↔ PTH | 0 | 3.8088 mm | `J_RX1.5` ↔ `H2` |

**55 of the 57 sub-0.45 mm pairs involve a COMPONENT hole. The 3446-via
stitching fence — the feature the archive spends §0 on — has a via-to-via
minimum of 0.3785 mm and only 2 pairs anywhere near the floor.** The tight
population is a stitching via placed against an SMA jack's own ground barrel,
and it is systematic: it recurs on **all ten launches** — `J_ANT1` through
`J_ANT8`, `J_RX1`, `J_RX2` — which makes it launch geometry, not a router
accident.

**Why the class matters: JLC publishes a DIFFERENT floor for each class, and
NOTHING for the mixed one.** Read live 2026-07-31 from
`jlcpcb.com/capabilities/pcb-capabilities`: **via spacing "0.2 mm"**, **pad
spacing "0.45 mm"**. Every one of the 55 mixed pairs sits *between* those two
numbers. I went looking for the mixed rule and it does not exist: JLC's
`difference-and-tolerance-explanation-between-via-and-pad-holes` article
"does not specify minimum spacing rules between via holes and pad holes", and
their own public Q&A entry **#693 is a customer asking exactly this question and
is UNANSWERED** — *"the only rule that i can not find is what the minimum
distance is allowed between pad and hole."* The governing number for this
board's tightest feature class **is not published by the fab**.

**And the vendor DOES publish a tolerance that the archive never applies.** Same
JLC article, quoted: pad holes are **"controlled for diameter … with a tolerance
of +0.13mm/−0.08mm"**, while **"the diameter of via holes is not controlled."**
DERIVED, at max material condition on the pad hole alone:

```
  1.400 mm SMA barrel  +0.13  ->  1.530 mm       radius +0.065 mm
  0.3016  -  0.065     =  0.2366 mm  of wall remaining
```

| against | result |
|---|---|
| `fab_tiers.yaml` advanced `min_hole_to_hole: 0.25` | **SHORT by 0.0134 mm** |
| JLC published **via** spacing 0.2 mm | clears by +0.0366 mm |
| JLC published **pad** spacing 0.45 mm | short by 0.2134 mm |

**8 of the 54 mixed pairs go under the declared tier's own 0.25 mm floor once
the vendor's published pad-hole tolerance is applied** (nominal gap < 0.315 mm):
0.3016 ×2, 0.3028, 0.3118, 0.3121 ×2, 0.3144 ×2. **The archive's +0.0516 mm
margin is nominal-only, and the vendor's own published tolerance consumes
126 % of it.** No gate in this repo — `policy_audit`, the DRU, `escape_check`,
`fence_pitch` — applies a vendor drill tolerance to a hole-to-hole gap.

**WHAT THIS IS AND IS NOT.** It is **not** proof the board is unmanufacturable:
against the authority canon M6 says governs at order time — JLC's published
page — the worst pair still clears the via floor by 0.0366 mm even at max
material. It **is** an unproven margin presented as a proven one, on 8 sites,
systematic across all ten of the board's ten deliverable ports, in the one
dimension where the board already has zero margin (§2). **This is a DFM question
to put to JLC in writing before the order, and it belongs beside §2a/§2b/§2c as
a fourth human gate**, not inside a table that reads as cleared.

---

## 4. §0's *PREMISE* — JLC's LIVE PUBLISHED PAGE DISAGREES WITH `fab_tiers.yaml`, AND CANON M6 SAYS THE PAGE WINS

§0 asserts, as its central claim: *"Ordered at JLC's standard 4-layer defaults
this board is unmanufacturable, and that is arithmetic, not caution … without
[the advanced option] the drill set is rejected."* That arithmetic is done
against `fab_tiers.yaml`'s `jlc_4layer_standard` row. **Read live 2026-07-31
from `jlcpcb.com/capabilities/pcb-capabilities`, that row does not match what
JLC publishes today:**

| parameter, 4-layer | `fab_tiers.yaml` `jlc_4layer_standard` | `fab_tiers.yaml` `jlc_4layer_advanced` | **JLC published, live 2026-07-31** |
|---|---|---|---|
| min via diameter | 0.45 | 0.25 | **"0.25 mm via diameter"** (default) |
| min via hole | 0.30 | 0.15 | **"0.15 mm hole size"** (default) |
| min track / space, 1 oz | 0.127 / 0.127 | 0.09 / 0.09 | **"0.09 / 0.09 mm (3.5 / 3.5 mil)"** |
| via spacing | 0.50 | 0.25 | **"0.2 mm"** |
| the paid option | — | "small via" | **"0.15mm hole size with *any size via diameter* … will cost more"** |

**JLC's published 4-layer DEFAULT is the repo's ADVANCED row.** The paid option
on the live page is for non-standard via *diameters*, not for reaching 0.15 mm
holes. `fab_tiers.yaml`'s own header states the rule: *"the fab's PUBLISHED
capability page overrides these numbers at order time"* (canon M6).

**Consequence, stated without exaggeration.** This does **not** endanger the
board — it is the safe direction, and the board is orderable either way; it is
the reason §0's geometry (§2) all verifies while its conclusion does not follow.
It **does** mean the ORDER_README's §0, whose entire job is telling a buyer
which options to purchase, instructs them to request and pay for an upgrade
JLC's page currently describes as standard. **D-TIER is explicitly a COST
CEILING**, and ordering above the fab's actual requirement is that ceiling
failing in the other direction. The escape-via argument in `nets.yaml:30-40`
(`PE42482A-X` QFN-24 at 0.50 mm pitch: 0.50 − 0.30 = 0.20 mm against a 0.50 mm
floor) is arithmetically correct **against the repo's file**; against the live
page the same part escapes at 0.50 − 0.15 = 0.35 mm against a 0.2 mm via floor
with no upgrade at all.

**I am not proposing an edit here** — `fab_tiers.yaml` is under `skills/`, and
my brief is propose-never-apply. Proposal in §9.

**Confidence note, stated because it changes what a reader should do with
this**: the capability numbers above come from a WebFetch summarisation of the
page, not from my own eyes on the HTML. I could not corroborate them on a second
JLC page (the two candidate help articles carry no numbers, one of them because
the question is unanswered). **Treat §4 as one channel.** Canon M6 already makes
"read the published page at order time" mandatory; this raises it from ritual to
the specific thing that must be read.

---

## 5. BOM — SEMANTIC, NOT CODE-IDENTITY. **11/11 CLEAN. NO R30-SHAPED DEFECT.**

The R30 precedent (usb-hub v1.3: catalog value 3.09k, schematic label 100k,
identity-only M-BOM passed it) is the reason this had to be done by resolving
the codes, not by comparing them. **What the repo's own M-BOM does is
identity + a LOCAL ledger**: `bom_source_check.py`, RAW EXIT 0, reports
*"every BOM LCSC == source (28 coded)"* plus *"coverage leg C: 7/7 R/C rows
value-graded"* — and leg C grades against `lcsc_passives_ledger.yaml`, a file in
this repo. Canon M1: **that is the checker and the checked sharing a method.**

So I resolved all 11 codes against the vendor, with my own script against JLC's
`selectSmtComponentList` endpoint (independent code path, independent parse),
2026-07-31:

| BOM Comment (= schematic value) | LCSC | catalog `componentModelEn` | BOM MPN | catalog value / spec | pkg ✓ |
|---|---|---|---|---|---|
| 100nF | C1525 | CL05B104KO5NNNC | CL05B104KO5NNNC | **100nF** 16V X7R ±10% | 0402 |
| 10kΩ | C25744 | 0402WGF1002TCE | 0402WGF1002TCE | **10kΩ** ±1% 62.5mW | 0402 |
| 1uF | C15849 | CL10A105KB8NNNC | CL10A105KB8NNNC | **1uF** 50V X5R ±10% | 0603 |
| 220Ω | C25091 | 0402WGF2200TCE | 0402WGF2200TCE | **220Ω** ±1% | 0402 |
| 4.7uF | C1779 | CL21A475KAQNNNE | CL21A475KAQNNNE | **4.7uF** 25V X5R ±10% | 0805 |
| 47Ω | C137864 | RC0402JR-0747RL | RC0402JR-0747RL | **47Ω** ±5% | 0402 |
| 680Ω | C137948 | RC0402FR-07680RL | RC0402FR-07680RL | **680Ω** ±1% | 0402 |
| BLM21SP601SN1D | C3716677 | BLM21SP601SN1D | BLM21SP601SN1D | **600Ω@100MHz**, 2.3 A, 60 mΩ | 0805 |
| KH-SMA-KE-Z | C504007 | KH-SMA-KE-Z | KH-SMA-KE-Z | SMA board-side jack | **Plugin** |
| KT-0603R | C2286 | KT-0603R | KT-0603R | Red LED, Vf 1.8–2.4 V, 20 mA | 0603 |
| PE42482A-X | C5121458 | PE42482A-X | PE42482A-X | **SP8T**, 10 MHz–8 GHz, 2.3–5.5 V | QFN-24 |

**11/11: catalog MPN == BOM MPN, catalog value == schematic label, catalog
package == BOM footprint package token.** `mergedComponentCode` is null/empty on
all 11 and `componentAlternativesCode` likewise — **no code redirects**, so
nothing of the `C82317 → C131025` shape is visible at catalog level. (F-ECHO is
still owed: the uploader is the only instrument that answers that, §2d.)

`bom_legibility_check.py` (F-LEGIBLE), RAW EXIT 0: **13 checks, F-MPN 11/11,
F-WORDS 11/11, F-ENCODE byte-order-mark present, 0 not re-derivable.** My live
read independently corroborates every one of its 11 MPN resolutions.

### STOCK — live, both pools, MOQ included

Live 2026-07-31, my own API read, graded against `build_quantity: 5`:

| LCSC | qty/bd | need 5× | live stock | archive | drift | **MOQ** | verdict |
|---|---|---|---|---|---|---|---|
| C1525 | 1 | 5 | 46 123 730 | 46 128 109 | −4 379 | 1 | CLEAR |
| C25744 | 4 | 20 | 31 252 | 31 036 | +216 | **779** | CLEAR |
| C15849 | 1 | 5 | 14 329 575 | 14 329 374 | +201 | 1 | CLEAR |
| C25091 | 2 | 10 | 1 706 701 | 1 706 906 | −205 | 1 | CLEAR |
| C1779 | 1 | 5 | 3 549 170 | 3 549 249 | −79 | 1 | CLEAR |
| C137864 | 4 | 20 | 73 417 | 73 417 | 0 | 1 | CLEAR |
| C137948 | 1 | 5 | 744 754 | 744 754 | 0 | 1 | CLEAR |
| C3716677 | 1 | 5 | 5 838 | 5 838 | 0 | 1 | CLEAR |
| C504007 | 10 | 50 | 22 707 | 22 708 | −1 | 1 | CLEAR |
| C2286 | 1 | 5 | 7 333 019 | 7 335 999 | −2 980 | 1 | CLEAR |
| C5121458 | 1 | 5 | 1 284 | 1 284 | 0 | 1 | CLEAR |

**11/11 clear. Every archive number re-reads within ordinary drift.** Lifecycle,
by product-page read (not snippet): `C5121458` PE42482A-X — pSemi, **Active**,
no NRND/EOL, MOQ 1, page stock **1 284** matching the API to the unit;
`C504007` KH-SMA-KE-Z — kinghelm, **Active**, Through Hole, MOQ 1. The endpoint
carries **no lifecycle field at all**, so lifecycle is graded on 2 of 11 lines,
the two that matter (sole-source active part, and the 10× line). **The other 9
are UNGRADED for lifecycle and I am naming that rather than implying coverage**
— all 9 are jellybean 0402/0603/0805 passives from stock pools of 5 838 to
46 M.

**TWO THINGS WORTH CARRYING FORWARD:**

1. **`C25744` (10 kΩ, `R_PD1`–`R_PD4`) has `minPurchaseNum: 779` while the build
   needs 20.** It is BUYABLE — 779 ≤ stock 31 252 — and cooksense's fatal shape
   was MOQ (21) > stock (5), which is **not** this. But the order line bills
   **779 pieces ≈ $8.96** instead of 20, and **the archive names this nowhere.**
   It is the only one of 11 lines with an MOQ above its need.
2. **`jlc_stock_check.py` never reads `minPurchaseNum` — and this repo has
   already diagnosed that in writing, twice, in prose that no code consumes.**
   MEASURED: `grep -rn minPurchaseNum skills/` returns **three** hits and
   **ZERO of them are executable code** —

   - `skills/kicad-pcb/references/design-policies.md:167`, the A-BUY canon row:
     cooksense v1.7, *"one BOM line whose `minPurchaseNum` (21) exceeds its
     entire `stockCount` (5) … nine refusals, zero design defects."*
   - `skills/jlcpcb-fab/scripts/release_freshness_check.py:86` — the same
     incident, in a **docstring**.
   - `skills/jlcpcb-fab/references/lcsc_passives_ledger.yaml:145`, and this one
     is the sharpest thing I found all review. Verbatim: *"REPLACES C25862
     (0402WGF1201TCE), whose **minPurchaseNum is 7463** against a stockCount
     that read 25 / 65 / 90 across one afternoon — unorderable in ones, and
     **the naive `stock >= 5 x qty` test passes it.**"*

   **A comment in a data file names the defect in the gate, states that the
   gate's test passes the bad case, and the gate was not changed.** The fix
   there was to swap the PART; the instrument still cannot see the next one.
   And the family recurs on this very board: C25862 is `0402WGF1201TCE`
   (MOQ 7 463) and this board ships `C25744 = 0402WGF1002TCE` (MOQ **779**) —
   the same Uniroyal `0402WGF` series, one line away in the same catalog.
   **`C25744` clears only because 779 ≤ 31 252; nothing in the pipeline
   checked.** Not blocking for this board. Proposal in §9.

**THE TWO POOLS ARE REAL AND I MEASURED THE GAP.** `C504007` reads **22 707**
on JLC's SMT-cart endpoint and **14 953** on its LCSC retail product page, the
same day. Both clear the 50 needed (454× / 299×), so nothing is at risk — but
§2d's claim that *"JLC's assembly uploader allocates from a different pool"* is
now **demonstrated, not asserted**, and a lens that grades one channel has
graded one pool.

**A NEGATIVE RESULT, RECORDED SO NOBODY RAISES IT AS AN ALARM.** The archived
`jlc_catalog_C504007.json` carries a field the ORDER_README does not quote:
**`assemblyComponentFlag: false`**. It reads like a statement that JLC will not
assemble the part. It is not: **I measured it `false` on all 11 codes**,
including base-library 0402 resistors JLC places by the million. **The field
carries no information about assemblability and must not be read as if it
does.** (`isBuyComponent: "1"` and `noBuyReason: null` on all 11.)

---

## 6. THROUGH-HOLE ASSEMBLY — §2a's EVIDENCE IS REAL, AND THE OPTION EXISTS

**Both cited files exist and both say what §2a says they say.** MEASURED:

- `verification/jlc_catalog_C504007.json` — 7 197 bytes, carries a real
  `_provenance` block with `read_at: 2026-07-31T10:06:01-07:00`, the exact
  endpoint, the POST body, a `why:` and a `not_proven:`. Response:
  **`componentSpecificationEn: "Plugin"`** — JLC's own word for through-hole —
  `componentTypeEn: "Coaxial Connectors (RF)"`, `componentLibraryType: expand`,
  `stockCount: 22708`, `minPurchaseNum: 1`. Every field re-reads identical live
  except `stockCount` (22 708 → 22 707).
- `verification/stock_check.csv` — 1 220 bytes, 11 rows, carries the `mpn`
  column, and its `pkg` column reads **`Plugin` for `C504007` and a real SMD
  package string for all ten others.** Exactly as claimed.

**One accuracy note on §2a's quoted block.** It prints
`assemblyProcess  null  <- NO API ANSWERS THIS`. **The key `assemblyProcess`
does not appear in the archived response at all** — it is ABSENT, not null. The
conclusion drawn from it ("no API answers this", therefore human gate) is
correct and I reached it independently; the quoted line presents an absence as a
returned null.

**THE OPTION IS SELECTABLE — measured, and this is new information for the
gate.** `jlcpcb.com/capabilities/pcb-assembly-capabilities`, read live
2026-07-31, lists **"Single sided placement (SMT/Thru-hole)"** under Economic
PCBA and **"Single & double sided placement (SMT/Thru-hole)"** under Standard
PCBA. This board's `03_src/rules/assembly.yaml` declares `service: standard`,
`sides: [top]` — which maps onto a tier the page states supports Thru-hole.

So §2a resolves cleanly into two halves, and only one is still open:
**AVAILABILITY — measured, the option exists on the declared service tier.**
**SELECTION — still a human gate**, because the page states no THT minimums,
fees or per-part acceptance, and `assemblyProcess` is unanswerable by API. If
JLC declines the process the fallback is `not_assembled` /
`process_incompatible` on those ten refs, which is a BOM/CPL change and
therefore a new release.

---

## 7. CPL, POPULATION AND PAYLOAD — clean

| gate | RAW EXIT | result |
|---|---|---|
| `assembly_coverage.py` (A-POP) against the staged archive | **0** | **PASS** — 32 footprints, 27 CPL placements, 5 unpopulated all declared, histogram `top=27`, **A-POS datum worst 0.00000 mm** (tol 0.05) |
| `fab_payload_census.py` | **0** | **OK, 5 checks** — F-IDENT 4/4 copper gerbers distinct; F-POUR 4/4 zone-bearing layers, **In1.Cu = 1 zone → 1 G36 region** (the solid unbroken RF reference) |
| `bom_legibility_check.py` (F-LEGIBLE) | **0** | OK, 13 checks |
| `bom_source_check.py` (M-BOM) | **0** | PASS |
| `release_freshness_check.py` on the staged tree | **1** | **`A-STOCK: 11 graded line(s), verdict=PASS`**, **`A-BUY: SOURCING: CLEAR over 11 coded+placed line(s)`**, `DESIGN: FAIL (10)`, `SOURCING: CLEAR` |
| `policy_audit.py --skip-drc` | **1** | FAIL=1 (A-POP `MANIFEST-UNDECLARED`, an artefact of `07_releases/` being empty), HUMAN=6, N-A=11, PASS=27 |

**THE DENOMINATORS ARE REAL.** `stock_check.json` reads `"graded_lines": 11,
"total_lines": 11, "uncoded_lines": 0, "zero_coverage": null`. A-STOCK and
A-BUY each grade **11**, not zero — the pre-`628ee3d4` failure mode (both gates
resolving through a `fab/bom.csv` that did not exist, reaching a zero
denominator and emitting NOTES) is closed and I confirmed it by reading the
sidecar, not the prose.

**CPL cross-check, MEASURED:** the 27 CPL designators are exactly the union of
the 11 BOM rows' designator lists (1+4+1+2+1+4+1+1+10+1+1 = 27). `U_MCU` appears
in neither. Header is JLC's `Designator,Val,Package,Mid X,Mid Y,Layer,Rotation`.
All 27 rows `top`. Gerber zip: **13 files** — 4 copper, 2 mask, 2 paste, 2 silk,
edge cuts, both drills. `PTH.drl` `TF.FileFunction` = `Plated,1,4,PTH`,
`NPTH.drl` = `NonPlated,1,4,NPTH`. Complete for a JLC 4-layer PCBA order.

**Human gates already named by the archive and still owed** — I re-read the
generated evidence rather than the prose: `rotation_human_gate.txt` names
**`C5121458: U_SW`** as the sole single-channel A-POL placement (LED `C2286` is
adjudicated in §2c and not in the file); `bom_echo_gate.txt` lists **11 coded
lines** for F-ECHO.

---

## 8. STACKUP AND THE IMPEDANCE ORDER

**The fleet claim verifies, and it is broader than stated.** MEASURED:
`grep -c '(stackup'` = **0** on all **34** sealed `07_releases/**/*.kicad_pcb`,
and **0 on all 442** `.kicad_pcb` files anywhere under `projects/`. Fleet norm,
not this board's regression. The 4-layer sealed population is real
(crow-recorder-central-v2 ×8, cooksense ×7, usb-hub-3s-v3 ×13) and none of them
carries one either.

**DOES IT BLOCK AN IMPEDANCE-CONTROLLED ORDER? NO — and here is why, measured
rather than assumed.** JLC's impedance service does not read a `(stackup)` block
out of a `.kicad_pcb`; it is an order-form selection, and the page confirms
controlled impedance is offered on **"4/6/8/…/32 layers"** at **±10 %**. The
laminate is named in the two places the buyer actually reads — `ORDER_README`
§0 and `MANIFEST.txt` line 23 — and I verified the name resolves:

**`JLC04161H-7628` IS A REAL JLC 4-LAYER 1.6 mm STACKUP, and the two numbers the
whole RF constant set rests on are EXACT.** From JLC's own impedance/stackup
page, read live 2026-07-31: top prepreg 7628 = **"0.21040mm"** against the
archive's declared **h = 0.2104 mm**; prepreg 7628 Dk = **4.4** against the
archive's declared **er = 4.4**; 1 oz outer available, against the declared
**t = 0.035 mm**. **The impedance basis checks out against the vendor.**

**One discrepancy, measured and NOT load-bearing — reported because it is real.**
`nets.yaml:388` declares `stackup_mm: [0.2104, 0.9792, 0.2104]  # JLC04161H-7628`.
JLC's page gives the core for that stackup as **1.065 mm**, not 0.9792.
DERIVED: the archive's own vector sums to 1.5004 mm with copper (2×0.035 +
2×0.0152), on a board whose `.kicad_pcb` declares **1.6000 mm**; JLC's numbers
reconstruct **1.5862 ≈ 1.6 mm**. Traced to its consumer: `stackup_mm` is read
**only** by `copper_length_audit.py` for via-barrel pricing, and the RF50 class
is declared `no_vias: true`, so **no shipped RF number moves.** It is a wrong
declared constant in a shipped source file, not a defect in any published
result.

**A PROVENANCE INCONSISTENCY ON THE SAME NUMBER, since impedance is the
deliverable.** The archive grades `h`/`er` three different ways:
`verification/gcpw_constants.txt` — the SHIPPED artifact — marks them
**`[DECLARED]`**; `01_docs/decisions/0005-…md:162-163` marks them
**"MEASURED (stackup)"**; `01_docs/BRIEF.md:98` marks the stackup
**"inherited-UNVERIFIED (v1 ADR-0003)"**. They are now, as of this review,
**corroborated against the vendor's published table** — which is the grade none
of the three had. Worth landing in one place before the seal.

---

## 9. WHAT I WOULD DO — proposals only, nothing applied

Under `skills/` (propose, never apply, per my brief):

1. **`fab_tiers.yaml` — reconcile against the live page (canon M6).** The
   `jlc_4layer_standard` row (via 0.45/0.30, h2h 0.50, track/space 0.127) is
   contradicted by JLC's published 4-layer default (0.25/0.15, 0.2, 0.09/0.09).
   **Do not silently rewrite the numbers** — the rows carry
   `provenance:` strings recording what was proven by ordering, and a live-page
   read is a different authority from a paid-for board. Add the page read as a
   dated second field so the two authorities are visible side by side, and let
   `P-TIER` grade against the stricter of them.
2. **Split `min_hole_to_hole` by PAIR CLASS.** One scalar cannot express a
   vendor who publishes 0.2 mm via-to-via, 0.45 mm pad-to-pad and **nothing** for
   the mixed case. Suggest `min_hole_to_hole: {via_via, pad_pad, via_pad}` with
   `via_pad: UNPUBLISHED` as a first-class value that a gate must report as
   UNGRADED rather than pass (canon M-COVER: a check must not compare against an
   absence). This board's tightest class would then surface as UNGRADED instead
   of as +20.6 %.
3. **Apply the vendor's drill tolerance where a gap is graded.** JLC publishes
   +0.13/−0.08 mm on pad holes and states via holes are uncontrolled. A gap gate
   that ignores a published tolerance reports a margin the board does not have.
4. **`jlc_stock_check.py` must read `minPurchaseNum`.** The field is already in
   every response the tool parses — it is dropped, not missing. Grade it against
   **`stockCount`** (`MOQ > stock` = unorderable in ones; cooksense's fatal
   shape, and C25862's at 7 463 vs 25) and separately against the **build
   quantity** (`MOQ > qty × build_quantity` = a cost surprise, this board's
   C25744 at 779 vs 20), and print both with their denominators. The
   known-bad fixture is already written down and costs nothing to build:
   `lcsc_passives_ledger.yaml:145` records C25862's numbers and states in
   writing that the current test passes them. **A gate whose own reference data
   documents the case it cannot catch has a fixture, not a research problem.**

On this project (not mine to apply either, but they are cheap):

5. **Re-stage.** `source/*.kicad_sch`, `pdf/schematic.pdf`,
   `verification/policy_audit.md`, the `MANIFEST.txt` `git_sha:` and
   `ORDER_README` §4/§7 are all two commits behind their own board. No fab file
   changes. This is the cheapest item on this page and it removes a whole class
   of confusion for the next lens.
6. **Add the §3 DFM question as a fourth human gate on ORDER_README's first
   screen**, with the numbers: 54 via↔PTH pairs under 0.45 mm, worst 0.3016 mm,
   0.2366 mm at the published pad-hole tolerance, and JLC's own unanswered Q&A
   #693. Ask them in writing before the order.
7. **Name the `C25744` MOQ (779 vs 20 needed) in §0's cost paragraph.**
8. **Land the stackup provenance in one place** — `[DECLARED]` /
   `"MEASURED (stackup)"` / `"inherited-UNVERIFIED"` are three grades of one
   number, and it is now corroborated against the vendor's published table.

---

## 10. WHAT I DID NOT FIND — stated plainly, because a clean result is a result

I went looking for these and they are not there:

- **No R30-shaped BOM defect.** All 11 lines resolve to a catalog part whose
  value matches the schematic label. §5.
- **No sourcing wall.** 11/11 clear at ≥5× the build quantity, live, on both
  pools, with the two critical parts confirmed Active by product-page read.
  `BLOCKED-SOURCING` would be a false verdict here and I am not casting it.
- **No stale fab payload.** The gerbers, drills, BOM and CPL are a correct
  export of the board that is in `04_kicad/` today, verified six independent
  ways. §1.
- **No untented vias.** I checked, expecting to find 3446 exposed mask openings.
  `F_Mask` and `B_Mask` carry no via apertures at all — the fence is tented on
  both faces.
- **No missing fab file.** 13 files in the zip, all four copper layers distinct,
  both drill files correctly typed, In1.Cu a single solid pour.
- **No part above the declared tier.** D-TIER/P-TIER pass with the max required
  rank equal to the declared rank.
- **No CPL/BOM disagreement.** 27 placements = the exact union of 11 BOM rows'
  designators; A-POS datum worst 0.00000 mm.
- **`assemblyComponentFlag: false` is not a finding.** It is false on all 11
  codes including base-library passives. §5.
- **No missing paste on `U_SW`'s exposed pad.** The one pad with no aperture is
  the EP, by design; 9 paste-only sub-apertures give 66.9 % coverage. §2.

The board's copper is in good shape. What is not finished is the *case* for
ordering it: one margin that has not survived the vendor's own tolerance, one
tier premise that has not survived the vendor's own page, and an archive that is
two commits behind its own board.

---

*Lens: manufacturability and orderability. Reviewed at git `9af663f0`, staged
tree `06_build/staging/`. Every gate run UNPIPED with the exit code read
directly. Three lenses ran beside this one in fresh context and I did not read
their output.*
