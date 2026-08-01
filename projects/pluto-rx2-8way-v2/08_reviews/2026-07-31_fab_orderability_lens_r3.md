# pluto-rx2-8way-v2 v1.0 — FAB / ORDERABILITY LENS, ROUND 3

subject: pluto-rx2-8way-v2 v1.0 (STAGED, not sealed) — `06_build/staging/`, board written 2026-07-31 16:00:51, archive assembled 16:07–16:23, repo `main` at `083dc488`
date: 2026-07-31
reviewer: redteam-agent (Opus 5, fab-manufacturability and orderability lens — fresh context, round 3)
context-given: full-tree, fresh context; rounds 1 and 2 treated as STALE and re-measured, nothing inherited
verdict: DO-NOT-ORDER

```
design_verdict: DEFECTIVE
order_verdict:  DO-NOT-ORDER
```

**Keys at lines 10–11, deliberately — `M-REV` reads only the first 40 lines and
a missing or out-of-vocabulary verdict is a FAIL, not a skip. Both are from the
closed vocabulary and both were verified to parse by calling
`release_freshness_check._read_review_header` on this file; this file also
returns ZERO `_RELPATH_RE` hits, so it cannot generate a freshness finding by
quoting the paths it reports on.**

**Scope:** manufacturability and orderability, end to end. Copper geometry as a
FAB payload, the fab tier against the board, the hole population, the BOM as a
purchasable document, and the order form as an instruction to a vendor.
Topology, RF and pin-level correctness are other lenses' and are not re-graded
here.

**Method posture.** Round 2's findings were fixed and the board rebuilt, so
every number below was re-derived from the artifacts, with my own code, in this
session. **Nothing is inherited.** Where a claim in `MANIFEST.txt` or
`ORDER_README.md` reproduced, I say CONFIRMED and give my number; where it did
not, I give both. Instruments were chosen to not share a method with the gate
they check (canon M1): the hole census comes from the Excellon files' own
`TA.AperFunction` tool attributes rather than pcbnew, the sourcing numbers from
a hand POST to JLC's catalog endpoint rather than `jlc_stock_check.py`, the
gerber payload from a `kicad-cli` re-export rather than the `pcbnew`
`PLOT_CONTROLLER` that wrote the shipped set, and the DRC leg from four
KNOWN-BAD FIXTURES built out of this board's own copper.

**Why the two keys.**

- `design_verdict: DEFECTIVE` — the copper is clean and I proved the
  instrument that says so can fail (§2). The defect is elsewhere and it is
  ours to fix: **this board has via-in-pad on its only active device, and the
  order package never says so** (§6, F-1). The declared tier's own record
  carries `via_in_pad: true  # POFV: resin-filled + capped, paid option`, and
  the order form in `ORDER_README.md` §0 has no such row and no such cost. An
  edit to artifacts we control turns this green, which is the test for a
  design red.
- `order_verdict: DO-NOT-ORDER` — F-1, plus the two vendor questions that are
  open by construction (§5), plus the three human gates §2 of the order README
  already owes. **Not `BLOCKED-SOURCING`:** sourcing measures CLEAR — 11/11
  lines purchasable, every `minPurchaseNum` 1, every line's stock above 5× its
  build need (§4). Naming a sourcing block here would be false.

**Nothing in `skills/` was edited by this work.** §8 proposes; it does not
apply. The only file this review writes is itself.

---

## 1. THE HOLE POPULATION, RE-CLASSIFIED BY PAIR CLASS FROM THE DRILL FILES

MEASURED with my own Excellon parser over
`fab/pluto_rx2_8way_v2-PTH.drl` and `-NPTH.drl`. Classification comes from the
files' own tool attributes — `TA.AperFunction,Plated,PTH,ViaDrill` on T1
C0.150, `…,ComponentDrill` on T2 C1.400, `NonPlated,NPTH,ComponentDrill` on
the NPTH file's T1 C3.200 — so the census does not depend on reading the board.

| class | count | tool | diameter |
|---|---|---|---|
| VIA | **3446** | PTH T1 | 0.150 mm |
| PTH pad | **50** | PTH T2 | 1.400 mm |
| NPTH | **4** | NPTH T1 | 3.200 mm |
| **TOTAL** | **3500** | | |

**CONFIRMED, exactly.** Also measured: **0** duplicate coordinates, **0** G85
slots, and exactly ONE via class — no second via geometry hides in the file.
Cross-checked against the board from the other side: `04_kicad`-equivalent
`source/pluto_rx2_8way_v2.kicad_pcb` carries 3446 `(via …)` blocks, every one
`(size 0.25) (drill 0.15)` through-hole, 50 `thru_hole` pads at drill 1.4 and
4 `np_thru_hole` at 3.2. Two independent artifacts, same population.

### Minimum hole-to-hole edge-to-edge, by pair class

