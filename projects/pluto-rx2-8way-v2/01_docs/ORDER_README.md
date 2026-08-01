# pluto-rx2-8way-v2 v1.0 — ORDER README

**8-way RF receiver splitter / switch matrix.** 4 copper layers, fab tier
`jlc_4layer_advanced`. Board outline, hole census and every gate count are in
`MANIFEST.txt`, which is their one home; this file states the ORDER DECISIONS,
the human gates, and what is not green.

```
design_verdict: DEFECTIVE
order_verdict:  DO-NOT-ORDER
```

**THIS TREE IS STAGED, NOT SEALED.** It lives in `06_build/staging/` and has
NOT been written into `07_releases/`. Both keys are from the closed vocabulary
(`design_verdict: SOUND|DEFECTIVE`, `order_verdict:
ORDER|DO-NOT-ORDER|BLOCKED-SOURCING`); §1 gives the reason for each.

**WHAT THIS REVISION CHANGED, AND WHAT IT DID NOT.** This archive was rebuilt
on 2026-07-31 through the board's own `03_src/rebuild_all.sh` after **one BOM
line was fixed at source** (`C25744` -> `C60490`, §1 — the outgoing part cannot
be bought at our quantity and no gate in this repo could see that). **The
copper did not move, and that is MEASURED, not asserted:** the four copper
gerbers and both drill files are multiset-identical as command streams apart
from `%TF.CreationDate`, `cpl.csv` is byte-identical, the board's via / segment
/ footprint sets have symmetric difference 0, and the `.kicad_sch` and `.net`
are UUID-masked-identical. Five RF instrument outputs are byte-identical to the
previous staging. `MANIFEST.txt`'s **THE REBUILD DELTA** block classifies all
of it item by item.

**So the round-1 RF verdict and the schematic/netlist verdict remain verdicts
about THIS board.** What is genuinely new is one BOM row and the documents —
including **five corrected numbers and five withdrawn claims** that were
checkable and wrong (§8c, §7 item 2, §0, §2a).

**THE ARCHIVE STILL SHIPS NO RED-TEAM REVIEW DOCUMENTS**, and A-EVID still
FAILS on exactly those four names. That remains deliberate: the earlier lens
rounds graded copper this board has left, and promoting one revision's review
as another revision's verdict is the adjacent-property error. §7 item 3.

---

## 0. THE FAB OPTIONS — NONE OF THESE IS A DEFAULT

**Ordered at JLC's standard 4-layer defaults this board is unmanufacturable,
and that is arithmetic, not caution.** The hole census it rests on — via count
and geometry, PTH and NPTH counts, and the minimum hole-to-hole edge-to-edge
both NOMINAL and AT MAX MATERIAL — is stated once, in `MANIFEST.txt`'s `fab:`
block, and is not retyped here.

**The trigger is the 0.15 mm DRILL, and that is the whole argument.** JLC's
capabilities page footnote ③, read verbatim 2026-07-31 on two channels:

> *"0.15mm hole size with any size via diameter, and 0.2mm or 0.25mm hole size
> with via diameter less than 0.45mm, will cost more."*

All 3446 vias on this board are 0.15 mm hole. The paid option is not an
optimisation; it is the order.

**THE PREVIOUS REVISION OF THIS SECTION GAVE A SECOND ARGUMENT AND BOTH ITS
NUMBERS WERE WRONG.** It said *"JLC's no-fee 4-layer tier floors are
`min_via_drill` 0.30 mm and `min_hole_to_hole` 0.50 mm"* and concluded that the
closest hole pair was under the standard-tier hole-to-hole minimum too.
MEASURED against the vendor page:

| the claim | the page | |
|---|---|---|
| no-fee `min_via_drill` **0.30 mm** | free at **0.20 mm** drill provided the pad is >= **0.45 mm** (fee table row 4) | REFUTED |
| no-fee `min_hole_to_hole` **0.50 mm** | **via<->via 0.2 mm**, **pad<->pad 0.45 mm**. 0.50 mm is the *Min. Non-plated hole SIZE* and the *castellated* hole-to-hole — two unrelated rows | REFUTED |

So the board's tight class at **0.3265 mm** is **63 % ABOVE** the real
via-to-via floor, not under it. **The conclusion survives and the second
argument leg is deleted rather than defended** — a reader who checks that leg
against the vendor page will find it does not hold, and may discard the sound
first leg with it. `skills/kicad-pcb/references/fab_tiers.yaml` carries the same
two wrong numbers in `jlc_2layer_default`; that is a SKILL fix and is PROPOSED,
not applied, in §9.

### The line to put on the order, verbatim

> **ADVANCED option REQUIRED: min via 0.25/0.15 mm** (PE42482A-X QFN-24 at
> 0.50 mm pitch — its 0.300 mm signal lands admit a via PAD of at most 0.25 mm
> at 0.2 mm clearance to the neighbouring land, and JLC's own rule that via
> diameter exceed via hole by ≥ 0.1 mm then forces a ≤ 0.15 mm drill; both
> no-fee rows need a 0.40–0.45 mm via pad, which does not fit).
> **4-layer JLC04161H-7628, IMPEDANCE CONTROL REQUESTED.**

That sentence is not written here. It is generated-in-place from
`03_src/rules/nets.yaml`, which is its one home, and it fills the `<reason>`
slot in the `order_readme:` field `skills/kicad-pcb/references/fab_tiers.yaml`
carries for this tier.

**THE REASON CLAUSE WAS RE-DERIVED ON 2026-07-31 BECAUSE THE PREVIOUS ONE WAS
WRONG TWICE, AND IT IS THE SENTENCE THAT JUSTIFIES A PAID OPTION.** It read
*"at the standard-tier 0.30 mm drill the adjacent-pin hole-to-hole gap is
0.50 − 0.30 = 0.20 mm against a 0.50 mm floor, so no escape via fits."*

- **The floor is not 0.50 mm** (above): the real via↔via floor is **0.2 mm**,
  so 0.20 would sit AT it, not under it. The sentence proved nothing.
- **It is the wrong quantity.** MEASURED on the shipped board: the tightest
  via↔via HOLE gap anywhere within 4 mm of U_SW is **0.6017 mm**. No two
  adjacent 0.5 mm-pitch pins both carry a via, so hole-to-hole never binds
  here. The escape is via-in-pad on four numbered lands — pad 8 (`3V3`), pad 11
  (`SW_V3`), pad 18 (`GND`), pad 25 (EP) — plus the EP thermal cross.

**The correct derivation, MEASURED, reaching the same tier.** U_SW's signal
lands are **0.300 × 0.600 mm on a 0.500 mm pitch**, so adjacent land EDGES are
0.200 mm apart. A via centred in a land must clear the neighbouring land by
this board's `default_clearance` **0.2 mm**:

| via pad | clearance to the neighbouring land | |
|---|---|---|
| **0.25 mm** | **0.225 mm** | **fits** |
| 0.40 mm | 0.150 mm | fails 0.2 |
| 0.45 mm | 0.125 mm | fails 0.2 |
| 0.60 mm (the netclass value) | 0.050 mm | fails everything |

So 0.25 mm is the largest via PAD the land admits — and JLC's own footnote ①,
*"Via diameter should be 0.1mm(0.15mm preferred) larger than Via hole size"*,
then forces the HOLE to ≤ **0.15 mm**, which is fee-table row 1. **Both no-fee
rows require a 0.40–0.45 mm via diameter, and neither fits a 0.300 mm land.**
The paid option is forced by the LAND WIDTH through the vendor's own
diameter-vs-hole rule. **Conclusion unchanged; the argument is now true.**

### The order form, option by option

| option | value | why this value and not the default |
|---|---|---|
| Layers | **4** | F.Cu = RF only; **In1.Cu = the SOLID unbroken RF reference**, excluded from routing; In2.Cu = power/signal; B.Cu = GND pour + stitching |
| **Stackup** | **JLC04161H-7628**, 1.6 mm | **REQUIRED, not a preference.** Every published RF number on this board is solved for THIS laminate: top prepreg **h = 0.2104 mm**, **Dk = 4.4**, outer copper **t = 0.035 mm**. From those, ADR-0004 derives RF50 = **0.36 mm** for 51.24 Ω CBCPW and the fence bound λ_pp/20 = **1.1910 mm**. A substituted stackup voids the whole constant set — do not accept one without re-running `03_src/gcpw_constants.py` |
| Via / process tier | **`jlc_4layer_advanced`** — 0.25 mm pad / 0.15 mm drill, **ADVANCED small-via option REQUIRED** | see the arithmetic above |
| **Via protection** | **RESIN-FILLED AND CAPPED (POFV / plugged-and-plated-over) — REQUIRED, NOT OPTIONAL** | **TEN vias have their drilled hole inside a SOLDERABLE LAND of `U_SW`, and every one of them is OPEN AT THE TOP.** This is the only option on this form that was never asked for and had to be; the arithmetic and the vendor citation are immediately below |
| **Impedance control** | **REQUESTED** | the board's product IS impedance: nine equal-radius 14.00 mm GCPW arms whose relative phase is the deliverable |
| **Copper weight** | **1 oz (35 µm) outer** | this is the `t = 0.035 mm` the constant set was derived at (ADR-0003, ADR-0004). 2 oz changes `eps_eff` and the published phase table |
| **Surface finish** | **ENIG recommended — and this is an ORDER-TIME CHOICE, not a project decision** | Stated as a choice because it is one: **no `03_src/` file declares a finish**, and inventing one here would put a fabricated obligation into a release. The engineering basis for the recommendation is measured: U_SW is a QFN-24 at **0.50 mm** pitch with a 2.750 × 2.750 mm exposed pad, where HASL's uneven surface costs land flatness; and the CBCPW derivation in ADR-0004 is explicitly for a **BARE** line, so the finish should be the thin, flat one. **OWED to v-next:** declare the finish in `03_src/` so it stops being decided at the order screen |
| Solder mask / silk | any; mask over the RF arms is **not** modelled | ADR-0004's tuple ends `… BARE`. Mask over a 0.36 mm line perturbs `eps_eff` by ~1 %; it is inside the 4.2–4.6 Dk window the fence bound already spans (1.2190 / 1.1910 / 1.1648 mm) but it is not separately budgeted |
| Quantity | **5** | `build_quantity: 5` in `03_src/rules/assembly.yaml`; A-STOCK grades every coded line against 5× its per-board quantity |
| Panelisation | none | single board, 50.000 × 73.000 mm outline (the 50.10 × 73.10 figure some earlier text carried is the bounding box INCLUDING the 0.1 mm Edge.Cuts stroke) |

