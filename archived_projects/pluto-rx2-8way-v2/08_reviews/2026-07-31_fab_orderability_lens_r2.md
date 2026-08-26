# pluto-rx2-8way-v2 — FAB / ORDERABILITY LENS, ROUND 2

subject: pluto-rx2-8way-v2 v1.0 (STAGED, not sealed) — `06_build/staging/`, board written 2026-07-31 14:30, archive re-staged 14:56, MANIFEST git_sha `2a65b60b`
date: 2026-07-31
reviewer: redteam-agent (Opus 5, fab-manufacturability and orderability lens — fresh context, round 2)
context-given: full-tree, fresh context; round-1 verdicts treated as STALE and re-measured, nothing inherited
verdict: DO-NOT-ORDER

```
design_verdict: DEFECTIVE
order_verdict:  DO-NOT-ORDER
```

**Keys at line 12, deliberately — `M-REV` reads only the first 40 lines and a
missing verdict is a FAIL, not a skip.**

Lens: manufacturability and orderability. Every number below was re-measured
against THIS archive, on an instrument that shares no method with the one that
produced it.

**THE ROUND-1 FINDING IS FIXED AND THE FIX IS CORRECT.** Independently
re-classified from the DRILL FILES (not pcbnew — canon M1): min hole-to-hole by
pair class is `VIA<->PTH 0.3265 nominal / 0.2615 at max material`, and
**sub-floor pairs at the 0.25 tier floor: 0**, down from 8. Every class figure in
the MANIFEST reproduces to four decimals **except one** (F-3 below). The gate
that certifies it was proven able to FAIL on this exact mixed class with a
known-bad fixture. That work is done and I am not re-opening it.

**THE VERDICT IS DO-NOT-ORDER FOR A REASON THE ARCHIVE DOES NOT CARRY.** Two
new order-blocking findings, both outside the hole-to-hole story:

- **F-1 — ONE BOM LINE CANNOT BE BOUGHT AT THE QUANTITY THE BOARD NEEDS.**
  `C25744` (10 kΩ, `R_PD1..R_PD4`) needs **20** pieces at build_quantity 5.
  JLC's own API returns `minPurchaseNum` **779** and `canPresaleNumber`
  **−6,175,510**. `A-STOCK` reads `stockCount` only, reports **PASS 11/11**, and
  ORDER_README §1 states **"No sourcing wall … every coded line clears the build
  quantity"**. That sentence is false. MEASURED first-hand, all 11 lines.
- **F-2 — TWO ORDER OPTIONS THE ARCHIVE DECLARES MAY BE MUTUALLY EXCLUSIVE.**
  §0 marks *0.15 mm via drill* **REQUIRED** and *impedance control* **REQUESTED**.
  JLCPCB's controlled-impedance capability table publishes **"Min. Via: 0.2mm"**.
  The archive raises this nowhere. MEASURED on two channels.

**THE VENDOR QUESTION §7.4 ASKS IS THE RIGHT QUESTION AND IS STILL OPEN**, and I
found the wording sound (§2 below). But §0's supporting arithmetic rests on two
no-fee floor numbers that the vendor page refutes (F-4), and the round-1 doubt
about whether the paid via option is needed at all is **REFUTED — it is needed,
and priced** (§3).

---

## 0. WHAT I MEASURED, AND HOW

| # | Question | Method (independent of the archive's) | Result |
|---|---|---|---|
| 1 | hole population by pair class | own parser over `fab/*.drl`, class from KiCad's own `TA.AperFunction` tags, pure-stdlib spatial grid + exact brute force on the small classes | 5 of 6 class rows reproduce; 1 does not (F-3) |
| 2 | can the hole-to-hole gate fail on the mixed class? | known-bad fixture: nudged one via to 0.1965 mm from `J_ANT8.2` | **YES** — 2 `hole_to_hole` violations. Gate is real |
| 3 | DRC | `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity`, unpiped, on a copy OUTSIDE the repo | 0 / 0 / 0, RAW EXIT 0 — but see F-8 |
| 4 | vendor capability | my own WebFetch of `jlcpcb.com/capabilities/pcb-capabilities`, `/impedance`, `/help/article/in-what-cases-will-there-be-charged-extra` + a separate agent on 8 channels incl. a direct read of JLC's fee-table PNG | see §3 |
| 5 | BOM identity + MOQ | direct `POST` to JLC's `selectSmtComponentList` API for **all 11** codes | 11/11 identity OK; **1/11 fails MOQ** |
| 6 | hole-to-track | own geometry pass, 3496 holes × 199 segments, same-net excluded | clears vendor floors (§4) |
| 7 | upload payload | `unzip` + `cmp` of the gerber zip against the loose files | 13/13 bit-identical |

Everything below is marked **MEASURED** (I ran it), **DERIVED** (arithmetic on a
measured number), or **INHERITED** (read from the archive, not re-measured).

---

## 1. THE HOLE POPULATION, RE-CLASSIFIED FROM THE DRILL FILES

**MEASURED.** Parsed `fab/pluto_rx2_8way_v2-PTH.drl` and `-NPTH.drl` — the
artifact the vendor actually receives. Class comes from KiCad's own Excellon
attributes, `Plated/ViaDrill` vs `Plated/ComponentDrill` vs `NonPlated`, so the
classification is the fab's, not mine and not the archive's.

```
TOOLS  PTH file : T1 = 0.150 ViaDrill,  T2 = 1.400 ComponentDrill
       NPTH file: T1 = 3.200 ComponentDrill (NonPlated)

CENSUS   VIA  0.1500 mm × 3446
         PTH  1.4000 mm ×   50
         NPTH 3.2000 mm ×    4      TOTAL 3500
```