Nominal, and at max material under the archive's stated model (JLC tolerances
PAD holes +0.13/−0.08 mm on diameter, so a pad hole's radius grows 0.065 mm and
a via's by zero):

| pair class | nominal | max material | where |
|---|---|---|---|
| **VIA ↔ PTH** | **0.3265** | **0.2615** | via (43.000, −27.000) ↔ `J_ANT8.3` (43.960, −27.540) — **the tight class** |
| VIA ↔ VIA | 0.3785 | 0.3785 | (48.060, −30.200) ↔ (48.584, −30.131) |
| NPTH ↔ VIA | 0.3768 | 0.3118 | via (35.000, −87.800) ↔ H4 (36.500, −89.200) |
| PTH ↔ PTH | 1.6934 | 1.5634 | `J_RX2.5` ↔ `J_ANT8.3` |

**All four rows CONFIRMED to four decimals.** Pairs under the 0.25 mm tier
floor at max material: **0** — CONFIRMED (the tightest is 0.2615, 4.6 % clear).

**The `PTH ↔ PTH` correction CONFIRMED, and I reproduced its whole argument:**
of the **41** PTH pairs under 2.6 mm, exactly **ONE is inter-footprint** — the
1.6934 mm `J_RX2.5` ↔ `J_ANT8.3` pair, pad coordinates (43.29, −30.56) and
(43.96, −27.54), which are pin 5 of `J_RX2` and pin 3 of `J_ANT8` by direct
footprint read — and the other **40 are intra-footprint**, a jack's own centre
pin to its own ground post. One precision nit, stated because the MANIFEST says
"exactly": the 40 are **not** all 2.1921 — **24 measure 2.1921 and 16 measure
2.1920**, a 0.1 µm split from Excellon coordinate rounding on the 45°-rotated
jacks. Changes nothing; 1.5634 mm is 3.5× the published 0.45 mm pad↔pad floor.

### Against the floors JLC actually publishes

| | published | board (nominal) | |
|---|---|---|---|
| via ↔ via | 0.20 mm | 0.3785 | **+89 %** |
| pad ↔ pad | 0.45 mm | 1.6934 | **+276 %** |
| **via ↔ pad (mixed)** | **UNPUBLISHED** | **0.3265 / 0.2615** | **ungoverned — §5** |
| NPTH ↔ via (mixed) | UNPUBLISHED | 0.3768 / 0.3118 | second ungoverned class |

**Exposure if the vendor answers "the pad governs" (0.45 mm): 54 VIA↔PTH pairs
are non-compliant nominally — CONFIRMED, and they involve 54 distinct vias,
so it is 54 barrels to move, i.e. a re-stitch and not a re-measurement.** At
max material the same count is 82. At 0.35 mm it is 19 nominal / 43 at max
material; at 0.30 mm, 0 nominal / 25 at max material. That gradient is the
thing to put in the question to JLC, because the answer's cost is not binary.

**A SECOND MIXED CLASS IS PRESENT AND IS NOT NAMED IN THE ARCHIVE.** `NPTH ↔
VIA` at 0.3768 / 0.3118 mm is also between the two published floors and also
unpublished; 8 pairs sit under 0.60 mm and 1 under 0.40 mm. It is looser than
the VIA↔PTH class and clears every candidate floor the VIA↔PTH class clears, so
it adds no new exposure — but the same written question should name it, since
an M3 mounting hole beside a stitching via is a different drilling problem from
a via beside an SMA barrel.

### The max-material model is an ASSUMPTION and it is load-bearing (F-5)

`MANIFEST.txt` states: *"the vendor tolerances PAD holes +0.13/−0.08 mm on
diameter and states the diameter of VIA holes is NOT controlled, so max
material grows a PAD hole's radius by 0.065 mm and a via's by ZERO."*

**"Not controlled" is an argument for more spread, not for none.** I re-ran the
census under the symmetric reading (every hole grows +0.13 mm on diameter):