### What the paid options COST — named, because §0 claims to be the order form

**Neither of these was in any earlier revision of this file, and the fab tier is
a COST CEILING under canon D-TIER — a ceiling with no price on it is not a
ceiling.** MEASURED from JLC's extra-charge article (`Last updated on Jan 27,
2026`), whose two fee tables are IMAGES; a second agent downloaded and read them
directly rather than trusting a summariser.

**1. The small-via fee — the board lands in the MOST EXPENSIVE row.**

| min via hole | min via diameter | extra cost |
|---|---|---|
| **0.15** | **0.25** / 0.3 | **Engineering fee $31.43 + $47.14 per m²**  <- THIS BOARD |
| 0.2 | 0.3 / 0.35 | $15.71 + $23.57 per m² |
| 0.25 | 0.35 / 0.4 | $15.71 + $15.71 per m² |
| 0.25/0.2 | 0.45 | **Free** |
| 0.3 | 0.4 | **Free** |

DERIVED for this board: outline **50.000 × 73.000 mm = 0.003650 m²**, so
`$31.43 + $47.14 × 0.003650` = **$31.60**. The per-area term is 17 cents; the
engineering fee is the whole cost, and it is per ORDER, not per board.

*(Vendor inconsistency, recorded so it is not read as our error: the `Free` row
reads `0.25/0.2 | 0.45` while its own Remark says `0.25mm or 0.35mm`. One of
them is a JLC typo and the page does not say which. It does not touch us —
0.15 is unambiguously row 1 either way.)*

**2. The drill count crosses a published surcharge threshold by 6.4×.**

> *"for orders with over 150,000 drill holes per square meter, an extra cost
> will be applied."*

DERIVED: **3500 holes / 0.003650 m² = 958,904 holes/m² = 6.39× the threshold.**
A 3446-via fence is not free.

The fee table gives **$0.63 per (m² · 10,000 drill holes)** for 4-32 layers,
with `Holes numbering less than 10,000 will be calculated as 10,000` and
`If the price is $1.57 or below, it will be waived`. On a 0.003650 m² board
every reading of that formula we can construct lands at fractions of a cent —
`0.63 × 0.003650 × (10000/10000) = $0.0023` — i.e. **under the waiver floor**.
**So the money is probably nil and we are not claiming otherwise.** What is NOT
in doubt is the note in the same table:

> *"Expedited production is not supported for orders over 150,000 drill holes
> per square meter."*

**This board cannot be ordered on an expedited build.** That is a schedule
fact, it is certain, and it was named nowhere before this revision.

**3. THE VIA-PROTECTION FEE — A COST LINE THIS ORDER HAS NEVER CARRIED, AND THE
ONE PAID OPTION THAT IS AN ELECTRICAL REQUIREMENT RATHER THAN A GEOMETRY ONE.**

**Ten vias have their DRILLED HOLE inside a solderable land of `U_SW`, the SP8T
RF switch. All ten are open at the top.** MEASURED three ways that do not share
a method (canon M1): `pcbnew` pad/via geometry, an independent text parse of the
shipped gerbers, and the footprint source.

| where | count | measured |
|---|---|---|
| **Exposed pad (pad 25, `GND`)** | **7** | holes at (41.000,49.000) (40.300,48.300) (41.700,48.300) (40.300,49.700) (41.700,49.700) (41.010,47.730) (42.350,48.930), inside the 2.750 × 2.750 mm land. **6 of the 7 sit FULLY under a printed paste window; the 7th is clipped by a window edge across 33 % of its hole diameter.** None has paste-free cover |
| **Pad 8 — `VDD`, the 3.3 V supply** | **1** | 0.250 mm annulus dead-centre in a **0.300 × 0.600 mm** land: **0.025 mm** of copper rail either side |
| **Pad 11 — `V3`, a digital control input** | **1** | identical geometry, dead-centre |
| **Pad 18 — `GND`** | **1** | centre 0.050 mm off the land centre; annulus overhangs the land edge by 0.025 mm |

**"Open at the top" is MEASURED FROM THE SHIPPED GERBERS, not inferred.**
`F_Mask.gts` carries **one** aperture over the exposed pad — `R(2.7500,2.7500)`
at (41.0000, −49.0000) — **with no dams and no via-tenting islands inside it**,
and one roundrect over each of pads 8/11/18 centred exactly on their vias.
`B_Mask.gbs` has **ZERO flashes within 3.2 mm of `U_SW`**, so the bottom is
fully mask-tented. **The vias are therefore tented from BELOW ONLY, and the
solder side is the open side.**

**THE BOARD DECLARED THESE VIAS TENTED THREE SEPARATE TIMES AND IS FABRICATED
OPEN ANYWAY.** `(setup … (tenting (front yes) (back yes)))` in the `.kicad_pcb`;
`(tenting (front yes) (back yes))` on the individual pad-8 and pad-11 vias in
the promoted routing chain `03_src/route/r5.kicad_pcb`; and
`fab_tiers.yaml`'s `jlc_4layer_advanced: via_in_pad: true  # POFV: resin-filled
+ capped, paid option`. **A per-via tenting flag cannot survive the mask
aperture of the pad the via sits in** — the pad's opening removes the mask over
the via regardless — and nothing in this pipeline compares the two. The
`.gbrjob`, which is the one machine-readable place KiCad would carry the
via-protection declaration to a fab, **is absent from the gerber zip** (13
files, no job file — §7 item 6's sibling). So all three declarations stop at the
repo boundary.

**WHAT THE PART REQUIRES — this is the vendor's wording, not our preference.**
pSemi **Application Note 62**, *Soldering Guidelines for Mounting
Bottom-terminated Components*, DOC-78164-1.01 (11/2025), `psemi.com/pdf/app_notes/an62.pdf`:

> *"pSemi recommends plugging any thermal vias in the board exposed pad area. If
> plugging the via is not feasible, tenting with solder mask is another viable
> option. To determine the most effective plugging process, work with your PCB
> supplier."*

**As drawn the board does NEITHER.** Not plugged, and tented only on the face
the solder does not come from. The PE42482A-X datasheet (DOC-75785-4) itself
contains **no** via, paste, plugging or stencil guidance at all — term counts
over the full text are zero for *via / stencil / aperture / solder / plating /
plugged / filled* — so AN62 is the authority by part class, and it is the only
one there is.

**WHY IT MATTERS HERE AND NOT ONLY AS HOUSEKEEPING.** Datasheet Table 8's last
row reads *"Exposed pad: ground for proper operation"* — **the EP is the RF
ground return for all nine ports, not a heat sink** (thermally it is a
non-event: 0.66 mW, ΔT = 0.042 °C). A starved or voided EP joint is an RF
defect. AN62 caps post-reflow EP voiding at **25 % per IPC-A-610** and
recommends X-ray verification.

**THE ARITHMETIC, at AN62's own stencil recommendation** (*"typical 0.125 mm
stencil design for 0.5 mm pitch components"*), taking SAC305 T4 paste at 50 %
metal **by volume** and a 1.6 mm finished board:

| | measured |
|---|---|
| one 0.150 mm × 1.6 mm barrel | **0.02827 mm³** |
| EP paste 9 × 0.750 × 0.750 mm | 5.0625 mm² = **66.94 %** of the 7.5625 mm² land — inside AN62's *"50 % to 70 %"* preferred band, so **the stencil is not the defect** |
| EP solder delivered @ 0.125 mm | 0.31641 mm³ |
| **7 barrels vs the EP joint** | **0.19792 mm³ = 62.6 %** (78.2 % at a 0.100 mm stencil, 52.1 % at 0.150 mm) |
| pad 8 / 11 / 18 solder delivered @ 0.125 mm | 0.01125 mm³ each (1:1 aperture) |
| **1 barrel vs one of those joints** | **2.51 ×** the entire joint (3.14 × at 0.100 mm) |

The three perimeter lands are the worse case, not the exposed pad: **the barrel
holds more than twice the solder the joint is given**, and two of the three
(`VDD`, `V3`) have no thermal or RF justification for a via-in-pad at all.

**THE PRICE — and it is OWED, not measured.** JLC's extra-charge article was
read directly for the small-via and drill-count rows above; **it was NOT read
for a resin-plug / POFV line, and this file will not invent one.** No price for
this option appears anywhere in this repo. **Ask for it with the §7 questions:**

> *"Please quote resin-filled and capped vias (plugged and plated over, POFV)
> for all 3446 × 0.15 mm vias on this 4-layer 1.6 mm board, and confirm the
> option is compatible with the advanced small-via option and with controlled
> impedance on the same order."*

**Do not order this board until that line is on the quote.** It is the only
paid option here that is not a geometry convenience — the other three buy
manufacturability, this one buys the RF ground joint of the part the board
exists to switch.

**IF POFV IS REFUSED OR PRICED OUT, THE FALLBACK IS COPPER, NOT A WAIVER**, and
it is more expensive than it looks. Mask dams inside the exposed pad are AN62's
sanctioned alternative, but the three vias in pads 8/11/18 have **0.025 mm** of
copper rail beside the annulus and cannot take a dam at any mask sliver floor —
those three would have to MOVE, which means a re-route, which re-opens **both**
of this board's tight margins at once (the VIA↔PTH hole class at **12.0 µm** of
true margin, and the RF fence at **1.1769 mm** against λ_pp/20 = **1.1910 mm**,
whose joint pass window was measured at **49.8 µm** wide). **POFV moves no
copper and therefore risks neither.** That asymmetry is the argument for paying.

**4. Checked and CLEAR, so it is not rediscovered.** Extra-charge item 5 is
*"When the ENIG area is over 30% of the total PCB dimension"*, and §0 recommends
ENIG. DERIVED: ~50 SMA barrel pads (π·0.95²·50 = 141.7 mm²) plus the QFN-24 and
passives (≈30 mm²) ≈ **175 mm² of 3650 mm² = 4.8 %**. Vias are tented
(`F_Mask.gts` is 7.5 kB — pads, not 3446 via openings). Well under 30 %. **No
ENIG surcharge.** *(Refined by item 3 and the conclusion is unmoved: **3436** of
the 3446 vias are tented on both faces; the ten inside `U_SW`'s lands are open
at the top, but they lie INSIDE pad apertures already counted in the 175 mm², so
they add no ENIG area. The 4.8 % stands.)*

**The `.kicad_pcb` carries NO `(stackup …)` block — and neither does any other
board in this fleet.** MEASURED 2026-07-31: `grep -c '(stackup'` returns **0**
on all 34 sealed `source/*.kicad_pcb` and on every working `04_kicad/` board in
`projects/`. So its absence here is FLEET NORM, not a regression of this board,
and the laminate is stated where the fleet states it — this file and
`MANIFEST.txt`. It is still a real gap: nothing machine-readable inside the
archive names the stackup. Recorded as an open item in §7, not silently fixed
by hand-editing a generated board (canon M3).

---

## 1. THE TWO KEYS

### `design_verdict: DEFECTIVE`

**DEFECTIVE is the correct key for this archive, and the reason is NOT that a
copper defect is known to be open.** It is that the instrument allowed to say
otherwise has not run against this board.

The last full red-team round (2026-07-31, four lenses) graded a board this one
has since left: the hole-to-hole fix moved copper. Under
`08_reviews/contracts.md` a `DO-NOT-ORDER` verdict blocks the seal until
re-gated or superseded, and only a RE-GATE can move it — a re-gate of THIS
archive, not a re-reading of the previous one. Writing `SOUND` here on the
strength of reviews of different copper is exactly the adjacent-property error
this repo has paid for before.

**The archive therefore ships NO `verification/redteam_*.md`, `pin_review.md`
or `render_review.md`, and A-EVID FAILS on precisely those four names.** That is
deliberate (§7 item 3). The previous revision of this document shipped the
stale r2 lens files to satisfy the contract by NAME and argued that "an absent
required artifact is worse than a stale one". **That argument is withdrawn**: a
stale review sitting at a contract-required path is read by every name-based
check as this release's verdict, and it grades one version's copper against
another version's release. An honest FAIL is the smaller defect.

**What the older findings measure as, now.** Each blocking finding from the
earlier rounds was re-measured against the SHIPPED board in this session. The
numbers are in the evidence files named in §4 and in `MANIFEST.txt`; in
summary: the `J_ANT8`↔`J_RX1` spacing defect is closed by re-placement (the
branch line is gone and the closest jack pair now clears a 5/16 in nut's
across-corners dimension); the fence bound is met with 0 arm-sides over, on a
CBCPW derivation that made the bound TIGHTER than the microstrip one it
replaced; `MANIFEST.txt` and this README exist; and `pdf/schematic.pdf` is
tscircuit's own render, regenerated by `rebuild_all.sh` step [1r] with M-FRESH
verifying it post-dates the `circuit.json` it depicts.

**So the honest reading is: the findings behind the verdict measure closed, and
the instrument that is allowed to say so has not run.** That instrument is the
next step, and it is not this document.

### `order_verdict: DO-NOT-ORDER`

Follows from the design verdict, and additionally from §2: three human gates
are owed before the first order, one of which (through-hole assembly) changes
what arrives in the box. A fourth is added by §7 item 4 — the vendor's
mixed-class hole rule, which must be put to JLC in writing.

**No sourcing wall — NOW. There was one, it was invisible to every gate in this
repo, and closing it changed the BOM.**

The previous revision of this sentence read *"every coded line clears the build
quantity; the count and the multiple are in `verification/stock_check.json`"*.
**Both halves were false.** MEASURED 2026-07-31 by POSTing all 11 codes to JLC's
own `selectSmtComponentList` endpoint by hand — a different method from
`jlc_stock_check.py`'s catalog read (canon M1) — and re-measured independently a
second time after the fix:

- **`C25744` (UniOhm 0402WGF1002TCE, 10 kΩ, `R_PD1`..`R_PD4`) needs 20 and its
  `minPurchaseNum` is 779 — 39× the requirement.** Its `canPresaleNumber` is
  **−6,175,310**: the ~31 k catalog units are already oversubscribed by six
  million, which is why the minimum jumped. `jlc_stock_check.py` reads
  `stockCount` ONLY (blind spot #73), sees ~31 k, prints `OK`, and A-STOCK's
  `PASS, 11/11 coded lines at >= 5x qty` was **literally true and operationally
  wrong**.
- **"the multiple" was in NO FILE for 10 of 11 lines.** `stock_check.json`
  carries no MOQ field of any kind — its per-line keys are `lcsc, designators,
  qty, status, stock, type, mpn`. The one MOQ number anywhere in the archive was
  a cached page for a single part. The README asserted a check that had never
  been run.

**THE FIX WAS MADE AT SOURCE AND THE BOARD WAS REBUILT.**
`03_tscircuit/src/pluto_rx2_8way_v2.tsx` now reads `const R10K = "C60490"`
(YAGEO **RC0402FR-0710KL**). The two parts' JLC `describe` strings are
**byte-identical** — `-55℃~+155℃ 10kΩ 50V 62.5mW Thick Film Resistor ±1%
±100ppm/℃ 0402` — and all seven structured attributes match. `C60490` was
already in the vetted passives ledger, so no skill file changed.

**MOQ, RE-MEASURED BY HAND FOR ALL 11 LINES, because the gate still cannot.**

| LCSC | designators | need (5 bd) | stockCount | **minPurchaseNum** | lib | MOQ |
|---|---|---|---|---|---|---|
| C1525 | C_SW1 | 5 | 46,106,812 | 1 | base | OK |
| **C60490** | **R_PD1..R_PD4** | **20** | **8,740,134** | **1** | **expand** | **OK** |
| C15849 | C_SW2 | 5 | 14,327,340 | 1 | base | OK |
| C25091 | R_T1,R_T2 | 10 | 1,713,109 | 1 | base | OK |
| C1779 | C_BULK | 5 | 3,548,353 | 1 | base | OK |
| C137864 | R_S1..R_S4 | 20 | 73,417 | 1 | expand | OK |
| C137948 | R_LED | 5 | 743,754 | 1 | expand | OK |
| C3716677 | FB_3V3 | 5 | 5,838 | 1 | expand | OK |
| C504007 | J_ANT1..8, J_RX1..2 | 50 | 22,707 | 1 | expand | OK |
| C2286 | LED_ST | 5 | 7,333,743 | 1 | base | OK |
| C5121458 | U_SW | 5 | 1,284 | 1 | expand | OK |

**11 of 11 pass MOQ. Denominator 11, failures 0** (it was 10/11 with one failure
before the swap). Every line's `minPurchaseNum` is 1, so `need` is purchasable
outright with no rounding up.

**THE SWAP HAS A PRICE AND IT IS NOT AVOIDABLE.** `C60490` is `expand`
(extended) where `C25744` was `base`, so this line now carries **one
extended-part setup fee** (~$3/reel) and the board's extended count goes 5 -> 6
of 11. That is not a choice we could have made differently: a catalog sweep of
**322 unique 0402 10 kΩ codes** — five keyword forms across two pages each,
5× the 64-code sweep this paragraph originally cited — found `C25744` is the
**only `base`-library 10 kΩ 0402 JLC lists**, and it is the one that cannot be
bought at 20. The conclusion survived the wider denominator, which is why the
wider denominator is the one recorded. The
basic-tier slot for this value does not currently exist in a buyable state. The
unit price falls $0.0115 -> $0.0058, so the parts cost drops; the setup fee is
the real delta.

**`BLOCKED-SOURCING` is not the applicable key** — the part was always
purchasable, just not as budgeted, and it now is.

**A SECOND MOQ-SHAPED FIELD THE GATE IS ALSO BLIND TO, found in the same raw
JSON and recorded so it is not rediscovered:** `leastPatchNumber` (JLC's minimum
patch quantity). **Six of 11 lines have `need` below it** — C1525, C15849,
C25091, C1779, C137948, C2286, each `leastPatchNumber` 20 against needs of 5-10,
each also carrying `lossNumber` 10. It does not block a purchase; it sets a
BILLED FLOOR, so the invoice will show more pieces than the build consumes.
Named here, and folded into the same proposed gate fix in §9.

---

## 2. HUMAN GATES OWED BEFORE THE FIRST ORDER — none is optional

### 2a. SELECT THROUGH-HOLE (PLUG-IN) ASSEMBLY. **On the standard SMT flow this board arrives with every RF port loose.**

MEASURED off the shipped board: the ten `KH-SMA-KE-Z` jacks (`J_ANT1`…`J_ANT8`,
`J_RX1`, `J_RX2`) carry **10 refs × 5 plated drilled pads = 50 plated holes at
1.400 mm**, with **F.Paste on none of them**. They are on the CPL as `top`, on
a `service: standard`, `sides: [top]` order. **No reflow profile solders a
1.400 mm barrel from a stencil that has no aperture over it.** This is the
board's entire product — ten RF ports.

**CORRECTION TO THE MECHANISM — the previous revision said "it is one
checkbox", and that checkbox does not exist.** JLC's own wording for
through-hole is *"Ordering process: The same as SMT assembly"* — plug-in
assembly is not a toggle on the SMT order form; it is selected by the parts
being through-hole and confirmed in the quote review, and JLC may decline to
run the process on a given order. **The RISK is unchanged and real** — 50 PTH
pads, F.Paste on none of them, all CPL-`top`. Only the described remedy was
wrong, and "one checkbox" is exactly the sentence that makes a human skip the
gate. Raise it explicitly in the order notes and confirm it in the quote
review; do not look for a tickbox.

**The line is BOUGHT, not dodged, and that was proved rather than assumed.**
JLC's own assembly-parts endpoint, re-read 2026-07-31 with the raw response
archived at `verification/jlc_catalog_C504007.json`:

```
componentCode             C504007
componentModelEn          KH-SMA-KE-Z          (Shenzhen Kinghelm Elec)
componentSpecificationEn  "Plugin"             <- JLC's own word for THROUGH-HOLE
componentTypeEn           "Coaxial Connectors (RF)"
componentLibraryType      expand               (extended: one reel/tray setup fee)
stockCount                22708                (23169 on 2026-07-30; ordinary drift)
minPurchaseNum            1
assemblyProcess           null                 <- NO API ANSWERS THIS
```

Cross-checked the same day by `verification/stock_check.csv`, whose `pkg`
column reads `Plugin` for exactly this line and a real SMD package string for
all ten others.

**WHAT THAT DOES NOT PROVE, stated so it is not read as proven:** that JLC will
RUN a through-hole line on *this* order. `assemblyProcess` comes back null and
no API answers it — which is why this is a HUMAN gate and not a machine one. If
JLC declines the process, the fallback is `not_assembled` with
`reason: process_incompatible` for these ten refs, which is a BOM/CPL change
and therefore **a new release, not an edit**.

### 2b. `C5121458` (PE42482A-X, `U_SW`) — JLC order-preview ROTATION check

Single-channel under canon A-POL: the pad-number fit is the ONLY evidence for
its rotation, and a pad-number fit structurally cannot see a model whose own
numbering differs from ours. Measured offset **0** against the advisory
name-DB's **270** — 90° apart. The measurement wins (the name DB is advisory),
but it is one channel, so a human confirms it in JLC's rendered preview before
the first order. Named by the exporter itself in
`verification/rotation_human_gate.txt`.

### 2c. `C2286` (KT-0603R, `LED_ST`) — POLARITY

The pad cloud is degenerate — rms **0.0375 mm at BOTH 0 and 180**, vs 1.0875 mm
at 90/270 — so the fit's "180" carries no physical claim. Adjudicated to offset
**0**, and the twin's own `ROT-DB-SUGGEST C2286,180` line is **refuted, not
ignored**: a 180 row would seat every unit reverse-biased. Two independent
channels agree on 0 — both libraries draw the cathode WEST, and the board
corroborates it without reading any drawing (`LED_ST` pad 1 is on GND, pad 2 on
`LED_STAT_A`, and KiCad's `Device:LED` is pin 1 = K). Confirm in the preview.

### 2d. F-ECHO — after upload, diff JLC's RESOLVED table against ours

Upload `fab/bom.csv`, save JLC's own resolved/matched part table out of their
UI, and run
`bom_legibility_check.py fab/bom.csv --echo SAVED.csv` against
`verification/bom_echo_gate.txt` (**11 coded lines**). A code JLC redirects is a
**SUBSTITUTION and a FINDING** — `C82317 → C131025` happened on a shipped board
in this fleet and nothing in this repo could have seen it. The stock PASS in §4
is measured against LCSC **catalog** stock; JLC's assembly uploader allocates
from a different pool, so that PASS is necessary and **not sufficient**.

---

## 3. Population — declared, never emergent

`not_assembled: H1, H2, H3, H4, U_MCU` — GENERATED from
`03_src/rules/assembly.yaml`, which is its one home, and reproduced in
`MANIFEST.txt`.

- **H1–H4** are M3 mounting holes — no part, 3.200 mm NPTH.
- **`U_MCU` (RP2040-Zero) is NOT machine-assembled, and the reason is
  MECHANICAL, not a sourcing preference.** The module is not flat-backed:
  measured off the vendor Creo STEP assembly, **23 components sit on the
  carrier-facing face** — the 12 MHz crystal 1.000 mm proud, the RP2040 QFN-56
  0.850, the RT9013 LDO 0.700, twenty 0201s 0.300 — against 0.010 mm
  castellation lands. The joint plane and the collision plane are the same
  plane, so the part cannot sit down; no reflow profile bridges a 1.0 mm
  standoff at 2.54 mm pitch. It is hand-soldered, and it is `on_bom: false`, so
  it leaves the BOM as well as the CPL. **Buy 5+ RP2040-Zero modules at retail
  (Waveshare direct, Amazon, Mouser, DigiKey — broad, not single-source) and
  solder them yourself.** Its footprint carries `exclude_from_pos_files` and
  **no F.Paste apertures** — paste printed under a part that is never placed
  reflows into solder balls.

**Top side only; no bottom-side placements.** The BOM line count, the CPL
placement count and the per-side histogram are stated once, in
`MANIFEST.txt`, and are GENERATED — `assembly_coverage.py --emit-manifest-line`
writes the `not_assembled:` line from `assembly.yaml` rather than a human
retyping it.

---

## 4. What was measured, and with what RAW exit code

Every gate below was run **UNPIPED** against the artifacts in THIS directory
(or the `04_kicad/` originals they are byte-copies of), on 2026-07-31, and the
exit code was read directly — never through a pipe.

**THE COUNTS ARE NOT REPEATED HERE.** Each gate's numbers live in exactly two
places: the evidence file named in the last column, and the `gates:` block of
`MANIFEST.txt`. A third copy in this file is how the previous revision's gate
table came to claim `62 ↔ 62` while the footer and the truth were both 63.

| gate | verdict | RAW EXIT | evidence |
|---|---|---|---|
| DRC `--severity-all --refill-zones --schematic-parity` | **CLEAN — 0 violations / 0 unconnected / 0 parity, all three CLASSIFIED, none summarised** | 0 | `verification/drc.json` |
| **standalone archive DRC** — `source/` copied OUTSIDE the repo and re-measured | **CLEAN, all three halves** | 0 | `verification/standalone_archive_drc.json` |
| netlist parity, node-for-node (`kicad_sch_parity.py`) | **PARITY 0** | 0 | `verification/parity.md` |
| ERC errors (`--severity-error --exit-code-violations`) | **0 errors** | 0 | `verification/erc.json` |
| ERC full severity (baseline) | warnings only, two types, both converter geometry/symbol-synthesis artefacts, neither electrical | 0 | `verification/erc.json` |
| `fence_pitch.py` (λ_pp/20 stitch bound) | **VERDICT: PASS**, 0 arm-sides OVER | 0 | `verification/fence_pitch.txt` |
| `fence_apertures.py` (same bound, lattice view) | **0 GAP lines.** Its own header states it **exits 0 by construction**, so its exit code is NEVER the evidence — the absence of GAP lines is | 0 (not evidence) | `verification/fence_apertures.txt` |
| `fence_sites.py` | 0 apertures over bound, 0 residual, 0 vias proposed | 0 | `verification/fence_sites.txt` |
| `gcpw_constants.py` | the constant set, re-derived | 0 | `verification/gcpw_constants.txt` |
| `line_type.py` | GCPW confirmed on the arms; In1.Cu reference continuous apart from the launch antipads | 0 | `verification/line_type.txt` |
| `placement_gates.py` (P-OUT / P-CAP) | **PASS**, 0 fails 0 warns | 0 | `verification/audit.txt` §[1] |
| `escape_check.py --board` (P-LAND) | **PASS**, 0 failing | 0 | `verification/audit.txt` §[2] |
| `copper_length_audit.py` (R-LEN) | **PASS**, 0 UNREACHED | 0 | `verification/audit.txt` §[3] |
| `jlc_twin.py` (independent vendor geometry) | **0 CRITICAL**, every CPL designator resolves a body | 0 | `verification/twin_report.csv`, `verification/missing_models.txt` |
| `twin_overlay.py` (A-RENDER) | **OVERLAY OK** — every measurable body renders within 1.00 mm of where the board puts it | 0 | `verification/twin_overlay.md` |
| `assembly_coverage.py` (A-POP) against THIS archive | **PASS** — 32 footprints, 27 CPL, 5 unpopulated all DECLARED; A-POS datum worst 0.00000 mm | 0 | `verification/assembly_coverage.txt` |
| `bom_source_check.py` (M-BOM) | **PASS** — every BOM LCSC == source | 0 | `verification/bom_source_check.txt` |
| `bom_legibility_check.py` (F-LEGIBLE) | **OK** — F-MPN, F-WORDS and F-ENCODE all clear | 0 | `verification/bom_legibility.txt` |
| `part_facts_check.py` (P-FACT) | **OK**, with 1 assertion UNREACHED and NAMED (RP2040-Zero's value assert: its code is on no BOM row, because the module is `on_bom: false`) | 0 | `verification/part_facts.txt` |
| `jlc_stock_check.py` (A-STOCK), live | **verdict=PASS**, every coded line ≥ 5× qty — **AND BLIND TO MOQ, which is the §1 finding.** It reads `stockCount` only; the MOQ denominator was measured BY HAND, 11/11, and is in §1, not in this file | 0 | `verification/stock_check.{json,csv,txt}` |
| `fab_payload_census.py` (F-PAYLOAD) | **OK** — F-IDENT: the four copper gerbers are all DISTINCT; F-POUR: every zone-bearing copper layer carries its regions | 0 | this table |
| `release_required_check.py` (A-EVID) | **FAIL — and correctly so:** 4 missing, 0 unparsed, 29 present. See §7 item 3. **Must be run with `--contract 07_releases/contracts.md`** — its default resolves to `06_build/contracts.md` for a staging dir and grades against a file with no contract tree | 1 | §7 |
| `policy_audit.py` | **FAIL=1, HUMAN=6, N-A=7, PASS=31.** The one FAIL is the A-POP path-resolution artefact of §7 item 1 — it grades the PROJECT ROOT because `07_releases/` is empty. Against THIS archive A-POP is PASS at RAW EXIT 0 (row above) | 1 | `verification/policy_audit.md` |

### RF instruments — what the numbers mean

- **`fence_apertures.py` EXITS 0 BY CONSTRUCTION.** Its own module header says
  so. A reader who takes its exit code as a pass has read nothing; the evidence
  is the ABSENCE of GAP lines in its output, and it needs the lattice pitch as
  its second argument or it does not run at all.
- **`RX1_TAP` E is the tightest arm-side on the board** — see
  `verification/fence_pitch.txt` for the margin. That is the number to re-check
  first if the stackup is substituted, because the bound moves with εr.
- **The fence verdict is decided by which elements a ±2.5 mm band admits at the
  arm ENDS**, and 2.5 is a default constant in the gate, not a derived one.
  `fence_pitch.py` also grades **interior gaps only** — lead-in and run-out are
  printed and enter no comparison. Both are open findings (RF-3, RF-4), and
  RF-4 is load-bearing: it is why the eight crowding vias were MOVED rather
  than deleted.

---
## 5. Bring-up

### ⚠️⚠️ BEFORE ANY OF IT — THE RF PORTS ARE RATED 0 VDC, AND THERE IS NOTHING PROTECTING THEM ⚠️⚠️

`U_SW` (PE42482) specifies **absolute maximum 0 VDC on RF1…RF8 and RFC**. This
board carries **no DC blocking capacitor and no clamp on any of them**. Those
nine nodes are the **centre pins of user-accessible SMA jacks** — the most
touchable points on the assembly.

**This is not theoretical, and the danger is inside this very section.** Step 2
below asks you to check continuity from the ANT centre pins to GND. **A
continuity tester or DMM applies a DC test voltage** — typically 0.2–3 V — and
that is already outside the part's stated rating.

Therefore, BINDING:

- **Do the ANT centre-pin continuity check with `U_SW` NOT FITTED**, or not at all.
  Once `U_SW` is on the board there is no safe way to DC-probe those nets.
- **Never connect a bias-tee, a phantom-powered LNA, an active antenna, or any
  feed carrying DC** to `ANT1`…`ANT8` or `RX1`/`RX2`. A passive antenna or a
  DC-free source only.
- **If DC on the ports is required for your application, it is a BOARD CHANGE** —
  series DC blocks on all nine ports — not a bring-up workaround.

This was raised independently by two review lenses and is the single most likely
way to destroy a populated board.

---

1. **Do not fit `U_MCU` first.** Power the board and confirm 3V3 is present and
   in tolerance at `FB_3V3` before the module goes on.
2. **Continuity, before RF — and see the DC warning above:** every SMA shell to
   GND; `ANT1`…`ANT8` centre pins isolated from GND (the launch antipads are the
   only reference break). **Do this with `U_SW` unfitted.**
3. **Control lines:** `SW_V1`…`SW_V4` and `SEL_V1`…`SEL_V4` toggle from the MCU
   and read back at `U_SW`'s control pads.
4. **RF, in this order:** insertion loss `RX1_MAIN` → each ANT arm, then port
   isolation. The arms are the board's published property; nine arm phases are
   comparable **only because In1.Cu is an unbroken reference**, so any
   measurement that disagrees should first be checked against a continuity
   break in In1.Cu.
5. **Expect the per-port return loss to be LAUNCH-DOMINATED.** The 3.510 mm
   antipad over a 1.450 mm barrel is a ~25 Ω coaxial section, ≈ **−11.4 dB**
   per launch by a first-order model — larger than anything on the arms, common
   to all ten jacks, and inherent to a THT SMA on 1.6 mm FR-4. The first VNA
   sweep will read as a design failure if this is not expected.
6. **`LED_ST`** lights on the STAT GPIO — if it never lights, check polarity
   against §2c before suspecting firmware.

### 5a. BUILD AND HANDLING ORDER — three constraints that are geometry, not preference

These were each measured and each dispositioned "belongs in bring-up" during
review, and none of them had been written down until now.

**Hand-solder the four series resistors BEFORE `U_MCU`.** MEASURED:
courtyard-to-courtyard from `R_S1`…`R_S4` to `U_MCU` is **0.4300 mm** on all
four; pad-copper to pad-copper is **0.9200 mm**. DRC is 0/0/0, so the copper is
perfectly legal — **0.43 mm is the iron-access number, not a clearance
violation.** With the module fitted there is not room to get a tip onto those
joints without working over it. If any of the four needs rework later, the
module comes off first.

**Tighten the SMA jacks BEFORE the board is populated, and torque them in a
diagonal order.** They are through-hole parts on a 1.6 mm board with 3.2 mm NPTH
mounting holes; sequential tightening walks the board. Nut-flat clearance between
the closest pair (`J_ANT8`↔`J_RX2`) is **+0.7680 mm** — real, but small enough
that an angled driver will find a neighbour.

**The bottom side is bare, and it will short on any conductive surface.**
MEASURED: **0** board `B.SilkS` drawings, **0** footprint `B.SilkS` graphics,
**0** refdes on `B.SilkS`, **54 through pads**, and **0 `F.Paste` and 0
`B.Paste` apertures on any `J_*`**. There is nothing printed on that face to
warn anyone, and 54 exposed through-pad tails. **Do not lay this board down on
an ESD mat with the bottom side loose, do not bench it on a conductive surface,
and use standoffs.** There is no silk telling you this because there is no silk
on that side at all.

---

## 6. Provenance

- Every artifact regenerated from `03_src/` + `03_tscircuit/` by
  `03_src/rebuild_all.sh` (canon M3). **Nothing in `04_kicad/` was
  hand-edited.**
- **`fab/bom.csv` and `fab/cpl.csv` carry the CONTRACT's names because the
  EXPORTER now writes them.** They are not renamed copies. Until 2026-07-31
  `export_jlc_package.py` wrote `bom_jlc.csv`/`cpl_jlc.csv` and every seal in
  this fleet bridged the gap by hand — which is what kept the mismatch
  invisible. Here the hand-copy did not happen, and the cost was not a missing
  file: `release_freshness_check.py` resolves **A-STOCK** and **A-BUY** through
  `fab/bom.csv`, so with the name absent both gates reached a **zero
  denominator** and emitted NOTES — *"no coded, placed line to grade"* and
  *"sourcing UNGRADED — 0 line(s) measured"* — instead of failures. Two gates
  that exist BECAUSE five sealed releases shipped failing stock evidence, silent
  over an empty set.
- **The archive stands alone, and that is tested rather than asserted.**
  `source/` was copied to a directory OUTSIDE this repository and re-measured
  on 2026-07-31: `kicad-cli pcb drc --severity-all --refill-zones
  --schematic-parity` = **0 violations / 0 unconnected / 0 parity, RAW EXIT
  0**, shipped as `verification/standalone_archive_drc.json`. The vendored
  `source/pluto_rx2_8way_v2.pretty` and the repointed `source/fp-lib-table` are
  what make that true: the in-repo table points at
  `${KIPRJMOD}/../03_src/lib/`, and a standalone copy carrying that table
  raises **12 `lib_footprint_issues`**. That same run created a
  `pluto_rx2_8way_v2.kicad_prl` in the COPY — the regeneration this archive's
  strip-last ordering exists for — and the archive itself carries **zero**.
- **No `*.kicad_prl` is archived.** `kicad-cli` regenerates one every time it
  opens a board, so a "don't copy it" filter is insufficient — the strip must be
  the **LAST** step, after every `kicad-cli` invocation including the final DRC.
- `MANIFEST.txt` ↔ this tree is **bijective in both directions** — every row has
  a file and every file has a row — and the count is stated in the MANIFEST's
  own footer rather than retyped here, because a hand-copied count is exactly
  what went wrong last revision (the gate table claimed **62 ↔ 62** while the
  footer and the truth were both **63**).

---

## 7. WHAT IS NOT GREEN — read this before sealing

Eight things. **Seven are not copper defects** — DRC, parity, the standalone
re-measure and the RF gates are in §4 and they are clean. **THREE are UNANSWERED
VENDOR QUESTIONS (items 4, 5 and 7), each order-blocking on its own, and they
should be sent in ONE message — item 7 was added this revision and §7a below
collects all three ready to paste.** **Item 8 is the exception: it IS a copper
defect, it is the only one, and it is closed by ordering a paid option rather
than by moving copper (§0 item 3).**

1. **`policy_audit` A-POP: FAIL — an artefact of NOT SEALING, and the only FAIL
   this audit reports.** `policy_audit` resolves A-POP's target as *the latest
   sealed release, else the project directory*; with `07_releases/` empty it
   grades the project root, finds no MANIFEST there, and reports
   `MANIFEST-UNDECLARED`. It closes at the seal. **S-OCCL, which was the second
   FAIL in the previous revision of this document, is now PASS** — the
   converter's de-collision pass was fixed and the thirteen text-over-wire
   occlusions are gone.

2. **THE ARCHIVE IS NOT BYTE-REPRODUCIBLE FROM COMMITTED STATE — and the
   previous revision of this item, and the MANIFEST beside it, BOTH said this
   board's own working tree was clean when it was not.**

   **The false sentence, first.** This item used to read *"Every input this
   board owns is committed and its working tree is clean"*, and `MANIFEST.txt`
   said *"`git status projects/pluto-rx2-8way-v2/` is EMPTY"*. Measured,
   unpiped, at the moment the stamp was written and again now:
   `03_src/route.yaml` is ` M`. It was modified **21 minutes BEFORE** the
   MANIFEST asserted it was not. **The substance survives and that was proved,
   not assumed** — the diff is comment-only: 146 non-comment lines on both
   sides, identical stripped sha256, `stitch.via.spacing: 0.75` in both, 0
   semantic diff lines. The board is not built from undeclared source. **But
   the claim is what a future reviewer checks, and this one was checkable and
   wrong**, which is the same class as §8a and §8b and belongs beside them.

   **What is actually dirty, counted rather than characterised.**
   `release_git_dirty.py pluto-rx2-8way-v2` (RAW EXIT 1) lists **eleven**
   paths, not the "four backend scripts, all in `skills/`" the stamp described:
   the four backend scripts, plus `design-policies.md`, `routing-pipeline.md`,
   `skills/kicad-pcb/scripts/contracts.md`, `gate_contract_audit.py`, the
   `03_src` contracts template, **`03_src/route.yaml`** (this board's own), and
   an untracked `skills/kicad-pcb/scripts/dru_subject.py`. Naming the four that
   matter for reproducibility is the right editorial choice; saying they are
   ALL in `skills/` is not, and it is false for the same file as above.

   **The mtimes in the previous stamp were ALREADY STALE WHEN WRITTEN.** It
   recorded `pcb_toolkit.py` at 13:51; the file read 15:27:44 — it moved again
   14 minutes AFTER the MANIFEST was stamped, while this archive sat staged.
   That does not weaken the conclusion, it strengthens it: the tree is further
   from reproducible than the stamp said. **This revision therefore records the
   dirty set as a COUNT and a SCOPE and does not retype mtimes**, because a
   transcribed timestamp of a file another session owns is stale the moment it
   is written.

   **The reproducibility conclusion stands, and it is now MEASURED rather than
   inferred.** The four shared backend scripts remain uncommitted, so
   `rebuild_all.sh` today is not provably the driver that produced any earlier
   board. What today's rebuild DID establish, by running it: **today's backend
   produces the same copper.** The fab set is multiset-identical to the
   previous staging apart from the `TF.CreationDate` stamp; the board's via /
   segment / footprint sets are exactly equal; the `.kicad_sch` and `.net` are
   UUID-masked-identical. So this is a **COMMIT DEPENDENCY, not a rebuild
   dependency**. `git_dirty: false` is a SEAL PRECONDITION, the flag stays
   `true`, and stamping it `false` to make a gate green is the shortcut the
   flag exists to prevent.

3. **`release_required_check.py` (A-EVID): FAIL, and the missing artifacts are
   exactly the four RED-TEAM REVIEW DOCUMENTS.** `verification/` carries no
   `redteam_layout.md`, `redteam_topology.md`, `pin_review.md` or
   `render_review.md`. **This is the correct state and must not be closed by
   copying the existing reviews in.** The four 2026-07-31 lens reviews in
   `08_reviews/` graded copper this board has left; promoting one version's
   review as another version's release verdict is the adjacent-property error
   `release_freshness_check.py`'s own M-REV comment warns about. A missing
   verdict is a FAIL and not a skip, and it stays a FAIL until a fresh lens
   reads the board that exists. Everything else the contract requires IS
   present.

4. **THE VENDOR QUESTION ABOUT THE TIGHT HOLE CLASS IS NOT SETTLED — put it to
   JLC IN WRITING BEFORE ORDERING.** The tight hole class on this board is a
   **VIA against a PTH PAD** (a stitching via beside an SMA ground barrel), not
   via-against-via. JLC publishes a via-to-via hole floor and a pad-to-pad hole
   floor and **NOTHING for the mixed class**; their own public Q&A #693 is a
   customer asking exactly this question, and it is unanswered. What this
   revision did is raise the board's declared `hole_to_hole` so that the board
   **honours ITS OWN declared tier at max material** under JLC's published
   `+0.13/−0.08 mm` PAD-hole tolerance ("the diameter of via holes is not
   controlled" — so the growth is applied to the pad hole only, once, not to
   both holes). That is a real fix and the measurement is in `MANIFEST.txt`.
   **It is not an answer to the vendor question.** Ask JLC, in writing, before
   the order: *"On the 4-layer advanced tier, what is your minimum hole-to-hole
   edge-to-edge between a 0.15 mm VIA hole and a 1.40 mm PTH PAD hole, and is
   it evaluated at nominal or at max material?"* Record the answer beside the
   §2 human gates. This is a DFM item, not a solved problem.

   **THE EXPOSURE IF THE ANSWER IS "THE PAD GOVERNS", stated because it is what
   decides how much rework the answer implies:** the mixed class sits BETWEEN
   the two published floors (above via<->via 0.2 mm, below pad<->pad 0.45 mm),
   so a legitimate answer could land anywhere in `[0.2, 0.45]`. At 0.2 the
   board clears by 63 %. **At 0.45, 54 via-against-SMA-barrel pairs are
   non-compliant and the board needs RE-STITCHING, not a re-measurement.**

5. **A SECOND VENDOR QUESTION IS OWED, AND IT IS ORDER-BLOCKING ON EITHER
   READING — the impedance option and the 0.15 mm drill are declared on the
   SAME order.** JLC's controlled-impedance capability page publishes
   **`Min. Via` = `0.2mm`** and never says whether that is a via HOLE or a via
   DIAMETER; MEASURED, the words `hole`, `drill`, `annular`, `pad`, `aperture`
   and `finished` occur **zero times each** on that page. §0 declares a 0.15 mm
   drill (forced by the QFN-24 escape arithmetic) AND impedance control (the
   board's product). On the HOLE reading the two cannot both be had; on the
   DIAMETER reading there is no conflict. **This revision does NOT pick a
   reading** — the full record, the options, and why guessing here is the
   ADR-0005 failure mode, are in **ADR-0006**
   (`01_docs/decisions/0006-the-impedance-option-and-the-0-15-mm-drill-are-declared-on-the-same-order.md`).
   Send this with the §7.4 question, in the same message:

   > *"For a 4-layer 1.6 mm board on stackup JLC04161H-7628 with impedance
   > control requested, is the 'Min. Via: 0.2mm' on your controlled-impedance
   > capability page a via HOLE minimum or a via DIAMETER minimum, and can that
   > order carry 0.15 mm drilled / 0.25 mm finished vias?"*

   A returned QUOTE is not an answer: the capabilities pages and the quoting
   engine are different systems, and a price is not a statement that the
   combination was checked.

6. **No `(stackup …)` block in the `.kicad_pcb`.** Fleet-wide (0 of 34 sealed
   boards carry one), so it is not this board's regression — but it means
   nothing machine-readable **inside** the archive states the laminate that
   RF50 = 0.36 mm was solved for. §0 states it in prose; a generator change is
   the real fix, and hand-editing the board to add it would violate canon M3.

7. **A THIRD VENDOR QUESTION, AND IT IS THE ONE THAT DECIDES WHETHER ITEM 4'S
   FIX IS A FIX AT ALL — the max-material model gives via holes ZERO growth.**
   The 0.3145 mm floor this board now honours is computed by applying JLC's
   published **`+0.13 / −0.08 mm`** hole tolerance to the **PTH PAD hole ONLY**,
   once, on the strength of the vendor's sentence *"the diameter of via holes is
   not controlled"*. Under that reading the tight class is **0.3265 mm nominal
   / 0.2615 mm at max material** against the 0.3145 mm floor KiCad enforces —
   **true margin 12.0 µm**, and the board passes.

   **"Not controlled" is not the same statement as "does not grow."** It says
   JLC publishes no tolerance for that hole, which is an absence of a
   specification, not a specification of zero. A SYMMETRIC reading — the drill
   wanders on both holes — subtracts another 0.065 mm and puts the tight class
   at **0.1965 mm, with 32 pairs under 0.25 mm.** **So the 0.3145 mm floor, and
   therefore item 4's entire fix, is CONDITIONAL on the asymmetric reading, and
   nobody has confirmed it.** Ask, in the same message as items 4 and 5:

   > *"Your capabilities page states that the diameter of via holes is not
   > controlled, while plated holes carry +0.13 / −0.08 mm. For a hole-to-hole
   > edge-to-edge check between a 0.15 mm via hole and a 1.40 mm PTH pad hole,
   > do you evaluate the via hole at its nominal 0.15 mm, or does it carry a
   > tolerance you have simply not published? If the latter, what is it?"*

   **Recorded as a CONDITION on a green gate, not as a new failure.** The board
   passes today under the model it declares, and that model is written down
   where it can be checked. What is not acceptable is for the condition to be
   invisible: an unpublished tolerance read as zero is exactly the shape of
   assumption ADR-0005 exists to stop.

8. **TEN VIAS HAVE THEIR DRILLED HOLE INSIDE A SOLDERABLE LAND OF `U_SW`, AND
   ALL TEN ARE OPEN AT THE TOP. This is the one real copper defect in this
   archive, and NO EARLIER REVISION OF THIS FILE OR OF `MANIFEST.txt` NAMED
   IT.** Seven in the exposed pad (six of them fully under a printed paste
   window), one each in pad 8 (`VDD`), pad 11 (`V3`) and pad 18 (`GND`). Full
   measurement, gerber evidence, the pSemi AN62 citation and the solder-volume
   arithmetic are in **§0 item 3**; the remedy is to **order resin-filled and
   capped vias (POFV)**, which moves no copper and so risks neither of this
   board's two tight margins.

   **Provenance, because it changes who owns the fix.** Of the ten, **five are
   deliberate and reasoned** — `03_src/route.yaml:460-462` places five EP
   barrels under canon R6 with the argument that the EP is an RF ground return.
   **Two more EP vias — (41.010,47.730) and (42.350,48.930) — appear NOWHERE in
   `03_src/`**; they are emitted by the build-time stitch/fence passes and no
   one chose them. **Two — pads 8 and 11 — arrive from the promoted routing
   chain** `03_src/route/r5.kicad_pcb`, which is committed source, each carrying
   its own `(tenting (front yes) (back yes))` that the pad's mask aperture then
   silently defeats. **One — pad 18 — is likewise not in `03_src/`.** So half
   the population is emergent, and the half that is declared was declared for
   the exposed pad only.

   **This is a CLASS defect, not this board's.** `fab_tiers.yaml`'s
   `via_in_pad: true` is read by `escape_check.py` (lines 191, 196, 208) purely
   as a FEASIBILITY PREDICATE — permission to grade a fine-pitch escape
   possible — and by `route_and_stitch_generic.py:2046`, where it **defaults to
   `True`**. It is read by nothing that emits an order line. The same tier
   carries `order_readme:` text for the small-via option and none for this one.
   **`smc0985-cooksense` v1.7 — a SEALED release — carries the identical
   finding** (*"276 unfilled via-in-pad at 0.15 mm drill with no POFV
   ordered"*, `verification/2026-07-30_v1.7_redteam_layout_REGATE3.md:33` and
   `:272`), graded P2 and dispositioned *recorded*. `pluto-cal-switch` has the
   same shape. **Fixing it in this ORDER_README fixes one board; the skill
   change that fixes the class is PROPOSED in §9 and NOT APPLIED here.**

### 7z. `FB_3V3` + `C_SW1‖C_SW2` IS AN UNDAMPED LC — characterised, NOT fixed

**Status: OWED. Measured on paper, unmeasured on hardware, deliberately not
respun.** It had no disposition row at all until now — `grep FB_3V3
DISPOSITIONS.md` returned **0**, as did `peaking`, `PSRR` and `undamped`.

**The topology.** `FB_3V3` (Murata `BLM21SP601SN1D`) sits in series on the LDO
**output**, feeding `3V3_MOD`, with `C_SW1` (100 nF) ‖ `C_SW2` (1 µF) as its
shunt. That is a second-order LC filter with almost nothing damping it.

**The arithmetic**, from this board's own part dossier rather than a textbook:

| | |
|---|---|
| `L` | **~2.4 µH** — DERIVED, not published: X ≈ 150 Ω at 10 MHz off the impedance curve, L = X/2πf |
| `R` | **0.06 Ω** DCR (datasheet max) + ~0.05 Ω cap ESR ≈ **0.11 Ω** |
| `C` | 1.1 µF nominal, **less under DC bias** — `C_SW2` is an X5R 0603 at 3.3 V |
| `f₀` | **~98 kHz** at nominal C, **~123 kHz** derated — the dossier says ~123 kHz, a review said ~103 kHz; both are this range with different C assumptions |
| `Q = (1/R)·√(L/C)` | **~13 to ~17** |
| peaking | **≈ +22 to +25 dB** |

**Why the existing note does not cover it.** The dossier gotcha that appears to
dismiss bead resonance is about **`FB_IN`** — the bead on the LDO *input*, where
ADR-0004 gives it one job and explicitly says it is not protection. `FB_3V3` is a
*different reference in a different position*: on the output, in the supply path
to the module. The note was written for v1's topology and does not describe this
board.

**What it means in practice.** A load step on `3V3_MOD` at ~100 kHz is amplified
by roughly 15×. A 10 mV disturbance becomes ~160 mV — inside the RP2040's
±10 % supply tolerance, so **this is a noise finding, not a functional one** on
present evidence. It is on the rail that also feeds `U_SW`'s control.

**Why it is not being fixed in copper now.** The standard remedy is a damping
leg — a series R+C (order ~1 Ω + 10 µF) in parallel with `C_SW`, which drops Q
to ~1 and costs nothing at DC. That is a board change, and **this board has two
margins under 2 %**: hole-to-hole runs 12.0 µm inside the floor KiCad enforces,
and the RF fence sits 1.1769 against a 1.1910 mm bound with a both-pass window
measured at 49.8 µm. Adding copper to damp a noise peak that has never been
observed is not worth spending either margin blind.

**SETTLED ANALYTICALLY — and the dB figure was the wrong number to quote.**
+22.6 dB is the gain against a **sinusoid at exactly 98 kHz**. Nothing on this
rail produces one: the RP2040's core regulator is an LDO, not a switcher, so
there is no fixed-frequency excitation down there at all. What the rail actually
sees is a **load step**, and a step is broadband — its first excursion is
`I × Z₀` and is **NOT multiplied by Q**. Q sets how LONG it rings, not how HIGH
the first peak goes.

`Z₀ = √(L/C) = ` **1.477 Ω**, so:

| load step | first excursion | % of 3V3 | vs the RP2040's ±10 % (330 mV) |
|---|---|---|---|
| 50 mA | 74 mV | 2.2 % | OK |
| 100 mA | 148 mV | 4.5 % | OK |
| 150 mA | 222 mV | 6.7 % | OK |
| **200 mA** | **295 mV** | **9.0 %** | **OK** |

This board's own derived worst case is **~110 mA** (RP2040 core plus the module's
WS2812 at full white), so even a deliberately generous 200 mA bound stays inside
tolerance. Ring-down envelope `τ = 2L/R` = **44 µs**, about 4 cycles.

**DISPOSITION: NOT-A-DEFECT — bounded, in spec at 1.8× the board's own worst-case
step.** No damping leg, and therefore no copper spent against this board's two
sub-2 % margins (hole-to-hole 12.0 µm inside the enforced floor; RF fence 1.1769
against 1.1910 mm, both-pass window 49.8 µm).

**Bring-up CONFIRMATION, not a gate** — if you have a scope out anyway: 20 MHz
bandwidth limit on `3V3_MOD` during a load-stepping loop, expect ringing near
98 kHz decaying in ~44 µs at well under 300 mV. **Only if it exceeds ~330 mV p-p
does the damping leg (≈ 1 Ω + 10 µF in parallel with `C_SW`) become owed** — and
that would mean the load step is larger than anything derived here.

---

### 7a. THE THREE VENDOR QUESTIONS, COLLECTED — send as ONE message

Items 4, 5 and 7 are three readings of the same underlying problem: JLC
publishes capability numbers without saying what they are numbers *of*. Asking
them one at a time invites three partial answers.

> Hello — before placing a 4-layer order I need three capability points
> confirmed that your published pages leave ambiguous.
>
> **1.** On the 4-layer advanced tier, what is your minimum hole-to-hole
> edge-to-edge between a **0.15 mm VIA hole and a 1.40 mm PTH PAD hole**, and is
> it evaluated at nominal or at max material? Your pages give a via↔via floor
> and a pad↔pad floor but nothing for the mixed class.
>
> **2.** Your capabilities page states the **diameter of via holes is not
> controlled**, while plated holes carry **+0.13 / −0.08 mm**. For that
> hole-to-hole check, is the via hole evaluated at its nominal 0.15 mm, or does
> it carry a tolerance you have not published? If the latter, what is it?
>
> **3.** For a 4-layer 1.6 mm board on stackup **JLC04161H-7628** with
> **impedance control requested**, is the **"Min. Via: 0.2mm"** on your
> controlled-impedance capability page a via **HOLE** minimum or a via
> **DIAMETER** minimum, and can that order carry **0.15 mm drilled / 0.25 mm
> finished** vias?
>
> **4.** Please also quote **resin-filled and capped vias (plugged and plated
> over, POFV)** for all 3446 × 0.15 mm vias on this board, and confirm it is
> compatible with both the advanced small-via option and controlled impedance
> on the same order.

**A returned QUOTE is not an answer to 1-3.** The capabilities pages and the
quoting engine are different systems, and a price is not a statement that the
combination was checked. Record the replies beside the §2 human gates.

---

## 8. TWO PUBLISHED RF NUMBERS ARE OVERSTATED — the claims, not the copper

Both are CLAIM defects carried forward into this archive so they are not
rediscovered a third time. Neither changes a gate, a gerber or a verdict.

### 8a. The tap's 440 Ω is 220 Ω at the junction and 220 Ω a millimetre away

`03_src/floorplan.yaml` argues that the RX1 monitor tap presents *"the whole
440 Ω lumped AT the junction, |Z_node| ≥ 440 Ω, RL ≥ 25.5 dB"*. **That is
overstated by 1.61×, and the mechanism is layout, not arithmetic.** Only
`R_T1` = 220 Ω is at the junction. `R_T2` = 220 Ω sits **1.180 mm** of GCPW
downstream — **15.10° of electrical length at 6 GHz** — so the two do not add
as a lumped 440 Ω at the node. Transformed through that line, the measured
worst-case node impedance floor is **273.85 Ω**, giving **RL 21.45 dB**, not
440 Ω / 25.39 dB.

**The fix it replaced was still worth 47×.** The defect this topology
superseded presented **5.80 Ω / RL 1.71 dB** at the node. 273.85 Ω against
5.80 Ω is a **47× improvement in the worst case**, and the tap is SOUND. What
is wrong is the CLAIM, and the claim is what a future reviewer will check
against. Correct it in `floorplan.yaml`'s intent block at the next revision:
the guaranteed floor is **273.85 Ω / RL 21.45 dB at 6 GHz**, and 440 Ω is the
DC sum, not the RF node impedance.

### 8b. The silk's −20.26 dB is about 1 dB optimistic at 6 GHz

Same root cause. `DETAIL_DESIGN` §2 and the silkscreen publish
**−20.26 / 0.4322 / 26.2773 dB** to four significant figures **with no
frequency qualifier**. Those values are exact at 70 MHz. At 6 GHz the same
three measure **−21.6399 / −0.5812 / 23.2097 dB** — the mid line contributes
about 1.38 dB of the departure and the 0402 parasitics about 0.43 dB.

**This is a qualifier, not a number change.** Silk cannot change without a new
release; this file can carry it now: *coupling ≈ −20.3 dB at 70 MHz, ≈ −21.6 dB
at 6 GHz*. Anyone calibrating the monitor port against the silk legend at the
top of the band will be out by about a dB, in the safe direction.

### 8c. Four MEASURED numbers that travelled wrong, and are corrected here

**Every one is a CLAIM defect. None moves a gate, a gerber or a verdict** — and
each was checkable, which is why each is worth the paragraph. The corrected
figures live in `MANIFEST.txt`'s `fab:` and `gates:` blocks, which are their one
home; this section says what was wrong and how.

- **The MANIFEST's `PTH <-> PTH` hole-to-hole row was measuring the WRONG SET.**
  It recorded **2.1921 / 2.0621 mm**. Re-measured from the DRILL FILES (not
  pcbnew — canon M1), the true minimum is **1.6934 / 1.5634 mm** at
  **`J_RX2.5` <-> `J_ANT8.3`**. The shipped figure is `2.54·√2 − 2 × 0.7` — a
  jack's own centre pin to its own ground post — and **40 of the 41 close pairs
  sit at exactly that value, all of them INTRA-footprint**. The row silently
  measured intra-footprint pairs only, so the ONE inter-footprint pair, which is
  the actual minimum, never entered it. **Changes nothing** (1.5634 is 3.5× the
  0.45 mm pad<->pad floor) — but the label was wider than the number.

- **`seed_stubs` is 32 entries / 36 vias, and the earlier "23" omitted a whole
  entry.** Round 1's *"6 pin-serving + 17 fence = 23"* left out
  `{net: GND, pin: U_SW.25, vias: [5 coordinates]}` — the switch's exposed-pad
  thermal cross — and its **5** barrels. MEASURED now: **32 entries, 7
  pin-serving (11 vias) + 25 fence (25 vias) = 36 vias.** And the claim *"all at
  d = 0.0000 mm, exactly"* is **no longer true as worded**: 28 sit at d = 0.0000
  exactly, and the **8 declared to four decimals sit at 0.000224-0.000640 mm**
  because the emitter snaps to the micron. That is **0.18-0.51 % of the 125 µm
  via radius**. Nearest via on a different net than declared: **0**.

- **ERC is 0 errors / 213 warnings, and 209 was never a property of either
  board.** MEASURED on this schematic: **213 = 124 `endpoint_off_grid` + 89
  `lib_symbol_issues`**, all `severity: warning`, and the PRE-fix schematic
  reports the same 213 — so 209 is not a delta of any fix, it is a number
  neither board produces. **The "474/474 coordinates" denominator is
  UNREPRODUCIBLE and is retired rather than inherited.** The two denominators
  that are real, both re-derived here: **234/234** sheet connectivity
  coordinates on a 25 mil grid (78 wire endpoints + 89 symbol placements + 46
  global labels + 16 no-connects + 5 junctions), and **115/115** distinct
  ERC-flagged positions on 25 mil — of which only **4/115** are on the 50 mil
  grid KiCad's ERC actually checks against. The warnings are the converter
  putting the sheet on its own grid, half a step off the checker's.

- **The fence table is NOT "unchanged to four decimals" at ROW level.** The fix
  commit says it is. MEASURED, 3 of 22 arm-side rows moved: **ANT1 E
  1.1314 -> 1.1639**, **ANT5 E 1.1505 -> 1.1639**, **ANT2 W offset rows 7 -> 8**.
  Restated honestly: *the fence VERDICT, the worst interior gap (1.1769 mm at
  `RX1_TAP` E), the arm-side count (22) and the OVER count (0) are unchanged to
  four decimals; two arm-side maxima moved by +0.0325 and +0.0134 mm, both to
  1.1639 mm — still 2.3 % inside the 1.1910 mm bound and no longer the worst on
  the board.* "Unchanged" is the kind of sentence that travels, and this one was
  0.0325 mm off.

---

## 9. PROPOSED SKILL CHANGES — NOT APPLIED HERE

This board does not own `skills/`. Each item below is a defect this revision
MEASURED from inside the board, written so the skill owner can act on it
without re-deriving it. **Nothing in `skills/` was edited by this work.**

1. **`jlc_stock_check.py` is blind to MOQ (canon A-STOCK, blind spot #73).** It
   reads `stockCount` only. It must also read **`minPurchaseNum`** and grade
   `need` against it, emitting the required purchase quantity per line — and
   **`leastPatchNumber`**, which sets a billed floor and comes free in the same
   response. **A known-bad fixture exists today: `C25744`** returns
   `minPurchaseNum` 779 with `canPresaleNumber` ≈ −6.2 M, and will stay one as
   long as that presale number is negative. Without the fixture the gate cannot
   be shown to fail. *Severity: this board's exposure was $9 of resistors. The
   identical condition on `C5121458` (RF switch, $6.09/pc, 1,284 in stock) is a
   $4,700 surprise. The missing check is the finding, not the nine dollars.*

2. **`skills/kicad-pcb/references/fab_tiers.yaml` carries two REFUTED vendor
   numbers** in `jlc_2layer_default`: `min_via_drill: 0.3` and
   `min_hole_to_hole: 0.5`, the latter with an inline comment calling 0.5 "JLC
   published". MEASURED against the page: free drill goes to **0.20 mm** with a
   0.45 mm pad, and the two published hole-to-hole floors are **via<->via
   0.2 mm** and **pad<->pad 0.45 mm** — 0.50 mm is the *Min. NPTH SIZE* and the
   *castellated* hole-to-hole, two unrelated rows. Re-derive every
   `min_hole_to_hole` in that file, and **add `min_hole_to_hole_pad` as a
   distinct key**: a single scalar cannot represent a vendor model that
   publishes two floors and nothing for the mixed pair, and that modelling gap
   is what let this board's round-1 hole-to-hole defect exist.

3. **`release_freshness_check.py`'s `M-REV` has a zero-denominator silent
   pass.** `graded = [n for n in _REVIEW_LENS_FILES if (ver / n).is_file()]`
   followed by `if not graded: return` means a release with NO review documents
   reports `DESIGN: PASS / FRESHNESS: PASS`, RAW EXIT 0 — while A-EVID on the
   same tree, at the same moment, reports 4 missing artifacts and exits 1. The
   gate enforces *"a missing verdict is a FAIL, never a skip"* for a missing
   **KEY** and not for a missing **FILE**, and its own docstring states the
   doctrine without the distinction.

4. **`policy_audit.py` never runs A-EVID** — 0 occurrences of the string in the
   script and 0 in the audit it generates. `release_required_check.py` is
   invoked only by `fleet_regrade.py` and `tests/t1_release_required.py`, so a
   seal driven off `policy_audit` + `release_freshness_check` alone **would not
   notice that four required review documents are absent**. Until that is
   wired, A-EVID must be run BY HAND at every seal, and this file is the record
   that it currently must be.

5. **`bom_source_check.py` leg C declares its coverage as `7/7`** in a run that
   saw 11 rows. It should print **7/11 with the 4 ungraded rows NAMED** — they
   are the non-R/C lines (`C3716677`, `C504007`, `C2286`, and `C5121458`, which
   is the board's entire function), where the Comment *is* the MPN and the check
   degenerates to a string comparing itself. `7/7` reads as complete coverage of
   a denominator that is not the file's.

6. **`jlc_twin.py`'s verdict depends on a flag the caller must remember.**
   Without `--adjudications 03_src/rules/twin_adjudications.yaml` this same
   board reports **11 CRITICAL**; with it, 0. The file is not auto-discovered.
   A gate whose verdict depends on an optional flag will eventually be run
   without it.

7. **THE BIGGEST ONE, AND IT IS A CLASS DEFECT: `via_in_pad: true` IS READ AS
   PERMISSION AND NEVER AS AN OBLIGATION. Nothing anywhere turns a via-in-pad
   into an order line, and no gate can see an open barrel under paste.**

   MEASURED. `grep -rn via_in_pad skills/` finds five readers and they split
   cleanly:

   | reader | what it does with the field |
   |---|---|
   | `escape_check.py:191,196,208` | **feasibility predicate** — `tier.get("via_in_pad", False)` makes a fine-pitch ring escape grade `ok` |
   | `route_and_stitch_generic.py:2046` | `vip = bool(c.get("via_in_pad", True))` — **defaults to TRUE**; the router will drop a barrel in a pad unless told not to |
   | `route_and_stitch_generic.py:973` | comment citing *"advanced-tier `via_in_pad`"* as the justification for the escape |
   | `fab_tiers.yaml:121,169` | the DECLARATION, `# POFV: resin-filled + capped, paid option` |
   | `templates/03_src/route.yaml:204` | a **different field with the same name** — a routing permission, not a fab capability |

   **So the capability flag is consumed three times as licence to place the via
   and zero times as a requirement to buy the process that makes it legal.**
   `jlc_4layer_advanced` even carries an `order_readme:` string for the
   small-via option — the mechanism for emitting an order line EXISTS on this
   very tier — and there is none for `via_in_pad`. Same class as the unread
   `order_readme:` field and M-FIELD's 9-of-47 unread reference keys.

   **It has already shipped.** `smc0985-cooksense` v1.7, SEALED: *"276 unfilled
   via-in-pad at 0.15 mm drill with no POFV ordered … nothing in `ORDER_README`
   orders POFV / resin-plugged vias"* — graded P2, dispositioned *recorded*.
   `pluto-cal-switch/02_parts/YAT-10A+/part.yaml:114-119` reasons about
   epoxy-plugged EP vias and reaches the same dead end. **This board makes
   three.**

   **Three separate changes, in order of value:**

   **(a) A NEW GATE — `R-VIP` — because none of this is currently checkable.**
   For every via whose DRILL intersects an SMD pad's copper, FAIL unless the
   board's via protection is filled/capped or the via is covered by mask on the
   PASTE side. It is cheap and purely geometric: intersect drill circles with
   pad polygons, then test the mask aperture on that side. **The known-bad
   fixture is this board as it stands — ten hits — and the known-good is the
   same board with `(filling yes)(capping yes)`.** A gate with both already
   available is a gate that can be shown to fail.

   **(b) `fab_tiers.yaml` must carry the order line, not just the capability.**
   Add alongside `via_in_pad: true` an emitted string in the same shape as the
   existing `order_readme:` — e.g. `via_in_pad_order_readme: "RESIN-FILLED +
   CAPPED VIAS (POFV) REQUIRED: <n> vias have their hole inside a solderable
   land"` — and have the release writer emit it whenever R-VIP finds ≥ 1 hit.
   **A declared capability with no emitter is how all three boards got here.**

   **(c) KiCad's own declaration is being silently defeated, and something
   should say so.** The `.kicad_pcb` carries `(tenting (front yes)(back yes))`
   and individual vias carry their own `(tenting …)`, but **a pad's mask
   aperture overrides both** and no tool warns. Worse, the `.gbrjob` — the one
   machine-readable carrier for `(covering)/(plugging)/(capping)/(filling)` —
   **is absent from the exported zip** despite `(creategerberjobfile yes)`, so
   even a correct declaration would not reach the fab. Fixing the job-file
   export is a prerequisite for (b) meaning anything downstream.

8. **THE FINDINGS LEDGER LOSES P2s BY CONSTRUCTION, AND IT LOST THE ONE ABOVE.**
   The via-in-pad defect in §7 item 8 was **already found on 2026-07-30** — the
   r2 layout lens logged the exposed-pad half as **L-09**, with the same seven
   coordinates and the same 66.9 % paste figure, and prescribed *"either add
   mask dams inside the EP or record the plugging requirement in the fab
   MANIFEST."* **Neither happened, and thirteen hours later a fab lens spent a
   fresh measurement pass rediscovering it.** How it was lost is mechanical and
   fixable:

   - `08_reviews/DISPOSITIONS.md` contains **zero `L-xx` ids** — not L-09, not
     any of them. Round-1 findings were renumbered into a private `P0-n`/`P1-n`
     scheme and the round-2 table has **no id column and no review-file
     column**, so no finding is greppable by the id the review gave it.
   - Every **P0 and P1** from the r2 layout lens got its own row. **All six P2s
     got none.** They were absorbed into a single line —
     `| P2 x25 across the four lenses | all | recorded in the review files; none blocking. |`
     — whose count (6 layout + 7 topology + 0 pin + 12 render = **25**)
     reconciles exactly. **The ledger knew precisely how many findings it was
     dropping.**
   - **The same commit did both.** `c7ebda44` (2026-07-30 22:34) added the r2
     layout review containing L-09 **and** the aggregate row that discarded it.
     Not a stale-input race — one author, one commit, one decision.
   - **The contract already forbids this.** `08_reviews/contracts.md:40-53`
     says *"One row per finding, across ALL reviews"* and reserves the verb
     `recorded — <note>` explicitly for P2s. There is no severity filter in the
     rule; one was applied anyway.
   - **And the audit cannot catch it, by construction.** The contract's audit
     line checks that *"every `DISPOSITIONS.md` row links an existing review
     file"* and that *"every **P0/P1** row has a non-empty disposition"* —
     **row → review, never review → row**, and scoped to exactly the severities
     that were not dropped. A finding that never becomes a row is invisible to
     it. `grep -rn DISPOSITIONS tests/` returns **0 hits**: no test references
     the ledger at all, and the project contract still calls the coverage check
     a *"Candidate machine check"*, i.e. unbuilt.

   **The fix is one gate and one contract row, and the fleet already contains
   the working pattern.** `crow-mic-pod-v2`'s ledger also groups P2s, but its
   group row **enumerates every id inside it**
   (`GAIN-1, CAP-1, PWR-1, POUR-1, …`), so nothing becomes ungreppable;
   `usb-hub-3s-v3` carries **62** individual P2 rows. Proposed:

   **(a) `t1_dispositions_coverage.py` — parse every `| <id> |` from every
   review file in `08_reviews/` and assert each id appears in
   `DISPOSITIONS.md`.** Direction review → row, ALL severities. Known-bad
   fixture: this project today (25 missing). Known-good: `usb-hub-3s-v3`.

   **(b) Amend `skills/pcb-design/templates/contracts/08_reviews/contracts.md`**
   so the audit line reads coverage in BOTH directions and drops the `P0/P1`
   scope, and so a group row is legal **only if it enumerates its ids**. Per
   CLAUDE.md the template is the source of truth and existing project copies
   re-sync on their next revision — so this is the change that makes the
   machine check above enforceable rather than advisory.

   **Why this matters more than the board.** The ten open barrels cost one paid
   fab option. The ledger defect cost a rediscovery, and would have cost the
   order if the second lens had not happened to look at the same copper.
   **A P2 that is counted and then discarded is worse than one never found**:
   the tally makes the ledger look complete.
