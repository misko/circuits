# The SE-corner label-ownership blocker — measured to a conclusion, NOT fixed

Date: 2026-07-29 (v1.8 pass). Status: **OPEN ORDER-BLOCKER.** This file exists so
the next pass inherits a measurement and a decision, not a search.

## What the defect is

Three connector designators do not identify their own connector. Measured on the
v1.7 board with `pcbnew`, silk text bounding box to footprint **courtyard**
bounding box (the earlier reports measured 0.161 mm pad-to-pad; courtyard-to-box
gives 0.141 mm — same finding, different reference):

| silk string | box | distance to the part it NAMES | distance to a DIFFERENT connector |
|---|---|---|---|
| `J_ISOLOOP` | x[183.764, 188.836] y[100.386, 101.614] | **2.719 mm** (J_ISOLOOP) | **0.141 mm** (`J_RH_EXHAUST`) |
| `J_ESTOP` | x[192.386, 193.614] y[73.358, 77.402] | **0.141 mm** (J_ESTOP) | **0.141 mm** (`J_DOOR`) — an EXACT TIE |
| `J_DOOR` | x[185.649, 189.351] y[83.146, 84.374] | 4.404 mm (J_DOOR) | nearer to `D_DOOR` |

`J_ISOLOOP` is the **NOT-SELV 30 V isolated contactor loop.** Its designator is
printed on a JST-GH humidity-sensor header.

## Why no silk-only pass can fix `J_ISOLOOP` — the four directions, measured

`J_ISOLOOP`'s courtyard is x[191.555, 199.245] y[87.655, 102.345]. For its
designator to be OWNED it must be nearer to that box than to any other
`J*`/`F*`/`TP*` part. Every direction out of that box is closed:

| direction | what is there | free? |
|---|---|---|
| EAST | `x > 199.245` → the board edge (`J_MODE` courtyard already reaches 200.495) | **no** |
| SOUTH | `y > 102.345` → the board outline ends at y = **102.000** | **no** |
| NORTH | `y < 87.655` at x[193.755, 199.245] is `J_DOOR`'s courtyard (y up to 87.155). The one pocket, x[191.555, 193.755] y[82.795, 87.155], is **1.155 mm from J_DOOR against 2.155 mm from J_ISOLOOP** — J_DOOR wins | **no** |
| WEST | `U_OPTO` x[178.935, 191.065] y[87.165, 92.835], then `J_RH_EXHAUST` x[180.605, 191.395] y[93.755, 100.245]. The only gap is the y[100.245, 102.345] sliver where the label already sits, 0.141 mm from J_RH_EXHAUST | **no** |

**The generator's own message — `nearest legal site inf mm away` — is literally
true.** There is no owned site. This was verified rather than assumed, because
the same corner has produced a wrong "nearest site" number three times.

