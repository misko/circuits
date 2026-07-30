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