Census matches the MANIFEST exactly. Max-material model held identical to the
archive's so the comparison is apples-to-apples: PAD holes +0.13/−0.08 mm on
diameter → **+0.065 mm on radius**; via hole diameter not controlled → **+0.000**.

| pair class | nominal | max material | MANIFEST | verdict |
|---|---|---|---|---|
| `VIA <-> PTH` | **0.3265** | **0.2615** | 0.3265 / 0.2615 | ✅ reproduces |
| `VIA <-> VIA` | 0.3785 | 0.3785 | 0.3785 / 0.3785 | ✅ reproduces |
| `NPTH <-> VIA` | 0.3768 | 0.3118 | 0.3768 / 0.3118 | ✅ reproduces |
| `PTH <-> PTH` | **1.6934** | **1.5634** | *2.1921 / 2.0621* | ❌ **F-3** |
| `NPTH <-> PTH` | 3.8088 | 3.6788 | (not carried) | — |
| `NPTH <-> NPTH` | 9.5000 | 9.3700 | (not carried) | — |

**Sub-floor pairs at the 0.25 tier floor, at max material: 0.**
**Pairs below the declared 0.315 floor, nominal: 0.**
The round-1 defect (8 of 54 pairs at 0.2366 max-material) is CLOSED. MEASURED.

Population by threshold, so the shape of the distribution is visible rather than
a single number:

```
nominal  < 0.315 : none
nominal  < 0.350 : PTH<->VIA 19
nominal  < 0.400 : PTH<->VIA 38, VIA<->VIA 2, NPTH<->VIA 1
nominal  < 0.450 : PTH<->VIA 54, VIA<->VIA 2, NPTH<->VIA 1
maxmat   < 0.250 : none
maxmat   < 0.280 : PTH<->VIA 13
maxmat   < 0.315 : PTH<->VIA 30, NPTH<->VIA 1
```

The r1 structural claim survives verbatim: the tight population is **54 VIA↔PTH
pairs under 0.45 mm**, not the 3446-via fence. The fence's own worst pair is
0.3785 and it is the LOOSEST of the three tight classes. The 8 displaced
`seed_stubs` moved the right holes.

### F-3 — the MANIFEST's `PTH<->PTH` row is INTRA-FOOTPRINT ONLY, and understates its class by 0.4987 mm

**SETTLED. The independent reimplementation is right; the shipped MANIFEST is wrong.**

MEASURED, exact brute force over all 1225 PTH pairs (no spatial prefilter that
could hide a distant pair):

```
min PTH<->PTH = 1.6934 nominal / 1.5634 max material
  at drill (43.2900, −30.5600) <-> (43.9600, −27.5400), centre distance 3.0934
```

Attributed by footprint origin and the vendored footprint's own pad map
(`SMA_Vertical_5.08sq_D1.4`: pad 1 = centre = RF signal at (0,0); pads 2–5 = the
four ground posts at (±2.54, ±2.54)):

- `J_RX2` origin (40.75, −33.10), rotation 0 → offset (+2.54, +2.54) = **pad 5**
- `J_ANT8` origin (46.50, −25.00), rotation 0 → offset (−2.54, −2.54) = **pad 3**

**`J_RX2.5` ↔ `J_ANT8.3`. Exactly the pair the dispute named.**

**The mechanism, which is the part that matters.** The MANIFEST's 2.1921 is not
a rounding difference and not drift — it is a **different measurement**. Within
one jack, centre pin to any ground post is 2.54·√2 = 3.5921 mm centre-to-centre,
minus two 0.700 mm radii = **2.1921 exactly**. That is the intra-footprint
minimum, and it is what the MANIFEST reports. Of the 41 PTH↔PTH pairs under
3.0 mm, **39 sit at exactly 2.1920/2.1921** — every one of them a jack's own
centre-to-post distance. The true class minimum is the one pair that spans
**two different footprints**, and the row that reports it never looks there.

**Does it change anything? No, and I checked rather than assumed.** JLC publishes
`Pad Hole-to-Hole Spacing 0.45mm` (MEASURED, capabilities page). 1.5634 at max
material is **3.5× that floor**. No pair moves, no gate changes, no verdict
changes.

**What it costs is the instrument.** A class-minimum row that structurally cannot
see an inter-footprint pair is the same failure shape as the round-1 finding one
level up: the number is real, its SCOPE is narrower than its label, and the label
is what a reviewer checks against. Here the narrower scope happened to be
harmless because two SMA jacks are 3 mm apart. On a board with two THT connectors
side by side it would not be. **Propose (do not apply): the emitter that writes
the MANIFEST `fab:` census must enumerate PTH↔PTH across footprint boundaries,
and `t1_*` needs a two-footprint fixture whose inter-footprint pair is tighter
than either footprint's internal minimum — it goes RED against today's emitter.**

### The gate can fail — proved, not assumed

**MEASURED.** Repo canon requires a known-bad fixture. Copied the archive source
to scratch, moved one via 0.13 mm along the line to `J_ANT8`'s pad-2 barrel:

```
via (43.0, 23.0) -> (43.1133, 22.9363)     gap 0.3265 -> 0.1965 mm
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity
  Found 2 violations
  hole_to_hole | warning | Drilled hole too close to other hole
                           (board setup constraints min 0.3145 mm; actual 0.1965 mm)
```

Two things follow, and both are load-bearing:

1. **KiCad's `hole_to_hole` rule DOES police the VIA↔PTH-pad mixed class.** So
   the archive's `DRC 0/0/0` is genuine evidence for the tight class — it is not
   green because the rule looks away. This was worth proving: had the rule been
   via-to-via only, the entire DRC leg of the fix would have been vacuous and
   only the offline measurement would stand.