| model | VIA↔PTH min | pairs < 0.25 (all classes) | pairs < 0.20 |
|---|---|---|---|
| asymmetric (the archive's) | 0.2615 | **0** | 0 |
| symmetric (+0.13 on every hole) | **0.1965** | **32** | 7 |

The declared `min_hole_to_hole: 0.315` and the headline *"pairs under the tier
floor at max material: 0"* are both **conditional on the asymmetric reading**,
and the archive does not quote a vendor sentence saying via holes carry no
tolerance — it quotes the absence of one. This does not change the verdict (the
NOMINAL geometry clears every published floor and nominal is what a DRC grades)
but it belongs in the same written question as §5: *"is your hole-to-hole
minimum evaluated at nominal or at max material, and what tolerance applies to
a 0.15 mm via hole?"* One sentence, same message, closes it.

---

## 2. THE DRC LEG IS NON-VACUOUS — PROVED, NOT ASSERTED

**First, the binding, MEASURED rather than repeated.** I copied `source/`
outside the repository and re-ran the gate myself:

```
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity
  → 0 violations / 0 unconnected / 0 parity     RAW EXIT 0
```

Then I built four KNOWN-BAD fixtures from that same copy and re-ran the
identical command line on each:

| fixture | perturbation | violations | unconnected | parity | **RAW EXIT** |
|---|---|---|---|---|---|
| base | none | 0 | 0 | 0 | **0** |
| `fx_hole` | one via moved 0.35 mm | **2** `hole_to_hole` | 0 | 0 | **0** |
| `fx_mixed` | same via moved 0.0265 mm | **2** `hole_to_hole` | 0 | 0 | **0** |
| `fx_open` | one `ANT2` track segment deleted | 0 | **1** | 0 | **0** |
| `fx_parity` | `R_LED` renamed on the board only | 0 | 0 | **2** | **0** |

**Two conclusions, and the second is the more important one.**

1. **All three halves of the gate can go red on this board's own
   configuration.** `fx_mixed` is the decisive one: it moves the tight-class
   via to a 0.2999 mm nominal gap and KiCad reports
   `hole_to_hole | Drilled hole too close to other hole (board setup
   constraints min 0.3145 mm; actual 0.2999 mm)` with items
   `Via [GND] on F.Cu - B.Cu` and `PTH pad 3 [GND] of J_ANT8`. So the
   **VIA-against-PTH-PAD class — the class the whole §5 vendor question is
   about — is actually graded**, at the floor the board declares, and the
   0/0/0 is a real measurement of it and not an empty set.
2. **Every one of the four fixtures exits 0.** Two hole-to-hole violations,
   a missing connection and two parity errors each returned RAW EXIT 0.
   Binding #76 is not a caution, it is a measurement: without
   `--exit-code-violations`, `kicad-cli pcb drc`'s exit code carries no
   information whatsoever. The MANIFEST already says so in the `gates:` block,
   correctly; the `RAW EXIT` column in `ORDER_README.md` §4 still prints `0`
   beside the DRC rows and a reader who scans the column learns nothing.

**One number the archive does not state.** KiCad enforces the declared 0.315 mm
as **0.3145 mm** (internal-unit rounding, visible verbatim in every fixture
message). Against the board's 0.3265 mm tight pair the true margin is
**12.0 µm**, not 11.5. It passes; it is thin, and thin is worth writing down.

Other legs, checked for vacuity the same way rather than read:

- **`fence_apertures.py`** — the evidence is the ABSENCE of GAP lines, and the
  shipped `verification/fence_apertures.txt` has none; it was given its lattice
  pitch as `argv[2]` (its output states `pitch 0.8 mm`), so it ran rather than
  tracebacked, over `3433 PCB_VIA GND + 40 PTH GND = 3473` fence elements.
  CONFIRMED as non-vacuous input; its exit code is correctly labelled
  not-evidence in both documents.
- **`A-POP`** — `assembly_coverage.txt` grades 32 footprints / 27 CPL / 5
  declared-unpopulated with an A-POS datum worst of 0.00000 mm. The single
  `policy_audit` FAIL is `A-POP MANIFEST-UNDECLARED` resolved against the
  project root because there is no sealed release; against this archive A-POP
  is PASS. CONFIRMED as a path artefact, not a population defect.

---

## 3. THE FAB TIER, CHECKED AGAINST THE BOARD AND NOT AGAINST THE PROSE

### The escape arithmetic — I re-derived every row

MEASURED off `U_SW` in the shipped board, not read from the argument: the
QFN-24 carries **12 lands of 0.600 × 0.300 mm and 12 of 0.300 × 0.600 mm**,
plus a 2.750 × 2.750 mm exposed pad, on a pitch of **0.500 mm** (one edge's pad
centres: 47.75, 48.25, 48.75, 49.25, 49.75, 50.25). So the land is 0.300 mm
across and adjacent land EDGES are **0.200 mm** apart. Premise CONFIRMED.

A via pad centred in the land protrudes `(pad − 0.300)/2` past the land edge,
so its clearance to the neighbour is `0.200 − max(0, (pad − 0.300)/2)`:

| via pad | clearance to the neighbouring land | vs `default_clearance` 0.2 mm |
|---|---|---|
| **0.25 mm** | **0.225 mm** | **fits** |
| 0.40 mm | 0.150 mm | fails |
| 0.45 mm | 0.125 mm | fails |
| 0.60 mm (netclass) | 0.050 mm | fails |

**All four rows reproduce exactly.** JLC footnote ① (*via diameter ≥ via hole
+ 0.1 mm*) then caps the hole at `0.25 − 0.10 = 0.15 mm`, and both no-fee rows
of the fee table need a 0.40–0.45 mm via diameter, which the 0.300 mm land does
not admit. **The tier argument is arithmetically sound and the conclusion —
`jlc_4layer_advanced`, ADVANCED small-via option REQUIRED — is forced.**

Two things I checked that the argument does not say:

- The board sits at the vendor's **minimum**, not its preferred, diameter-vs-
  hole margin: 0.25 − 0.15 = **0.100 mm**, where footnote ① says *"0.15 mm
  preferred"*. That is unavoidable for the same land-width reason, and JLC's
  fee table row 1 sells exactly the `0.15 hole / 0.25 diameter` pair, so it is
  a note and not a defect. It does mean the annular ring is **0.050 mm per
  side**, exactly the board's own `min_via_annular_width`, with no registration
  margin above it.
- The tightest via↔via hole gap within 4 mm of `U_SW` being 0.6017 mm is
  consistent with my global census: the board-wide via↔via minimum is 0.3785 mm
  and it is at (48.06, −30.20), ≈ 7.5 mm from `U_SW`. Hole-to-hole genuinely
  does not bind at the switch — CONFIRMED, and so is the withdrawal of the old
  argument that said it did.

### The board area, drill density and the money

MEASURED from `Edge_Cuts.gm1` alone, independently of the board file: the
profile is four `C,0.100000` strokes at X 20.000 → 70.000 and Y −93.000 →
−20.000.

| quantity | my measurement | archive | |
|---|---|---|---|
| outline (centreline) | **50.000 × 73.000 mm** | 50.000 × 73.000 | CONFIRMED |
| area | **3650.0 mm² = 0.003650 m²** | same | CONFIRMED |
| drill density | **3500 / 0.003650 = 958,904 holes/m²** | same | CONFIRMED |
| × the 150,000/m² threshold | **6.39×** | 6.39× | CONFIRMED |
| small-via fee | **$31.43 + $47.14 × 0.003650 = $31.60** | $31.60 | CONFIRMED |

**The expedited-production consequence is the certain one and the archive is
right to lead with it**: at 6.39× the published threshold this board cannot be
ordered on an expedited build, and the per-hole money on 0.00365 m² lands under
the $1.57 waiver on every reading of the formula. I could not find a reading
that produces a bill; I also could not prove one does not exist, and the
archive does not claim one way or the other. That is the correct posture.

**The ENIG-area exemption CONFIRMED by measurement rather than estimate.**
`F_Mask.gts` carries **188 flashes** and `B_Mask.gbs` **108**, and neither
carries any 0.150 or 0.250 mm aperture — i.e. **there is no mask opening over
any of the 3446 vias**. The vias are tented, so the exposed-metal area is the
pads only and the 30 % ENIG surcharge threshold is not near.

---

## 4. SOURCING — MOQ AND `leastPatchNumber` BY HAND, ALL 11 LINES

Re-measured 2026-07-31 by POSTing each of the BOM's own 11 codes to JLC's
`selectSmtComponentList` endpoint myself, reading the raw JSON. The denominator
is the BOM's (11 rows), not `stock_check.json`'s.

| LCSC | designators | need (5 bd) | stockCount | `minPurchaseNum` | `leastPatchNumber` | `lossNumber` | lib |
|---|---|---|---|---|---|---|---|
| C1525 | C_SW1 | 5 | 46,104,901 | **1** | 20 | 10 | base |
| C60490 | R_PD1..R_PD4 | 20 | 8,740,164 | **1** | 20 | 10 | expand |
| C15849 | C_SW2 | 5 | 14,324,394 | **1** | 20 | 10 | base |
| C25091 | R_T1, R_T2 | 10 | 1,711,397 | **1** | 20 | 10 | base |
| C1779 | C_BULK | 5 | 3,548,238 | **1** | 20 | 10 | base |
| C137864 | R_S1..R_S4 | 20 | 73,417 | **1** | 20 | 10 | expand |
| C137948 | R_LED | 5 | 743,754 | **1** | 20 | 10 | expand |
| C3716677 | FB_3V3 | 5 | 5,838 | **1** | 5 | 0 | expand |
| C504007 | J_ANT1..8, J_RX1..2 | 50 | 22,707 | **1** | 2 | 0 | expand |
| C2286 | LED_ST | 5 | 7,333,303 | **1** | 20 | 10 | base |
| C5121458 | U_SW | 5 | 1,284 | **1** | 0 | 0 | expand |

**11 of 11 pass MOQ. Denominator 11, failures 0. Every `minPurchaseNum` is 1.
CONFIRMED.** Every line's `stockCount` also exceeds 5× its per-board quantity,
by margins of 25× (`C5121458`, the tightest) upward. Sourcing is **CLEAR**.

**`leastPatchNumber`, stated more precisely than the archive states it.** The
value is **20 on EIGHT of the eleven lines**, not six; the ORDER README's "six"
counts the lines whose NEED is strictly below it, which is the right thing to
count and is correct as written (`C60490` and `C137864` need exactly 20 and so
are not among them). The three lines that do not carry 20 are `C3716677` (5),
`C504007` (2) and `C5121458` (**0**). It is a BILLED FLOOR, not a purchase
block — CONFIRMED — and no gate in this repo reads it.

**The known-bad fixture still exists.** Re-queried today: `C25744`
(0402WGF1002TCE) returns `componentLibraryType: base`, `stockCount: 30,612`,
**`minPurchaseNum: 779`**, `canPresaleNumber: **−6,175,847**`. The gate-blind
condition is live and reproducible, which is what makes it a usable fixture for
the §8 proposal.

**THE EXTENDED-PART FEE IS UNAVOIDABLE — VERIFIED ON A WIDER SWEEP THAN THE
CLAIM.** The archive says a sweep of 64 unique 0402 10 kΩ codes found `C25744`
the only `base` one. I swept five keyword forms across two pages each and
collected **322 unique 0402 10 kΩ codes**; of those, **exactly ONE is
`componentLibraryType: base`, and it is `C25744`**. The claim holds on a 5×
larger denominator. The `C25744 → C60490` swap therefore costs one extended
setup fee and there was no basic-library alternative to take instead.

---

## 5. THE TWO OPEN VENDOR QUESTIONS — VERIFIED PRESENT AND SENDABLE

Both are carried in `ORDER_README.md` §7, both as questions to put to JLC in
writing before ordering, both quoted verbatim so a human can paste them:

- **§7 item 4 — the mixed hole class.** *"On the 4-layer advanced tier, what is
  your minimum hole-to-hole edge-to-edge between a 0.15 mm VIA hole and a
  1.40 mm PTH PAD hole, and is it evaluated at nominal or at max material?"*
  It states the exposure (54 pairs, re-stitch) and cites the unanswered public
  Q&A. **VERIFIED PRESENT AND ADEQUATE.**
- **§7 item 5 — impedance vs the 0.15 mm drill.** *"…is the 'Min. Via: 0.2mm'
  on your controlled-impedance capability page a via HOLE minimum or a via
  DIAMETER minimum, and can that order carry 0.15 mm drilled / 0.25 mm finished
  vias?"* It records that a returned QUOTE is not an answer, which is the right
  guard. **VERIFIED PRESENT AND ADEQUATE.** `01_docs/decisions/0006-*.md`
  exists (7,652 bytes, written 16:37) and deliberately does not pick a reading.

Neither can be closed by measurement and I did not try. Two amendments I would
make to the same message rather than a new one:

1. add the **max-material / via-hole-tolerance** clause from §1 (F-5);
2. add the **`NPTH ↔ VIA` mixed class** from §1, so the question covers both
   ungoverned classes rather than one.

---

## 6. WHAT THIS LENS ADDS — findings, classified

### F-1 · P1 · VIA-IN-PAD ON THE BOARD'S ONLY ACTIVE DEVICE, AND THE ORDER FORM NEVER SAYS SO

**MEASURED.** Ten of the 3446 vias have their centres inside a solderable land
of `U_SW`:

| land | size | layers | vias inside |
|---|---|---|---|
| pad 8 (`3V3`) | 0.300 × 0.600 | `F.Cu F.Mask F.Paste` | 1 at (40.250, 50.900) |
| pad 11 (`SW_V3`) | 0.300 × 0.600 | `F.Cu F.Mask F.Paste` | 1 at (41.750, 50.900) |
| pad 18 (`GND`) | 0.600 × 0.300 | `F.Cu F.Mask F.Paste` | 1 at (42.900, 47.700) |
| pad 25 (EP) | 2.750 × 2.750 | `F.Cu F.Mask` | **7** |

Every one is a 0.150 mm drilled, 0.250 mm finished through-via. **None is
plugged from the top**: `F_Mask.gts` carries no aperture at 0.150 or 0.250 mm,
so the vias are tented globally — but each of these ten sits inside its own
land's mask OPENING, which is larger. `B_Mask.gbs` has no opening there, so
they are soldermask-plugged from below only. The three signal lands each carry
`F.Paste`; the EP's paste is a 3 × 3 array of 0.750 × 0.750 mm windows
(**66.9 %** coverage), and **6 of the 7 EP vias sit directly under a paste
window** (the seventh, (42.35, 48.93), misses by 0.025 mm).

**The arithmetic, at a nominal 0.10 mm stencil and ~50 % metal by volume:**

| | solder available | barrel volume | ratio |
|---|---|---|---|
| a 0.300 × 0.600 land | 0.00876 mm³ | 0.02827 mm³ | **barrel is 3.23× the solder** |
| the EP (9 windows) | 0.2531 mm³ | 7 × 0.02827 = 0.1979 mm³ | **barrels are 78 % of the joint** |

**The order package does not name this.** I grepped `MANIFEST.txt` and
`ORDER_README.md` for `via-in-pad`, `plug`, `POFV`, `resin`, `epoxy`, `fill`,
`tent`: the only hits are §0's passing mention of via-in-pad *inside the tier
justification* and the phrase "Vias are tented" *inside the ENIG-area
argument*, which is about the other 3436 vias. **§0's order-form table has no
via-covering row, and §0's cost section (small-via fee, drill density, ENIG)
prices no via fill.**

**And the tier the board declares already carries the option.**
`skills/kicad-pcb/references/fab_tiers.yaml`, `jlc_4layer_advanced`:

```
    via_in_pad: true          # POFV: resin-filled + capped, paid option
```

So the field exists, this board's tier sets it, the board's geometry needs it,
and it never reached the order form. That is the gap.

**Prior art, so this is not presented as newly discovered.** The r2 layout lens
found the EP half — `2026-07-30_v1.0_redteam_layout_r2.md` item **L-09**, P2,
same seven coordinates, same 67 % coverage — and its remedy was *"either add
mask dams inside the EP or record the plugging requirement in the fab
MANIFEST."* **Neither was done, and L-09 does not appear in
`08_reviews/DISPOSITIONS.md` at all** (grep: zero hits for `L-09` and for
`plugg`). What is new here is (a) that the recommendation did not survive the
rebuild, (b) the **three signal lands**, which L-09 did not measure and which
are the worse case at 3.23× rather than 0.78×, and (c) the `fab_tiers.yaml`
row that shows the option was always available.

**REMEDY — cheapest first, none of them a copper change:**
1. add a **via covering** row to `ORDER_README.md` §0's order table declaring
   **resin-filled and capped (POFV)** vias, and price it in the same section as
   the $31.60 small-via fee; **or**
2. offset the EP paste windows off the six barrels and move the three signal
   escapes to via-beside-pad — a re-route, expensive; **or**
3. accept it explicitly with a written statement of the risk on the three
   signal joints. **What is not acceptable is the current state, in which the
   order says nothing and the fab's default decides.**

### F-2 · P2 · THE SHIPPED GERBERS CARRY DRILL MARKS NO GATE READS

**MEASURED.** I re-exported the archive's own `source/` with `kicad-cli pcb
export gerbers` and compared command MULTISETS (not bytes — canon: gerbers are
not byte-comparable run to run). `F_Paste`, `B_Paste`, `F_Silkscreen`,
`B_Silkscreen` and `Edge_Cuts` are **command-multiset IDENTICAL**. Every copper
layer differs by exactly **3504** commands present in the shipped file and
**0** the other way; both masks by **56**, same direction. Resolved:

| layer group | extra in shipped | what it is |
|---|---|---|
| F/In1/In2/B_Cu | 3446 × `C,0.150000` + 54 × `C,0.350000`, all `%LPD*%` | KiCad drill marks (via drill; PTH/NPTH clamped to the 0.35 mm small-drill size) |
| F/B_Mask | 54 × `C,0.350000`, `%LPD*%` | same, at the 50 PTH + 4 NPTH centres |

They are plotted in **DARK** polarity, so they ADD rather than punch. I checked
subsumption per flash rather than assuming it: all **3446** via marks are
concentric inside their own 0.250 mm via pad, and **50 of the 54** coincide
with a 1.900 mm PTH flash (or, on the masks, all 54 coincide with a 1.9/3.2 mm
opening). **The remaining four do not:** they are isolated 0.350 mm copper dots
at (23.8, −23.8), (23.8, −89.2), (36.5, −89.2) and (66.0, −23.8) — the four M3
NPTH centres — **on all four copper layers**, with no pad under them.

**Fabricated consequence: none.** Each dot is entirely inside a 3.200 mm
non-plated hole and is drilled away. **Documented consequence: three.** (a) The
shipped gerbers are not reproducible by `kicad-cli`, only by
`export_jlc_package.py`'s `PLOT_CONTROLLER` path, and the archive's
regenerability claim does not say which. (b) `fab_payload_census.py`
(F-PAYLOAD) grades layer distinctness and pour presence and does not see them.
(c) A CAM operator extracting a netlist from the gerbers sees four unnetted
copper islands and may raise a query that delays the order. **Recommend:** set
the plotter's drill-mark mode explicitly to none in the exporter and say so, or
declare the marks in `MANIFEST.txt`'s `fab:` block. **PROPOSED, not applied.**

### F-3 · P3 · THE GATE TABLE UNDER-REPORTS `part_facts` BY ONE, AND THE MISSING ONE IS LOAD-BEARING

`ORDER_README.md` §4 row: *"`part_facts_check.py` (P-FACT) — **OK**, with 1
assertion UNREACHED and NAMED (RP2040-Zero's value assert…)"*. The shipped
`verification/part_facts.txt` says **`6/8 assertion(s) REACHED … (2
unreached)`** and names both. The second is:

```
P-FACT-UNREACHED: KT-0603R: pad1_net_polarity declared but no exported
                  netlist found under 06_build/fab
```

That is the assertion that would have machine-checked `LED_ST` pad 1 on GND —
which is precisely the "the board corroborates it without reading any drawing"
channel `ORDER_README.md` §2c leans on when it refutes the twin's
`ROT-DB-SUGGEST C2286,180`. The conclusion is still right (I confirmed pad 1 →
`GND`, pad 2 → `LED_STAT_A` in the board, and the tsx source states pad 1 =
CATHODE), **but it is a human channel, not the gate the §4 table implies ran.**
Fix the count and re-point the check at a directory that has the netlist.

### F-4 · P3 · STAGING EVIDENCE NAMES THE PRE-STAGING PATH

`verification/bom_source_check.txt` names `06_build/fab/bom.csv` and
`verification/bom_legibility.txt` names an absolute path to the same file, while
the archive ships `fab/bom.csv`. I byte-compared both: `bom.csv` and `cpl.csv`
are **IDENTICAL** to `06_build/fab/`, so nothing is stale and no number is
wrong. It is a seal-time hazard only — the freshness gate's evidence-path check
fires on release-directory names, and this is exactly the shape that failed on
a sibling board. Re-point or re-run at seal.

### Nothing else blocking that I could find

Checked and **CLEAR**, listed so they are not re-opened: the upload zip carries
all 13 fab files with **zero** byte differences from the loose copies and
**zero** fab files omitted; `F_Paste` has an aperture for every SMD pad and
**none over any of the 50 PTH barrels**, which is the measured basis of the
through-hole-assembly human gate; `B_Paste` is empty and the CPL histogram is
top = 27 / bottom = 0, consistent; `bom_legibility` grades 11/11 rows against a
hand-verified authority with the UTF-8 BOM declared; the CPL's 27 rows and the
BOM's 11 lines reconcile refdes-for-refdes.

---

## 7. M-BOM, GRADED SEMANTICALLY — 11/11

`bom_source_check.py`'s leg C prints `7/7 R/C rows value-graded (11 BOM rows
seen)`. **CONFIRMED as written and it is the wrong denominator**: it is 7 of
11, and it decodes the BOM's own `MPN` column against the BOM's own `Comment`
— checker and checked in the same row, which proves the row is
self-consistent and nothing about the world. The four rows it never grades are
the ferrite, the SMA, the LED and **the RF switch, which is the board's entire
function**.

So I resolved all eleven LCSC codes against JLC's catalog record (brand, MPN,
package, and the full parametric `describe`) and compared each to the
SCHEMATIC's own `Value`, which is a different document from the BOM:

| refdes | schematic `Value` | BOM Comment / MPN | catalog record | |
|---|---|---|---|---|
| C_SW1 | `100nF` | 100nF / CL05B104KO5NNNC | Samsung, 100nF 16V X7R ±10% **0402** | MATCH |
| R_PD1..4 | `10kΩ` | 10kΩ / RC0402FR-0710KL | YAGEO, 10kΩ ±1% 62.5 mW 50V **0402** | MATCH |
| C_SW2 | `1uF` | 1uF / CL10A105KB8NNNC | Samsung, 1µF 50V X5R ±10% **0603** | MATCH |
| R_T1, R_T2 | `220Ω` | 220Ω / 0402WGF2200TCE | Uniroyal, 220Ω ±1% 62.5 mW **0402** | MATCH |
| C_BULK | `4.7uF` | 4.7uF / CL21A475KAQNNNE | Samsung, 4.7µF 25V X5R ±10% **0805** | MATCH |
| R_S1..4 | `47Ω` | 47Ω / RC0402JR-0747RL | YAGEO, 47Ω **±5%** 62.5 mW **0402** | MATCH |
| R_LED | `680Ω` | 680Ω / RC0402FR-07680RL | YAGEO, 680Ω ±1% 62.5 mW **0402** | MATCH |
| FB_3V3 | `C3716677` | BLM21SP601SN1D | Murata, **600Ω@100 MHz**, 2.3 A, 60 mΩ, **0805** ferrite | MATCH |
| J_ANT1..8, J_RX1..2 | `C504007` | KH-SMA-KE-Z | Kinghelm, SMA coaxial RF, spec **"Plugin"** (through-hole) | MATCH |
| LED_ST | `C2286` | KT-0603R | KENTO, red 615–630 nm, 20 mA, **0603** | MATCH |
| U_SW | `C5121458` | PE42482A-X | pSemi, **SP8T RF switch, 10 MHz–8 GHz**, 2.2 dB IL, 85 dB isolation, 2.3–5.5 V, **QFN-24** | MATCH |

**11/11 resolve. Denominator 11, failures 0.** Every package matches its
footprint (`0402`↔`R_0402_1005Metric`, `QFN-24`↔`QFN-24_4x4_P0.5_EP2.7`,
`Plugin`↔`SMA_Vertical_5.08sq_D1.4`, and so on), every ceramic's voltage rating
(16 V minimum) clears the 3V3 rail with margin, and the RF switch is an **SP8T**
against a board with eight antenna ports — the topology the part is for.

Two tolerance notes, neither a defect: `R_S1..R_S4` are ±5 % where every other
resistor is ±1 %; they are the control-line series elements, not RF, so ±5 % is
appropriate. `R_T1`/`R_T2` at ±1 % are the tap divider and are correctly the
tighter part.

---

## 8. PROPOSED SKILL CHANGES — NOT APPLIED

This board does not own `skills/`. Each item is written so its owner can act
without re-deriving it. Items 1–6 of `ORDER_README.md` §9 are separately
proposed there and I do not restate them; these are additional, and I
re-measured the two that overlap.

1. **`jlc_stock_check.py` must read `minPurchaseNum` AND `leastPatchNumber`.**
   Re-measured today: the fixture is live (`C25744`, `minPurchaseNum` 779,
   `canPresaleNumber` −6,175,847) so the gate can be shown to fail, and
   `leastPatchNumber` arrives in the same JSON response at zero extra cost —
   **20 on 8 of this board's 11 lines**. Emitting the required purchase
   quantity and the billed floor per line is a print statement over data the
   tool already has in memory.
2. **`fab_tiers.yaml`'s `via_in_pad:` flag has no consumer.** It is set
   `true` on `jlc_4layer_advanced` with the comment
   `# POFV: resin-filled + capped, paid option`, and nothing reads it — no
   gate cross-checks it against the board's actual via-in-pad population, and
   no template puts it on the order form. F-1 is exactly the failure that
   creates. **Proposal:** a gate that counts vias whose centre lies inside an
   SMD land and FAILS when that count is non-zero and the order README carries
   no via-covering declaration. The population is trivially computable and the
   known-bad fixture is this board.
3. **`export_jlc_package.py` should set the drill-mark mode explicitly.** The
   `PLOT_CONTROLLER` default puts 3446 + 54 dark drill-mark flashes on every
   copper layer and 54 on every mask layer (F-2). Whatever the intended value,
   it should be stated in the script rather than inherited, and
   `fab_payload_census.py` should count apertures that correspond to no pad or
   via pad so the condition is visible.
4. **`bom_source_check.py` leg C's denominator.** Confirmed exactly as
   `ORDER_README.md` §9 item 5 describes: `7/7` over a file of 11 rows. It
   should print `7/11` and NAME the four ungraded rows. I add one measurement
   to that proposal: the four are `C3716677`, `C504007`, `C2286` and
   `C5121458`, and the last is the board's only active device — so the check's
   coverage gap is exactly co-extensive with the parts whose Comment IS their
   MPN, i.e. the ones where the check degenerates into comparing a string with
   itself.

---

## 9. WHAT I COULD NOT CLOSE, AND WHY

- **The mixed hole class** (§1, §5) — the vendor has published nothing between
  0.2 mm and 0.45 mm and their own public Q&A on it is unanswered. Not
  closeable by measurement; the exposure gradient in §1 is the best a
  measurement can do.
- **Impedance control with a 0.15 mm drill** (§5) — an ABSENCE in the vendor
  spec, correctly recorded in ADR-0006 without picking a reading.
- **The via-hole tolerance at max material** (§1, F-5) — same class: the
  archive quotes the absence of a published via-hole tolerance and then models
  it as zero. Send it with the other two.
- **F-ECHO** — whether JLC's uploader resolves our 11 codes to our 11 parts
  can only be answered by the uploader. `verification/bom_echo_gate.txt` sets
  it up correctly with all 11 codes and their designators.
- **Whether JLC will run the plug-in line at all** — `assemblyProcess` comes
  back `null` from the catalog endpoint (I confirmed the field exists and is
  null on `C504007`), so it is a human gate by necessity, not by choice.
- **The `U_SW` rotation** — single-channel under A-POL, correctly escalated to
  the order-preview human gate by the exporter's own
  `fab/rotation_human_gate.txt`.

## 10. THE SHORT VERSION

The copper is clean and I proved the instrument that says so can fail on all
three of its halves, including on the exact hole class the vendor question is
about. The tier is correctly chosen and its arithmetic reproduces row for row.
The board area, drill density, the 6.39× expedited-production bar and the
$31.60 small-via fee all reproduce. The BOM is purchasable — 11/11 on MOQ,
11/11 on stock, and I graded all eleven lines semantically against the catalog,
including the four the gate structurally cannot reach. Sourcing is CLEAR and
the extended-part fee on the 10 kΩ line is genuinely unavoidable, which I
verified on 322 candidate codes rather than 64.

**What stops the order is not the copper and not the parts. It is that this
board puts open, unfilled 0.15 mm vias inside three signal lands and the
exposed pad of a 0.5 mm-pitch QFN, and the document that instructs the vendor
does not mention it — while the tier that document declares carries the paid
option that fixes it.** That, the two questions JLC has not been asked, and the
three human gates already owed, are the whole of `DO-NOT-ORDER`.