Moving things does not obviously help either: `J_RH_EXHAUST` cannot go west
(`C_SWRHE` reaches x 178.025 and overlaps its y band by 0.020 mm) and cannot go
north (`U_OPTO`'s south face is 0.920 mm away); `U_OPTO` cannot go west
(`Q_SWRHE` x[174.025, 177.975] overlaps its y band) and cannot go north
(`R_OPTOLED`'s south face is 0.790 mm away); `J_ISOLOOP` is flush to the south
edge and its west limit is set by the 2.0 mm ISO moat derivation.

## Why the `J_ESTOP` / `J_DOOR` half is NOT a silk problem at all

Those two are **the same part** (`C189896` SM05B-GHS-TB), 0.090 mm of courtyard
gap apart, and **both harnesses are electrically identical 2-wire dry contacts on
pins 1–2** — a swapped pair mates perfectly and looks right. Traced in the
netlist: `ESTOP_OK` feeds `U_AND1.6` *and* `U_FAULTAND.3` (the latch SET);
`DOOR_OK` feeds only `U_OSCLR.1`. Swapped, an E-stop press holds the PRESS
one-shot cleared and pole B still breaks the isolated loop at `J_ISOLOOP` so the
contactor opens — **but `ESTOP_OK` stays high, nothing latches, and the coil rail
stays up**: release the button and everything resumes with no deliberate re-arm.

A perfectly-placed designator does not stop a connector that mates. **The remedy
is a mechanical key — ADR-0018 decision C applied a second time.** That is the
third repetition of the same shape on this board: ADR-0018 keyed ONE of five
identical housings; ADR-0020 fixed one of six expander pins; ADR-0023's dossier
carried the hot-corner R_ON on one of eleven pads.

## What is and is NOT mitigation — stated plainly

**IS mitigation:** every refdes is also on **F.Fab**, and the **CPL is
authoritative** for assembly. A machine does not read silk. So the consequence
for ASSEMBLY is close to nil.

**IS NOT mitigation, for the case that matters:** a human plugging a harness into
a live 30 V terminal reads the silk. And `J_ISOLOOP` already carries two
independent self-identifying strings adjacent to it — `NOT SELV` at
(189.375, 85.125) and `ISO 30V` at (190.750, 86.500) — plus the full
self-identified north-stack caption `J_ISOLOOP (SE CORNER) = ISOLATED 30V
CONTACTOR LOOP -- NOT SELV -- POLES 1=C 2=LOOP 3=LOOP 4=E`. **A KF350 3.5 mm
screw terminal cannot be cross-plugged with a JST-GH**, so the J_ISOLOOP failure
is misidentification, not mis-mating. `J_ESTOP`/`J_DOOR` are the opposite: the
plugging error is physically possible and the silk is tied.

## Two things this pass deliberately did NOT do, and why

1. **A floorplan nudge to open a slot for `J_ISOLOOP`.** The four-direction table
   above shows there is nothing to open without moving `U_OPTO` or
   `J_RH_EXHAUST`, and both are blocked by their own neighbours. A nudge that
   fixes 1 of 3 refs while re-racing a stochastic router and re-spending the
   four-lens battery is a bad trade.
2. **Suppressing the designator to `refdes_waiver.json`.** "Silence beats a lie"
   is the right instinct — a string 0.141 mm from the WRONG connector actively
   misinforms, where an absent one sends the reader to F.Fab. But
   `generate_board` WRITES that file for itself and `P-SILK-REF` READS it, so a
   suppression there is a self-waiver, and a sibling agent is already patching
   exactly that hole. Landing a safety-relevant suppression through a mechanism
   known to be self-certifying would be the `jlc_twin` failure again.

## The recommended fix, sized

**A part change plus an east-column repack**, in one pass:

- Take `J_DOOR` (or `J_ESTOP`) out of the GH-5 family. ADR-0018 already measured
  the candidates: `S4B-ZR-SM4A-TF` (JST ZH-4) is **0.200 mm NARROWER** in the
  column than GH-5 and is **already on this BOM** (`C485354`, J_MODE) — zero new
  lines.
- **BUT NOT ZH-4 AS-IS**: J_MODE is ZH-4, so J_DOOR-as-ZH-4 becomes
  cross-mateable with it, and a MODE harness in J_DOOR shorts 3V3 to
  `DOOR_RAW_IN` through pole B = **reads door CLOSED = fail-permissive**. Checked
  before recommending. A 3-circuit ZH (`S3B-ZR-SM4A-TF`) carries everything the
  door needs (3V3, sense, GND), differs from J_MODE in circuit count, and would
  FREE roughly 1.5 mm of east-column width — which is the space the label
  ownership problem needs. **Sourcing is unverified; verify stock before
  committing to it** (ADR-0018 rejected the 4-circuit GH on exactly this ground:
  genuine JST read stockCount 0/1).
- Current column slack, measured: H4→J_MODE 0.203, J_MODE→J_ESTOP 0.235,
  J_ESTOP→J_DOOR 0.090, J_DOOR→J_ISOLOOP 0.510, J_ISOLOOP→J_RH_EXHAUST 0.160 =
  **1.198 mm total.** A part that grows the column by more than that forces a
  re-derivation of the 2.0 mm ISO moat (measured 2.126 mm today, +0.126 on the
  rule).

This closes the label blocker AND the v1.7 pin lens's finding C2 (the
transposition that de-latches the E-stop) with one change, which is the argument
for doing them together rather than chasing silk first.

## Board-wide context, so the next pass sizes it right

`silk ownership: 179/244 owned, 57 degraded, 8 unplaced` on the v1.8 rebuild.
This is **not** an SE-corner problem — it is board-wide placement density, and
the SE corner is only where it lands on a safety connector. Fixing three refs
does not fix the class; `MIN_OWNERSHIP_MARGIN_MM = 1.5` degrading through a
`(1.5, 1.0, 0.5, 0.1)` ladder and then "taking the NEAREST" is what produces an
exact tie, and that ladder lives in `03_src/cooksense/fix_silk_placement.py`
(project-local, editable). `OWNERSHIP_FIX` currently names only
`("J_DOOR", "J_ESTOP", "J_MODE")` — **`J_ISOLOOP` and the two pod housings are
not in it at all**, which is why nothing even tried for the 30 V terminal.

---

# UPDATE 2026-07-29 (v1.8 attempt 3) — the sourcing question is ANSWERED, and
# the pin-count key inside the GH family turns out to be FAIL-PERMISSIVE

Two things landed after the section above was written. Both change what the next
pass should do, so they are recorded here rather than re-derived.

## 1. The rebuild now DIES IN THE SILK PASS, and ADR-0024 is the cause

`rebuild_all.sh --reroute` (attempt 3, `06_build/rebuild_v18c.log`) does not reach
the router at all. It exits **1 at stage 1b/7**:

    FATAL: no clear silk position for ['R_DOORPD'] — a refdes that cannot be
    placed must not be left in a milled void

The chain, read out of the log and confirmed against the stage-1 board:

1. ADR-0024 added `R_DOORS` and `R_ESTOPS` and this floorplan anchored them into
   the pocket **x[189.6, 193.7] y[73.2, 79.3]**, whose comment (above, line ~752)
   records it as *"4.1 x 6.1 mm and empty"*.
2. `R_DOORS` lands in the **SAFETY-TEXT CLASS** (10 members this run — membership
   is GEOMETRIC, "every label within 8.0 mm of a safety housing", so it changes
   run to run), which forces its designator to **h 0.600** and gives it priority.
3. At h 0.600 rot 90 that designator needs `R_DOORPD`'s slot and takes it:
   `R_DOORS displaces R_DOORPD from x[189.436,190.664] y[75.392,79.808]`.
4. `R_DOORPD` is re-placed at **(191.800, 74.150)** — which is inside `J_ESTOP`'s
   courtyard y-band (`J_ESTOP` bbox y[65.505, 76.255]; `J_DOOR` starts at
   y 76.385, so the two are 0.130 mm apart and the watershed is y ≈ 76.32).
5. The CROSS-NAME rule then correctly refuses it: *"R_DOORPD carries J_DOOR's
   identity token but its label centre is 6.143 mm from J_ESTOP and only
   9.217 mm from J_DOOR"* — a resistor named `R_DOORPD` printed on the E-stop
   connector. Relocation finds no slot at any rung of the
   1.5 / 1.0 / 0.5 / 0.1 mm ladder, and the pass dies.

**THE FINDING, and it is the reusable one: the pocket was measured EMPTY OF
COURTYARDS, and it was not empty. It was `R_DOORPD`'s DESIGNATOR SLOT.** On the
v1.7 board `R_DOORPD`'s label occupied x[189.038, 190.162] y[75.223, 80.177] —
squarely inside the "empty" pocket. Silk is a placement resource with its own
occupancy, and a floorplan comment that clears a region by checking courtyards
has checked the wrong layer. Two 0402s whose COPPER fits caused a build failure
because their DESIGNATORS did not.

The floorplan's own justification for putting them there is still sound and is
the lever for the fix: *"Both resistors carry NO DC, so their span is
electrically free — unlike R_DOORPD/R_ESTOPPD, which must stay AT the connector
pin because that is where the divider acts."* ADR-0024 Decision B says the same
("they contribute ZERO to the rejection arithmetic"). `U_SCHM` is at
**(174.000, 60.000)**, ~25 mm west of the connector column, so `R_DOORS` /
`R_ESTOPS` have the whole run to sit on. **Do not spend the SE corner on them.**

## 2. The keyed-connector sourcing spike — ANSWERED, with a candidate the earlier
##    recommendation would have got wrong

The section above asks for `S3B-ZR-SM4A-TF` stock to be verified before
committing. **Verified, live JLC/LCSC catalog reads 2026-07-29** (data only — no
part was swapped; a connector change on a safety input is the user's call):

| MPN | LCSC | stock | lib | pitch | ckts | I | courtyard W vs GH-5 10.700 | fits the 1.198 mm column slack? |
|---|---|---|---|---|---|---|---|---|
| **S3B-ZR-SM4A-TF** ZH-3 | **C72591** | **38 697** | ext | 1.50 | 3 | 1 A | 9.000 (**−1.700**) | yes — frees more than the whole slack |
| **SM03B-SRSS-TB** SH-3 | **C160403** | **52 328** | ext | 1.00 | 3 | 1 A | 6.800 (**−3.900**) | yes |
| S3B-PH-SM4-TB PH-3 | C265101 | 1 673 | ext | 2.00 | 3 | 2 A | 11.200 (+0.500) | width yes; **depth +3.800 inboard** |

Both top candidates SHRINK the east column, which is the resource the
`J_ISOLOOP` label-ownership blocker needs — so the part change and the label
blocker close together, as the section above predicted.

**THE DISQUALIFICATION THAT MATTERS MOST, because it is the one a reasonable
reader would have chosen: a 3-circuit JST GH (`SM03B-GHS-TB`, C514175) IS
FAIL-PERMISSIVE AND IS WORSE THAN THE DEFECT IT FIXES.** A pin-count change
INSIDE the GH family is not a key. It blocks the wide→narrow direction only:
a `GHR-05V-S` (B = 7.50 mm) cannot enter a 3-circuit GH shroud (~5.0 mm cavity,
≈2.5 mm interference) — but the **narrow→wide direction is a full, pitch-matched,
multi-circuit engagement**, because the pitch is 1.25 mm on both. A `GHR-03V-S`
door harness left-seated in `J_ESTOP`'s GH-5 shroud puts 3V3 / sense / GND on
`3V3` / `ESTOP_RAW_IN` / `GND`, and the reed bridges 3V3 → `ESTOP_RAW_IN`:
**the E-stop reads NOT-ASSERTED with no E-stop button attached.** GH-2 (C189893)
fails identically with 4 seat positions. GH-4 is dead twice over — same
intra-series cell, and `C189895` reads **stock 1** on a fresh read today, exactly
as ADR-0018 option E recorded.

Also disqualified, each by a named cell: **ZH-4** (= `J_MODE`, the already-known
cell); **ZH-5** C485355 (a `ZHR-4` enters a ZH-5 shroud with 1.5 mm slack →
mode pole B bridges 3V3 → `DOOR_RAW_IN` → door reads CLOSED — and it is 0.102 mm
over the column slack); **ZH-6** C265070 (same, +2.800 mm); **ZH-2** C265329 —
worth reading, because it is the worst of the set: a `ZHR-2` in `J_MODE`'s ZH-4
shroud has **3 seat positions and one of them is circuits 3–4**, where the door
reed bridges `KEY_RELAY_ALLOWED` → `COIL_EN_IN` = pole A = **the oven door closes
the physical MANUAL rail cut.** That is ADR-0018's hazard re-created verbatim.
**Molex PicoBlade** C293630 is REJECTED on the precautionary principle rather
than on evidence: it shares GH's 1.25 mm pitch exactly, so if the shrouds do
intermate the contacts align on EVERY circuit, and the cross-section drawings
needed to settle it were not available. A key whose blocking claim is unproven
is not a key.

**Ranked, for the human decision:**

- **Rank 1 — ZH-3 `S3B-ZR-SM4A-TF` / C72591.** Deep genuine-JST stock, KiCad
  footprint ships in-tree, and **no new crimp system** — `SZH-002T-P0.5`
  (C246761, stock 113 425) is already required for `J_MODE`. One
  possibly-mateable cell (into `J_MODE`, same series), and it is RESTRICTIVE in
  **both** seat positions: left-seated the harness GND lands on
  `KEY_RELAY_ALLOWED` and shorts the AND-chain output; right-seated it lands
  directly on `COIL_EN_IN` and holds it at 0 V. Neither seat bridges 3↔4.
  **Two conditions, neither optional:** (a) pin it 1 = 3V3, 2 = `DOOR_RAW_IN`,
  3 = GND and build the harness with THREE wires — the GND on circuit 3 is what
  makes both seats *actively* restrictive instead of merely open-pinned; a
  harness built on circuits 2–3 would put the right seat on `J_MODE` 3–4 = pole
  A = permissive. (b) depth grows **+1.600 mm inboard** (8.000 vs 6.400) and the
  inboard neighbours of `J_DOOR` were NOT checked — **unverified.**
- **Rank 2 — SH-3 `SM03B-SRSS-TB` / C160403.** Safest of all: **zero
  possibly-mateable cells anywhere on the board** (1.00 mm pitch is unique
  here), no seat-position argument needed, frees 3.900 mm, depth +0.160 mm
  (free). Ranked second only on BUILDABILITY: `SSH-003T-P0.2` takes AWG#32–28 at
  0.4–0.8 mm insulation OD, and a field run to an appliance reed or an E-stop
  button wants AWG#26 or heavier (the existing GH harness is spec'd #30–26).
  **If the harness can honestly be built in AWG#28, SH-3 should be rank 1** — it
  is the only option needing no argument about how a plug seats. Adds a third
  crimp system; genuine `SHR-03V-S-B` C268100 reads stock 0 (`APSHR-03V-S`
  C392108 / 25 405 is the stocked JST-compatible plug).
- **Rank 3 — PH-3 `S3B-PH-SM4-TB` / C265101.** Zero mateable cells, 2 A, best
  wire range (AWG#24–30), excellent harness stock (`PHR-3` C265393 / 91 778).
  Blocked on geometry (+3.800 mm depth) and a thin 1 673 header stock for a
  DO-NOT-SUBSTITUTE safety part.

**WHICH connector to change is also a human call, and there is an argument the
section above did not make.** It proposes `J_DOOR`. But `J_ESTOP` is the input
whose transposition costs the LATCHING property, so giving *`J_ESTOP`* the unique
housing means the higher-integrity input cannot accept any other harness on the
board. Electrically the two are interchangeable for this purpose — same 1/2/GND
structure — and whichever stays GH-5 remains covered by ADR-0024's already-proven
restrictive cells against the pods.

**Still unverified, stated rather than glossed:** Mouser/DigiKey availability of
every plug housing and crimp contact (LCSC only was read; `ZHR-3` C160376 and
`SHR-03V-S-B` C268100 both read LCSC stock 0, which for self-supplied harness
parts is not decisive but is not verified either); depth clearance inboard of
`J_DOOR`/`J_ESTOP` for the +1.600 mm ZH growth; `escape_check.py` at 1.00 mm
pitch for SH-3 (GH passed at 1.25 and ZH at 1.50, so ZH-3 is covered by
precedent and SH-3 is not); the 2.126 mm ISO moat re-derivation (both top
candidates SHRINK the column so it should only get easier, but ADR-0018 records
the moat is 2-D and it was not re-solved). Every stock figure is LCSC catalog
`stockCount`, not JLC assembly-warehouse allocation.

---

# UPDATE 2026-07-29 (later) — THE CONNECTOR SPIKE IS NO LONGER AN ACTION, AND THE
# `J_ISOLOOP` BLOCKER MAY CLOSE FOR FREE. Read this before acting on anything above.

**USER DECISION, 2026-07-29: neither `J_DOOR` nor `J_ESTOP` is installed in this
build** (no access to those signals). Worked in **ADR-0025** (`proposed`, awaiting
a user decision); ADR-0024 carries an addendum. What that does to THIS file:

1. **DO NOT pursue the keyed-connector change.** The ZH-3 (`C72591`, 38 697) /
   SH-3 (`C160403`, 52 328) sourcing table and the GH-3 fail-permissive
   disqualification above are all still CORRECT and are retained as a measured
   spike — but the transposition hazard they were sized to fix is **closed by
   scope**: with no housings fitted there is nothing to cross-mate. Spending a
   part change on it now would be paying for a hazard that no longer exists.
2. **`J_ESTOP`/`J_DOOR` are 2 of the 3 mis-owned designators, and they leave with
   the parts** if the footprints are removed (ADR-0025 option O5).
3. **THE ONE THAT MATTERS: removing `J_DOOR` makes `J_ISOLOOP`'s designator
   OWNABLE.** The four-direction table above proves the only candidate pocket is
   `x[191.555, 193.755] y[82.795, 87.155]` and that `J_DOOR` wins it. Re-measured
   at that pocket's centre (192.655, 84.975), nearest `J*`/`F*`/`TP*` courtyard:

   | present | nearest | 2nd | margin |
   |---|---|---|---|
   | all (today) | `J_DOOR` **1.100 mm** | `J_ISOLOOP` 2.680 mm | J_ISOLOOP loses |
   | `J_DOOR` gone | `J_ISOLOOP` **2.680 mm** | `J_ESTOP` 8.769 mm | **+6.089 mm** |
   | both gone | `J_ISOLOOP` **2.680 mm** | `J_RH_EXHAUST` 8.870 mm | **+6.190 mm** |

   `MIN_OWNERSHIP_MARGIN_MM` is 1.5, so this clears it 4×. The 30 V NOT-SELV
   render-lens P0 — declared above to be unfixable by any silk-only pass, which
   was true — closes as a SIDE EFFECT of the scope reduction. `OWNERSHIP_FIX` in
   `fix_silk_placement.py` still names only `("J_DOOR","J_ESTOP","J_MODE")`, so
   **`J_ISOLOOP` must be ADDED to it** or nothing will try.
4. **CORRECTION to section 1 of the previous update: the "4.1 x 6.1 mm empty"
   pocket was worse than "R_DOORPD's designator slot".** Measured on the sealed
   v1.6 board, it also held **`J_ESTOP`'s designator** (x[187.978, 192.022]
   y[77.266, 78.494]) **and `J_DOOR`'s** (x[189.149, 192.851] y[75.146, 76.374]).
   Triple-booked before ADR-0024 added anything. The reusable finding is unchanged
   and stronger: a floorplan comment that clears a region by checking COURTYARDS
   has checked the wrong layer.
5. **CORRECTION, measured: marking parts NOT-ASSEMBLED does not free one micron of
   silk.** `fix_silk_placement.py` contains no `dnp` / `exclude_from_bom` /
   population reference at all (grepped). A DNP part still gets a designator
   placed, so DNP-ing `R_DOORS`/`R_ESTOPS`/`J_DOOR`/`J_ESTOP` leaves the stage-1b
   `FATAL: no clear silk position for ['R_DOORPD']` exactly where it is. Only
   REMOVAL from the netlist, or MOVING the parts west toward `U_SCHM` (174, 60),
   frees the pocket. Do not expect the FATAL to dissolve from a BOM change.

---

# CLOSED 2026-07-29 (v1.8, ADR-0025) — and the closing pass found a SECOND defect
# of the SAME SHAPE in the code that was supposed to fix the first

**`J_ISOLOOP` OWNS ITS LABEL. Measured on the built board by the pass's own
VERIFY/RESIDUAL lines, not predicted:**

    VERIFY   J_ISOLOOP  label centre 8.000 mm from own part
                        vs 13.656 mm from J_RH_EXHAUST  (lead +5.656 mm)
                        -> OWNS ITS LABEL

against `MIN_OWNERSHIP_MARGIN_MM = 1.5`. The three hazard captions also improved
and are now all at the block body: `ISO 30V` 0.085 mm, `NOT SELV` 0.117 mm,
`1C2L3L4E` 0.085 mm. **The line above that said `NOT SELV`'s nearest site
measured 11.086 mm is therefore WITHDRAWN** — it was true while `J_DOOR`'s
courtyard held the north pocket and it is not true now.

## What actually closed it, in order

1. **`J_DOOR` left the NETLIST** (ADR-0025 D1 — the user has no door signal).
   That opened the one direction the four-direction table above proved closed.
2. **`J_ISOLOOP` was ADDED to `OWNERSHIP_FIX`.** The list named only
   `("J_DOOR","J_ESTOP","J_MODE")`, so *nothing had ever tried* for the 30 V
   terminal. It now reads `("J_ESTOP","J_ISOLOOP","J_MODE")`.
3. **A latent contradiction in `fix_silk_placement.py` had to be repaired first,
   and step 2 is what made it reachable.** The first rebuild after adding the ref
   died at stage 1b/7 with

       FATAL: no clear silk position for ['J_ISOLOOP']

   PASS D0 arms a 2.6 mm hazard-caption reserve around `J_ISOLOOP` at
   x[188.975, 201.825] y[85.075, 104.925] and evicts every silk label inside it,
   **`forbid`ding the band** so an evictee cannot be re-placed back in. But the
   loop ran over `sorted(fps)` *including `J_ISOLOOP` itself*, whose courtyard
   x[191.555, 199.245] y[87.655, 102.345] is **WHOLLY INSIDE the reserve.** So
   every position from which its designator could own itself was forbidden to it
   while `need_owner` was simultaneously required — **unsatisfiable by
   construction.** One guard clause: a hazard reserve may not evict its own
   owner. Measured safe rather than assumed — with the designator left in place at
   x[192.809, 197.791] y[86.438, 87.562] none of the three captions collides with
   it in x, and the captions are placed AFTER the eviction loop so a future
   collision would be reported rather than silently dropping a hazard warning.

## THE REUSABLE FINDING, and this corner has now produced it TWICE IN TWO PASSES

**A rule that clears a region by checking the wrong kind of occupancy will report
the region as free.**

| pass | what cleared the region | what it missed |
|---|---|---|
| v1.8 attempt 3 | the floorplan cleared the SE pocket by checking **COURTYARDS** | three DESIGNATORS were in it (`J_ESTOP`, `J_DOOR`, `R_DOORPD`) |
| v1.8 attempt 4 | the caption reserve cleared its band by checking **FOREIGNNESS** | the OWNER is not foreign |

Both were honest failures — each pass refused to place rather than degrading —
and that is the only reason either was findable. A silk pass that fell back to
"nearest slot" would have shipped both.

## What is NO LONGER an action, and what the E-stop half became

The `J_ESTOP`/`J_DOOR` transposition half of this file (the exact 0.141 mm tie)
is gone, but **not** in the way the update above predicted. `J_DOOR` was deleted;
`J_ESTOP` stayed POPULATED behind a removable shorting plug so a real E-stop can
be fitted later without a copper revision. **That decision resurrected the keyed
connector spike this file's previous update told the next pass to abandon** — and
for a reason the abandonment did not consider: with only one connector left, the
travelling object is the PLUG, and a GH-5 shorting plug bridging circuits 1-2
lands on switched-3V3-to-GND on all four sensor-pod housings. So `J_ESTOP` is now
**SH-3 `SM03B-SRSS-TB` / `C160403`** (stock 52 323 live, `escape_check` at
1.00 mm pitch PASSES on all five tiers — the gap this file listed as unverified),
with the sense node on **circuit 3** because circuit 3 is the one circuit that
cannot align in any foreign shroud. Full derivation in ADR-0025 D5.

**Retaining the measured spike after its motivating hazard closed is what made
that possible.** The sourcing table above was written for a transposition hazard
that scope removed; it turned out to answer a question nobody had asked yet.

## Two numbers in this file that the closing pass CORRECTED

- **`escape_check.py` at 1.00 mm pitch: no longer unverified.** PASS, all five
  tiers, floor `jlc_2layer_default`, 2026-07-29.
- **`SM03B-SRSS-TB`'s MP tabs are the outermost copper and overhang its mouth
  face.** The column table above compares COURTYARDS (6.800 vs 10.700) and that
  is right, but the first anchor at the GH-5's own x coordinate produced **two
  `copper_edge_clearance` errors at 0.2250 mm against a 0.300 mm rule** — MP pad
  bb reaches local y +2.775 where F.Fab stops at +2.575, and the GH-5's MP centre
  is at only +1.350. **An SH is not a small GH**, and predicting an east face
  from a footprint's pad CENTRES rather than pad BOUNDING BOXES is what got it
  wrong. Fixed by moving the anchor 0.400 mm inboard (0.625 mm clearance).