2. **The enforced floor is 0.3145 mm, not the declared 0.315.** KiCad applies a
   0.5 µm epsilon. Immaterial here (the board's 0.3265 clears the declared floor
   by 11.5 µm and the enforced one by 12.0 µm), but a pair at 0.3146 would pass
   DRC while sitting under the value `floorplan.yaml` declares. Worth knowing
   before anyone tunes to the floor. MEASURED.

---

## 2. THE VENDOR QUESTION — §7 item 4 is CORRECT, and is NOT the only one owed

**VERIFIED PRESENT AND CORRECTLY WORDED.** ORDER_README §7 item 4 carries it as a
DFM item to put to JLC in writing before ordering, states plainly that the 0.315
fix "is NOT an answer to the vendor question", and asks:

> *"On the 4-layer advanced tier, what is your minimum hole-to-hole edge-to-edge
> between a 0.15 mm VIA hole and a 1.40 mm PTH PAD hole, and is it evaluated at
> nominal or at max material?"*

That is the right question. It names both hole classes, both diameters, the tier,
and — the part most requests omit — **the evaluation basis**, which is the exact
axis the round-1 defect turned on. I would not change a word.

**The premise is corroborated, not merely repeated.** MEASURED on my own channel,
`jlcpcb.com/capabilities/pcb-capabilities`:

```
Via Hole-to-Hole Spacing   0.2mm
Pad Hole-to-Hole Spacing   0.45mm
```

Two rows, no third. **No mixed via-to-pad rule is published.** The independent
agent additionally confirmed the description column for both rows is literally
empty in the raw HTML (so neither row states edge-to-edge vs centre-to-centre),
and located **Q&A #693** — posted **2025-03-07**, asking exactly this, **still
unanswered**, verified on the `jlccnc.com` mirror as well. Two sibling questions
(#110, #26) are likewise unanswered; JLC's Q&A is an unmoderated question board,
not an answer source. So the archive's characterisation is accurate.

**Where the board actually stands against the two rules that DO exist** (DERIVED
from my §1 measurement):

| published rule | board's worst, nominal | at max material | |
|---|---|---|---|
| Via↔Via **0.2 mm** | 0.3785 | 0.3785 | ✅ +89% |
| Pad↔Pad **0.45 mm** | 1.6934 | 1.5634 | ✅ +247% |
| *(mixed, unpublished)* | **0.3265** | **0.2615** | **⚠️ ungoverned** |

The mixed class sits between the two published floors — above via-to-via, below
pad-to-pad. That is precisely why no published number resolves it, and why the
answer could legitimately land anywhere in `[0.2, 0.45]`. **If JLC answers 0.45
(i.e. the pad governs), 54 pairs are non-compliant and the board needs
re-stitching, not a re-measurement.** The archive does not say this, and it is
the thing that determines how much rework the answer implies. Worth adding to
§7.4 in one sentence: *the exposure if the answer is "the pad governs" is 54
pairs.*

### F-2 — a SECOND vendor question is owed, and the archive does not raise it

**MEASURED, two channels** (my own WebFetch of `jlcpcb.com/impedance`, and the
independent agent's raw fetch of the same page). The controlled-impedance
capability header reads:

> *"Min. Trace width/Spacing: 3.5mil | **Min. Via: 0.2mm** | Min. BGA: 0.25mm"*

ORDER_README §0 declares **both** of these on the same order:

- `Via / process tier` → **0.15 mm drill, ADVANCED small-via option REQUIRED**
- `Impedance control` → **REQUESTED**, stackup `JLC04161H-7628` **REQUIRED**

**"Min. Via: 0.2mm" is ambiguous between hole and diameter, and the board's
status flips on that reading:**

- if it means via **HOLE**: 0.15 < 0.20 → the board's vias are **below the
  impedance-controlled process minimum**, and the two options cannot both be had.
- if it means via **DIAMETER**: 0.25 ≥ 0.20 → no conflict.

I cannot resolve it from the page and I will not guess. Two things tilt toward
the hole reading and neither is conclusive: the capabilities page's own footnote
② names *"Preferred Min. Via hole size: 0.2mm"* (the same number, explicitly a
hole), and JLC's fee table's left column — `0.15 / 0.2 / 0.25 / 0.3` — is hole
size throughout. The general capabilities page writes the pair explicitly
(`Min. Via hole size/diameter — 0.15mm / 0.25mm`) where the impedance page gives
one number, which is why it is ambiguous at all.

**This is order-blocking on either reading**, because the order form asks for both
and nobody has established they can coexist. It belongs beside §7.4 as a second
written question:

> *"For a 4-layer 1.6 mm board on stackup JLC04161H-7628 with impedance control
> requested, is the 'Min. Via: 0.2mm' on your impedance capability page a via
> HOLE minimum or a via DIAMETER minimum, and can that order carry 0.15 mm
> drilled / 0.25 mm finished vias?"*

**Also MEASURED and worth carrying:** JLC's impedance page publishes the stackup
the archive names, and the numbers ADR-0004 solved against are the vendor's own —
top prepreg `7628×1` **0.21040 mm**, prepreg Dk **4.4**, outer copper **0.035 mm**.
§0's stackup row is correct against the source. Note however that JLC's *"No
requirement"* 4-layer 1.6 mm stackup has an **identical layer structure** — so
naming `JLC04161H-7628` buys the *guarantee*, not a different laminate. §0's
"REQUIRED, not a preference" is right about the constants and slightly overstated
about the physics.

---

## 3. FAB TIER — the paid option IS required; the r1 single-channel doubt is REFUTED

**Round 1 raised a doubt worth corroborating: a WebFetch summary reported JLC's
live 4-layer page giving 0.25/0.15 vias as the DEFAULT, i.e. the board might not
need the paid option. CORROBORATED ON A SECOND CHANNEL AND REFUTED.** The r1
summary confused *minimum capability* with *no-fee default*. Both are on the same
page, in different rows.

**MEASURED, my own fetch of the capabilities page:**

> *"① 0.2mm hole size with via diameter less than 0.45mm, will cost more.
> ② 0.15mm hole size with any size via diameter will cost more."*

**"0.15mm hole size with ANY size via diameter will cost more."** The board is
0.15 mm hole. The paid option is required. §0's conclusion stands.

The independent agent went further and read **JLC's own fee-table PNG** (embedded
in `/help/article/in-what-cases-will-there-be-charged-extra`, last updated
**2026-01-27**) rather than the prose around it — the WebFetch summariser had
reported the figures as absent:

| min via hole | min via diameter | extra cost |
|---|---|---|
| **0.15** | **0.25** / 0.3 | **Engineering fee $31.43 + $47.14 per m²** |
| 0.2 | 0.3 / 0.35 | $15.71 + $23.57 per m² |
| 0.25 | 0.35 / 0.4 | $15.71 + $15.71 per m² |
| 0.25/0.2 | 0.45 | **Free** |
| 0.3 | 0.4 | **Free** |

**The board lands in row 1 — the most expensive tier.** D-TIER treats fab tier as
a COST CEILING, and this is the ceiling's actual price: it was never named.

Verified against the board rather than the prose, item by item:

| §0 claim | board | verdict |
|---|---|---|
| 4 layers | `F.Cu / In1.Cu / In2.Cu / B.Cu`; In1 carries 0 track segments | ✅ MEASURED |
| vias 0.25 pad / 0.15 drill | **3446 of 3446** at exactly `size 0.25 / drill 0.15`. One class, no second | ✅ MEASURED |
| min hole-to-hole 0.3265 | reproduced from the drill files | ✅ MEASURED |
| 1 oz outer copper | not machine-stated anywhere in the archive; ADR-0004's `t = 0.035` is prose | ⚠️ INHERITED, unverifiable from the payload |
| stackup `JLC04161H-7628` | **`grep -c '(stackup' = 0`** — the board carries none | ⚠️ INHERITED (§7.5 already declares this) |
| surface finish | no `03_src/` file declares one; §0 states it as an order-time choice | ✅ honest, and correctly marked OWED |
| impedance control REQUESTED | **conflicts with the 0.15 mm drill — F-2** | ❌ |

**Track/space is NOT a reason for the tier, and §0 does not claim it is —
correctly.** MEASURED: the board's track widths are `{0.20 ×152, 0.30 ×4,
0.36 ×18, 0.40 ×25}`, minimum **0.20 mm** = 7.9 mil, against a multilayer no-fee
floor of **0.09/0.09 mm** (MEASURED, capabilities page). The board is over 2× the
free floor. The `min_track_width: 0.09` in the board's design settings is a
permission never exercised. No trace fee.

**Netclass observation, not a finding.** All four netclasses (`Default`, `RF50`,
`CTRL`, `PWR`) declare `via_diameter 0.6 / via_drill 0.3` — the *standard*-tier
via. Every via physically on the board is 0.25/0.15, placed by the generator, so
nothing inconsistent ships. But a human who opens this board and drops an
interactive via gets a 0.6/0.3 hole that the fence spacing was never solved for.
Cosmetic today; a trap at the next revision.

### F-4 — §0's two no-fee floor numbers are both wrong

**MEASURED.** ORDER_README §0 states:

> *"JLC's no-fee 4-layer tier (`jlc_4layer_standard`) floors are `min_via_drill`
> **0.30 mm** and `min_hole_to_hole` **0.50 mm**."*

Neither survives the vendor page:

| §0 claim | vendor, MEASURED | |
|---|---|---|
| no-fee `min_via_drill` 0.30 mm | free at **0.20 mm** drill provided pad ≥ 0.45 mm (fee table row 4) | ❌ REFUTED |
| no-fee `min_hole_to_hole` 0.50 mm | **via↔via 0.2 mm**, **pad↔pad 0.45 mm**. 0.50 mm is the *min NPTH size* and the *castellated* hole-to-hole, two unrelated rows on the same page | ❌ REFUTED |
| no-fee via **pad** 0.45 mm (in `fab_tiers.yaml` as 0.6) | **0.45 mm** confirmed | ✅ |

**The conclusion survives; one leg of the argument does not.** §0 argues two
things — that essentially every plated hole is under the standard-tier drill
minimum (**TRUE**, and it is what triggers the fee), and that *"the closest pair
is under the standard-tier hole-to-hole minimum as well"* (**FALSE** — 0.3265 is
63% ABOVE the published via↔via 0.2 mm floor). A reader checking the second claim
against the vendor page will find it does not hold and may discard the first with
it. It should be cut, not defended: the fee is triggered by the 0.15 mm drill
alone, which is the cleaner argument anyway.

`skills/kicad-pcb/references/fab_tiers.yaml` carries the same two wrong numbers
in `jlc_2layer_default` (`min_via_drill: 0.3`, `min_hole_to_hole: 0.5`, with an
inline comment calling 0.5 "JLC published"). **Propose (do not apply):** re-derive
every `min_hole_to_hole` in that file from the two published rows, and add
`min_hole_to_hole_pad` as a distinct key — a single scalar cannot represent a
vendor model that publishes two floors and no rule for the mixed pair, which is
the modelling gap that let the round-1 defect exist in the first place. Canon M6
says the page governs; the page has been read now.

### F-6 — the drill count crosses a published extra-charge threshold by 6.4×

**MEASURED** (my own fetch, article last updated 2026-01-27):

> *"9. Too Many Drilling Holes — For orders with over 150,000 drill holes per
> square meter, an extra cost will be applied."*

**DERIVED:** board outline from `Edge_Cuts.gm1` is **50.000 × 73.000 mm** =
3650 mm² = 0.003650 m². 3500 holes ÷ 0.003650 m² = **958,904 holes/m²** —
**6.39× the threshold.** (Using the MANIFEST's 3662.3 mm² outline: 955,679/m²,
6.37×. The conclusion is insensitive to which area is used.)

The fee amount is not published in text (it is in an unlocated image). This is a
COST item, not a manufacturability blocker — but §0 is explicitly *"the order
form, option by option"* and *"NONE OF THESE IS A DEFAULT"*, and a 6.4× overshoot
of a published surcharge threshold belongs in that table. A 3446-via fence is not
free.

**Checked and clear, so it is not rediscovered:** extra-charge item 5 is *"When
the ENIG area is over 30% of the total PCB dimension"*, and §0 recommends ENIG.
DERIVED: exposed metal is ~50 SMA barrel pads (π·0.95² × 50 = 141.7 mm²) plus the
QFN-24 and the passives (≈ 30 mm²) ≈ **175 mm² of 3650 mm² = 4.8%**. Vias are
tented (`F_Mask.gts` is 7.5 kB — it carries pads, not 3446 via openings), so they
do not count. Well under 30%. No ENIG surcharge.

---

## 4. HOLE-TO-COPPER — measured against the vendor's floors, and CLEAR

The round-1 defect was a declared floor set below the vendor's. I looked for the
same shape in the adjacent geometry, because `min_hole_clearance` in this board's
design settings is **0.15 mm** and JLC publishes higher numbers than that.

**MEASURED** — own geometry pass, every drilled hole against all 199 track
segments, same-net excluded (a track landing on its own pad is not a clearance):

| vendor rule (MEASURED, capabilities page) | board worst, nominal | at max material | margin |
|---|---|---|---|
| **PTH to Track — min 0.28 mm** (0.35 recommended) | **0.4774** (`J_ANT4.5` vs `SW_V1`) | **0.4124** | **+0.132 vs min, +0.062 vs recommended** ✅ |
| **Via hole to Track — 0.2 mm** | **0.2522** (`via@(40.2,55.8)` `SW_V1` vs `SW_V4`) | **0.2153** (at track width +20%) | **+0.015** ✅ |
| Hole Position Tolerance ±0.05 mm | — | — | INHERITED, not modelled here |

**Both clear, including the recommended PTH figure, and including the max-material
case.** The board's 0.15 mm `min_hole_clearance` is again a permission never
exercised — no hole comes anywhere near it. **Nothing to report here, and I am
saying so plainly rather than manufacturing a second finding out of a floor that
is loose on paper and tight nowhere in copper.**

**One genuine residual exposure, MEASURED verbatim from JLC's own tolerance
article** (`/help/article/difference-and-tolerance-explanation-between-via-and-pad-holes`,
last updated 2025-04-24). It confirms both halves of the archive's max-material
model — *"pad holes are controlled for diameter … +0.13mm/-0.08mm"* and *"the
diameter of via holes is not controlled"* — and then says:

> *"In actual production, **the hole size may be adjusted to combine closely
> spaced holes** to reduce the number of drills and improve work efficiency.
> Alternatively, **the hole size might be reduced due to limited space between
> lines and widths**."*

**The archive's max-material model assumes via growth = 0.000 mm. The vendor
disclaims control of that dimension in the same breath as reserving the right to
CHANGE it, specifically to merge closely spaced holes.** With 54 via↔PTH pairs
under 0.45 mm and 3446 vias on an 0.8 mm lattice, "closely spaced holes" is a
description of this board. The likely consequence is benign — every candidate for
merging is GND-to-GND, into an SMA ground barrel that is itself GND — but "via
growth = 0" is an assumption the vendor explicitly does not underwrite, and it is
the same *nominal-only-margin* shape as the round-1 finding one level further out.
It belongs in the §7.4 written question as a third clause: *do you resize or merge
vias on this board, and if so, against what spacing?*

---

## 5. BOM / CPL / STOCK

### Provenance — CLEAN

**MEASURED.** `fab/bom.csv` sha256 `12308e84…`, `fab/cpl.csv` sha256 `77745795…`
— **distinct**, so the hand-copy fingerprint (identical sha256 under both names,
as on another board's v1.7) is absent. `export_jlc_package.py` at `628ee3d4`
writes `out/"bom.csv"` and `out/"cpl.csv"` directly (lines 340–341); the legacy
`bom_jlc.csv`/`cpl_jlc.csv` are read only for LCSC carry-over. `06_build/fab/` and
`06_build/staging/fab/` are byte-identical for both files. ✅

**Denominators are non-zero and I checked them rather than the verdicts:**

| gate | denominator | MEASURED? |
|---|---|---|
| `A-STOCK` | `graded_lines 11 / total_lines 11`, `uncoded_lines 0`, `zero_coverage null` | ✅ real denominator, not the empty set |
| `M-BOM` leg A/B | 28 coded refdes vs `circuit.json` | ✅ |
| `M-BOM` leg C (semantic) | **7 of 11 rows** value-graded | ⚠️ partial, and declared |
| `P-FACT` | 7 of 8 assertions reached a comparison, 1 UNREACHED and NAMED | ✅ honest partial |
| `F-ECHO` | 11 coded lines staged for the post-upload diff | ✅ |
| **MOQ / `minPurchaseNum`** | **1 of 11** — only `C504007`, via `verification/jlc_catalog_C504007.json` | ❌ **F-5** |

### F-5 — ORDER_README claims a MOQ artifact that does not exist

**MEASURED.** §1 states:

> *"Live LCSC stock was re-read on 2026-07-31 and every coded line clears the
> build quantity; the count and **the multiple** are in
> `verification/stock_check.json` and `MANIFEST.txt`."*

`grep -rin "minpurchase\|multiple\|moq\|min.order"` across the **entire** staging
tree returns exactly two hits: this sentence, and `verification/jlc_catalog_C504007.json`
(`"minPurchaseNum": 1`, `"preMinPurchaseNum": 24`) — a cached page for **one**
part. `stock_check.json` has no MOQ field of any kind; its per-line keys are
`lcsc, designators, qty, status, stock, type, mpn`. **The multiple is not in the
file the README says it is in**, for 10 of 11 lines. This is #73 surfacing not as
a missing check but as a document asserting a check that was never run.

### F-1 — `C25744` cannot be bought at 20, and `A-STOCK` says PASS

**MEASURED, first-hand, all 11 lines**, by POSTing each code to JLC's own
`selectSmtComponentList` endpoint — the same store the parts pages render from,
and a different method from `jlc_stock_check.py`'s catalog read (canon M1):

| LCSC | designators | need (5 bd) | stockCount | **minPurchaseNum** | canPresale | lib | verdict |
|---|---|---|---|---|---|---|---|
| C1525 | C_SW1 | 5 | 46,106,824 | 1 | +34.5M | base | OK |
| **C25744** | **R_PD1..R_PD4** | **20** | **30,949** | **779** | **−6,175,510** | base | **FAIL** |
| C15849 | C_SW2 | 5 | 14,327,780 | 1 | +9.8M | base | OK |
| C25091 | R_T1,R_T2 | 10 | 1,713,109 | 1 | +1.36M | base | OK |
| C1779 | C_BULK | 5 | 3,548,653 | 1 | +2.99M | base | OK |
| C137864 | R_S1..R_S4 | 20 | 73,417 | 1 | +69,160 | expand | OK |
| C137948 | R_LED | 5 | 743,754 | 1 | +573,101 | expand | OK |
| C3716677 | FB_3V3 | 5 | 5,838 | 1 | +5,681 | expand | OK |
| C504007 | J_ANT1..8, J_RX1..2 | 50 | 22,707 | 1 | +17,625 | expand | OK |
| C2286 | LED_ST | 5 | 7,333,748 | 1 | +6.67M | base | OK |
| C5121458 | U_SW | 5 | 1,284 | 1 | +1,282 | expand | OK |

**`C25744` needs 20 and its minimum purchase is 779 — 39× the requirement.** Its
`canPresaleNumber` is **−6,175,510**: the catalog stock of 30,949 is already
oversubscribed by six million, which is exactly why the minimum jumped. This is
the #73 blind spot realised: `jlc_stock_check.py` reads `stockCount`, sees 31,308,
prints `OK … stock=31308`, and the archive's `A-STOCK verdict=PASS, 11/11 coded
lines at >= 5x qty` is literally true and operationally wrong.

Ten of eleven lines pass MOQ. **The denominator is 11 and the failure count is 1.**

**Severity, stated honestly rather than inflated.** This is not a part that cannot
be had — it is a part that cannot be had *at the modelled quantity*. Buying 779
0402 resistors at $0.0115 is ~$9, so the financial exposure is trivial **on this
line**. What is not trivial is that no gate in the archive can see the condition,
and the identical condition on `C5121458` (RF switch, $6.09/pc, 1,284 in stock)
would be a $4,700 surprise. The check is what is missing, not the nine dollars.
`order_verdict` stays **DO-NOT-ORDER**; `BLOCKED-SOURCING` is not the right key
because the part is purchasable, just not as budgeted.

**Verified alternative, MEASURED on the same endpoint:** `C60490`
(YAGEO **RC0402FR-0710KL**, 10 kΩ ±1% 62.5 mW 50 V 0402 — identical spec, and the
same RC0402 family already on this BOM at `C137864`/`C137948`): stock
**8,740,134**, `minPurchaseNum` **1**, `canPresaleNumber` **+4,785,981**. The cost
is that it is `expand` where `C25744` is `base`, so the swap trades a hard MOQ
wall for one extended-part setup fee. **This is a BOM change and therefore a new
release, not an edit.**

**Propose (do not apply):** `jlc_stock_check.py` must read `minPurchaseNum` and
grade `need <= max(stockCount_ok, minPurchaseNum satisfied)`, emitting the
required purchase quantity per line; and it needs a known-bad fixture — `C25744`
itself is one today, and it will stay one as long as `canPresaleNumber` is
negative.

### M-BOM SEMANTIC — the archive's leg C is an MPN decode, not a catalog resolution; I supplied the missing leg

**MEASURED, by reading `bom_source_check.py`'s own header.** Leg C resolves a
row's value in this order: *the BOM's own MPN column → the vendored `part.yaml`
directory name → the vetted LCSC ledger*, then decodes the EIA/RKM encoding and
compares to the label. **The comparison is OFFLINE and the LCSC code is never
resolved against the vendor catalog.** So leg C catches "MPN right, label wrong".
It structurally **cannot** catch "LCSC code does not correspond to its MPN" — and
the R30/#49 precedent is exactly a code whose catalog identity differed from
everything written beside it. Checker and checked share the row.

Coverage is **7 of 11** (`bom_source_check.txt`: *"coverage leg C: 7/7 R/C rows
value-graded (11 BOM rows seen)"*). The four ungraded are the non-R/C rows —
`C3716677` (ferrite), `C504007` (SMA ×10), `C2286` (LED), **`C5121458` (the RF
switch, which is the board's entire function)** — where the Comment *is* the MPN
and the check degenerates to a string comparing itself.

**So I ran the missing leg: all 11 codes resolved to catalog identity.**

| LCSC | catalog MPN | catalog value / rating | BOM label | |
|---|---|---|---|---|
| C1525 | CL05B104KO5NNNC | 100 nF ±10% 16 V **X7R** 0402 | 100nF | ✅ |
| C25744 | 0402WGF1002TCE | 10 kΩ ±1% 62.5 mW 50 V | 10kΩ | ✅ |
| C15849 | CL10A105KB8NNNC | 1 µF ±10% 50 V **X5R** 0603 | 1uF | ✅ |
| C25091 | 0402WGF2200TCE | 220 Ω ±1% 62.5 mW | 220Ω | ✅ |
| C1779 | CL21A475KAQNNNE | 4.7 µF ±10% 25 V **X5R** 0805 | 4.7uF | ✅ |
| C137864 | RC0402JR-0747RL | 47 Ω **±5%** 62.5 mW | 47Ω | ✅ (J = 5%, MPN-consistent) |
| C137948 | RC0402FR-07680RL | 680 Ω ±1% 62.5 mW | 680Ω | ✅ |
| C3716677 | BLM21SP601SN1D | **600 Ω @ 100 MHz**, DCR 60 mΩ, 2.3 A, 0805 | BLM21SP601SN1D | ✅ |
| C504007 | KH-SMA-KE-Z | SMA jack, board-side, inner-bore, positive pin, **Plugin**, 5 pins | KH-SMA-KE-Z | ✅ |
| C2286 | KT-0603R | red 615–630 nm, Vf 1.8–2.4 V, 20 mA, 0603 | KT-0603R | ✅ |
| C5121458 | PE42482A-X (pSemi) | **SP8T 10 MHz–8 GHz**, 2.2 dB IL, 85 dB iso, 2.3–5.5 V, QFN-24 4×4×0.85 | PE42482A-X | ✅ |

**11 of 11 match. Zero identity defects. No R30-class mislabel on this board.**
Observations, not findings: `C1525` at 16 V is the thinnest voltage margin on the
BOM, and both bulk caps are X5R rather than X7R — neither contradicts the BOM,
which declares no dielectric.

**Propose (do not apply):** leg C's declared coverage should print as **7/11 with
the 4 ungraded refdes NAMED**, the way `P-FACT` names its 1 unreached assertion.
`7/7` reads as complete and is a denominator over the subset the check happens to
handle.

### C504007 — the "went to zero" report is REFUTED

**MEASURED.** `stockCount 22,707`, `minPurchaseNum 1`, `canPresaleNumber
**+17,625**` (positive — presale capacity available, not spoken for),
`leastPatchNumber 2`, `lossNumber 0`. LCSC retail independently shows 14,948 in
stock, MOQ 1. Our 50 pieces clear by 454×. The archive's own cached
`jlc_catalog_C504007.json` (stockCount 22,708) is **corroborated to within one
unit of ordinary drift**. The earlier "went to zero / next reel already spoken
for" claim does not reproduce on either product-page channel; a search snippet
claiming "2,366 units" was encountered and **REFUSED under Q-SNIPPET**. The
archive's number is the right one.

### F-7 — §2a names a real risk and prescribes an action that does not exist

**The risk is real and correctly measured.** MEASURED and reproduced: 50 plated
1.400 mm holes across ten `KH-SMA-KE-Z`, **F.Paste on none of them**, all ten on
the CPL as `top`. No reflow profile solders a 1.4 mm barrel through a stencil with
no aperture. §2a is right that this is the board's entire product.

**The remedy is wrong.** §2a says *"THROUGH-HOLE (PLUG-IN) ASSEMBLY MUST BE
SELECTED AT ORDER TIME … it is one checkbox."* JLCPCB's assembly FAQ (MEASURED,
last updated 2025-11-24) says:

> *"Now JLCPCB can support through-hole components by offering wave soldering
> services … The part's assembly type marked with **'wave soldering'** in our
> assembly parts library will be assembled manually."*
> `Ordering process:` ***"The same as SMT assembly."***
> `Cost:` *"$3.5 hand-soldering labor fee + $0.0173 manual assembly fee per joint"*

**There is no through-hole checkbox.** The gate is per-part: the library entry must
carry the wave-soldering flag. The independent agent reports `C504007`'s assembly
type reads **Wave Soldering**, which is the good outcome — but the archive's own
evidence (`assemblyProcess: null` in `jlc_catalog_C504007.json`) shows the field
the archive queried does not carry it, which is why §2a could not confirm it.

The human gate must therefore be re-aimed, not removed: **confirm in the uploader
that `C504007` resolves with wave/manual soldering and that 50 THT joints × 5
boards are priced** (DERIVED: 250 joints × $0.0173 + $3.50 ≈ **$7.83**, plus the
$0.0017/joint SMT line). §2a's *"one checkbox"* framing will send a human looking
for a control that is not on the form, and the most likely outcome of not finding
it is proceeding — which is exactly the failure §2a exists to prevent.

### F-8 — `kicad-cli pcb drc` exits 0 by construction; the MANIFEST cites its exit code as evidence

**MEASURED.** The known-bad fixture in §1 produced **2 `hole_to_hole` violations
and RAW EXIT 0**. `kicad-cli pcb drc --help` shows why: there is a
`--exit-code-violations` flag ("Return a nonzero exit code if DRC violations
exist") and **the repo's gate does not pass it** — not in
`skills/pcb-design/templates/03_src/rebuild_all.sh:185`, not in `rebuild_reuse.sh:91`,
not in `tsx_to_board.sh:256`. `hole_to_hole` is severity `warning` in this board's
config (29 of 62 rule severities are non-error), so it could not have set an exit
code anyway.

The MANIFEST records `DRC … 0 violations / 0 unconnected / 0 parity … RAW EXIT 0`.
**The classified counts are the evidence and the archive does report them — so the
archive is honest.** But `RAW EXIT 0` sits in that block as though it were
corroboration, and it is not: it is the same *exit-0-by-construction* pattern the
briefing already flags for `fence_apertures.py`, in the repo's single most-cited
gate. A board with sub-floor hole spacing exits 0.

**Propose (do not apply):** add `--exit-code-violations` to every `kicad-cli pcb
drc` gate invocation in `skills/`, and until then annotate the MANIFEST line the
way `fence_apertures` is annotated — *its exit code is not evidence; the
classified counts are*.

---

## 6. WHAT I CHECKED AND FOUND CLEAN

Stated so the next round does not re-measure it:

- **DRC**, unpiped, on a copy **outside the repo**: `0 violations / 0 unconnected
  / 0 parity`, RAW EXIT 0. Both halves classified; the unconnected half is
  genuinely zero, not summarised. MEASURED.
- **Gerber upload payload**: `pluto_rx2_8way_v2_gerbers.zip` holds 13 files and
  every one is **bit-identical** to its loose counterpart in `fab/`. No stale-zip
  risk; what gets uploaded is what was measured. MEASURED (`unzip` + `cmp`).
- **Hole census**: 3500 holes, 3446/50/4, single via class. MEASURED from drills.
- **`fence_apertures.py`** rerun with the lattice pitch as `argv[2]` (0.8 mm —
  without it, it tracebacks): **0 GAP lines** over 3433 PCB_VIA GND + 40 PTH GND
  = 3473 fence elements, bound 1.191 mm. Its exit code is not evidence and I did
  not use it. MEASURED.
- **Via tenting**: `F_Mask.gts` is 7.5 kB — pads only, no via openings. Vias are
  tented, which is both the ENIG-area answer and the correct choice for a
  stitched RF ground. MEASURED.
- **CPL**: 27 placements, all `top`, `bottom` empty; 11 BOM lines, 0 without LCSC.
  MEASURED.
- **`policy_audit`**: FAIL=1 (A-POP MANIFEST-UNDECLARED, an artefact of grading
  the project because `07_releases/` is empty), HUMAN=6, N-A=7, PASS=31.
  INHERITED — I did not re-run it, and it is not in my lens.

---

## 7. DISPOSITION

**`design_verdict: DEFECTIVE`** — not for the reason the archive gives. The
archive's own reason (no fresh red-team round has read this copper) is honest and
correct, and this review is one of the lenses closing it. But the key stays
DEFECTIVE on findings of mine: **F-1** puts a BOM line beyond purchase at the
required quantity with every gate green, and **F-2** puts two declared order
options in possible mutual contradiction. Neither is copper — the copper measures
clean, including the round-1 fix — but both are the shipped release being wrong
about what can be ordered.

**`order_verdict: DO-NOT-ORDER`** — F-1 and F-2 are each sufficient. §7.4's vendor
question remains genuinely open and now has two companions (impedance-vs-via-drill;
JLC's reserved right to resize or merge vias). Not `BLOCKED-SOURCING`: `C25744` is
purchasable, at 39× the quantity, and one verified drop-in exists.

**Blocking, in the order I would work them**

| # | finding | evidence |
|---|---|---|
| **F-1** | `C25744` `minPurchaseNum` **779** vs need **20**; A-STOCK PASSes | MEASURED, JLC API, 11/11 denominator |
| **F-2** | impedance control publishes **Min. Via 0.2 mm**; board drills 0.15 mm; both declared in §0 | MEASURED, 2 channels |

**Not blocking, but shipped wrong**

| # | finding | cost |
|---|---|---|
| **F-3** | MANIFEST `PTH<->PTH` row is intra-footprint only — **1.6934/1.5634**, not 2.1921/2.0621 | number wrong, verdict unaffected (3.5× the 0.45 floor) |
| **F-4** | §0's no-fee floors (0.30 drill, 0.50 hole-to-hole) both refuted by the vendor page; same numbers in `fab_tiers.yaml` | conclusion survives, one argument leg is false |
| **F-5** | §1 claims MOQ ("the multiple") is in `stock_check.json`; it is in no file for 10 of 11 lines | asserts a check never run |
| **F-6** | 958,904 drill holes/m² = **6.39×** JLC's 150,000/m² surcharge threshold; unnamed | unpriced cost, plus the row-1 via fee $31.43 + $47.14/m² |
| **F-7** | §2a's "one checkbox" does not exist — *"Ordering process: The same as SMT assembly"* | human sent to look for a control that isn't there |
| **F-8** | `kicad-cli pcb drc` lacks `--exit-code-violations`; 2 violations → exit 0, proved | exit code cited as evidence in the MANIFEST |

**Skill changes are PROPOSED, never applied** (§1 F-3, §3 F-4, §5 F-1/M-BOM, §5
F-8). Nothing in `04_kicad/` or `07_releases/` was touched; the only file this
review wrote is itself.

---

*Lens: fab / orderability, round 2. Board `pluto-rx2-8way-v2` at
`06_build/staging/`, git `2a65b60b` (dirty in `skills/`, per MANIFEST). Measured
2026-07-31. Vendor pages read the same day; JLC publishes no change date on the
capabilities page, and the extra-charge and impedance pages carry 2026-01-27 and
no date respectively.*
