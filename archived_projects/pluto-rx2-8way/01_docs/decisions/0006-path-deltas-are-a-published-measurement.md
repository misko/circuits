---
id: 0006
date: 2026-07-28
status: accepted
tags: [topology, verification, rf]
---
# 0006 — The 8 path deltas are a PUBLISHED MEASUREMENT; what the board owes is CONSTANCY

## Context

BRIEF P8/A1: the application is AoA, and the user's own words are *"we can
offset path length / phase in software **if its constant**"*. D4 already
records the conclusion — the deltas are a published measured artifact, not a
design target. That conclusion is not executable as written: "publish the
delta" does not say which quantity, measured how, against what constant, per
unit or per design, or **what the BOARD has to do so that the number stays
true after it is published.**

P8 permits UNEQUAL paths. It does not permit UNKNOWN or DRIFTING ones. The
obligation this creates is **stability**, and stability is a property the
layout and the part choice buy — or fail to.

## Options

- **Treat it as a routing tolerance** ("match all eight to within X mm").
  REJECTED: it answers the wrong question. A software offset is only as good
  as the number it is given, and a tolerance band is not a number. It also
  cannot be met — the tapped path (ADR-0002) contains two resistors and a
  different topology, so it is unequal by construction.
- **Publish the DELAY delta only** (D4 as written). REJECTED as incomplete —
  amplitude and leakage are equally static, equally calibratable and equally
  useless unmeasured.
- **Publish delay, amplitude and leakage, per path and as deltas, with the
  conversion constant pinned to the ordered stackup, and achieve constancy
  BY CONSTRUCTION.** CHOSEN.

## Decision

### 1. What makes the deltas CONSTANT — four mechanisms, each a board property

**(a) The switch is ABSORPTIVE, and that is a first-order requirement, not a
nicety.** Deselected ports are internally terminated in 50 Ω (Figure 1,
PDF p1; "Return loss (terminated port)" rows, Table 3, PDF p7 — 15–23 dB typ
across the band). With a REFLECTIVE switch each deselected element is
short-circuited, so **which** elements are shorted changes with the
selection — and the mutual coupling seen by the SELECTED element therefore
changes state to state. That attacks CONSTANCY directly: the same antenna
would present a different environment in each of the eight states, and no
per-path constant could describe it. Absorptive termination holds every
deselected element at ~50 Ω in all eight states. **This is the property that
made the SPDT-tree alternative lose, and it is recorded here because it is
easy to mistake for a specsmanship detail.**

**(b) Equal geometric length, so THERMAL DIFFERENTIAL DRIFT is bounded.**
This is the mechanism D4 did not name. A microstrip's electrical length
drifts with temperature (Dk temperature coefficient plus the laminate's
in-plane CTE); for FR-4 the propagation-delay coefficient is **ESTIMATED at
+100 ± 100 ppm/°C** (M-IMPORT: derived from TC(Dk)/2 plus ~15 ppm/°C of CTE;
this vendor publishes none, and the bar is wide on purpose). The published
delta is a DIFFERENCE, so what drifts is

> `Δτ_drift = TC · ΔT · (L_i − L_j) · t_pd`

— **proportional to the length DIFFERENCE, not to the length.** At
`t_pd = 6.09 ps/mm` (ADR-0003) over a 40 °C excursion:

| length spread `ΔL` | Δτ drift | phase drift @6 GHz | verdict |
|---|---|---|---|
| **1 mm** (the radial star, ADR-0007) | 0.024 ps | **0.05°** | negligible |
| 20 mm (a naive rectangular fan-out) | 0.49 ps | **1.05°** | comparable to the AoA error budget |
| 20 mm, at the pessimistic end of the bar (200 ppm/°C, ΔT 60 °C) | 1.46 ps | **3.2°** | not negligible |

**The conclusion does not depend on the exact coefficient** — it depends on
`ΔL`, which the board controls absolutely. Equal-length routing is therefore
not cosmetic and not merely "nice for phase": it is what makes a PUBLISHED
number stay true across the temperature range the board is used at. That is
the argument for ADR-0007's radial star.

**(c) No vias, no layer changes, in any RF arm.** A via's inductance depends
on drill and plating thickness, which vary board to board and are not
specified per-hole. Nine arms with nine vias would be nine independent
uncontrolled series inductances on exactly the paths whose differences are
being published.

**(d) Identical, not mirrored, passive orientation** for `R_T1`/`R_T2`, same
reel, same lot. Mounting-inductance asymmetry is ~0.1 nH ≈ 3.8 Ω ≈ 2° at
6 GHz, and mirroring a pair converts solder-fillet and pick-orientation
asymmetry into calibration error. This is a **CPL fact**, not a schematic one.

### 2. Port assignment — and a counter-intuitive result

**`RF1…RF7` carry array elements 1…7; `RF8` carries the RX1 tap (element 8).
`RFC` is the single output to Pluto RX2.**

Pin map (Figure 22 / Table 8, PDF p20): RF1 = pin 24, RF2 = 2, RF3 = 4,
RF4 = 6, RF5 = 13, RF6 = 15, RF7 = 17, RF8 = 19, RFC = 22.

Two independent arguments both select RF1/RF8 for the tap, and the second one
is the opposite of the obvious instinct:

1. **Insertion loss.** RF1/RF8 are the best ports — 1.9 dB max at 4–6 GHz
   against 2.2–2.3 for the rest (Table 3, PDF p4). The tapped path is already
   20.26 dB down and is the SNR bottleneck of every relative measurement, so
   it gets the best port.
2. **Leakage.** The instinct is "give the reference the port with the BEST
   isolation" — RF4/RF5, 38 dB min. **That is the adjacent-property error.**
   The isolation column grades the port that is LEAKING, not the port that is
   listening; the interference on any dwell is the power sum over the SEVEN
   DESELECTED ports. Choosing the reference port therefore chooses which term
   is REMOVED from that sum (the tapped element leaks ~20 dB down, so it
   effectively drops out). Removing the LARGEST term means putting the
   reference on the WORST-isolation port. Measured from Table 3 (PDF p5),
   4–6 GHz minimum column:

   | reference on | Σ leakage of the other seven | vs best |
   |---|---|---|
   | **RF8 (29 dB, "worst")** | **−23.4 dB** | — |
   | RF4 (38 dB, "best") | −22.5 dB | **0.9 dB worse**, and +0.3 dB more IL |

   Both objectives agree, and the naive choice loses on both.

**RF8 rather than RF1** because the reference then sits at code `V1V2V3 =
111`, the LAST slot of a straight 0…7 count, so the X/2 marker falls at the
frame boundary where a free-running PIO wraps (ADR-0005). Geometrically RF8
(pin 19) is adjacent to RFC (pin 22) on the package's top side, which is what
lets the pickoff and both Pluto-facing jacks cluster on one edge (ADR-0007).

### 3. What the release SHIPS

| quantity | per path | delta vs RF1 | why |
|---|---|---|---|
| routed electrical length, mm | yes | yes | the raw geometric fact |
| propagation delay, ps, at **6.09 ps/mm pinned to `JLC04161H-7628`** | yes | yes | the number software offsets with |
| `\|S21\|` vs frequency, 70 MHz – 6 GHz | yes | yes | amplitude is as static and as calibratable as phase |
| `∠S21` vs frequency | yes | yes | the AoA quantity itself |
| **the 8 × 8 leakage matrix**, at the six datasheet band rows | yes | — | NEW: ADR-0002's T3 makes the reference dwell leakage-limited above ~2 GHz, and the subtraction needs these coefficients |
| the **dark-state floor** (`V4 = 1, V1..V3 = 0`) | — | — | the instrument's own noise floor, and the OWED ten-barrel SMA port-to-port isolation |

**The conversion constant ships WITH the delta.** 6.09 ps/mm is pinned to
this stackup; a stackup change silently invalidates every published
picosecond, so the artifact states the stackup by name.

**It is a PER-UNIT artifact.** The tap arm, the connectors and the assembly
are unit-to-unit, so the published table describes THE BOARD IN HAND and
names which unit was measured. A design-level figure would be a lie for every
other unit.

**The vendor bound it is checked against** (canon M1 — a reference the design
did not produce): PE42482A-X publishes **relative insertion phase with
min/typ/max** (Table 3, PDF p8). At 6 GHz, RF2−RF1 is −9.4/−2.8/+3.8°,
RF3−RF1 −11.2/−5.7/−0.3°, RF4−RF1 −35.8/−26.3/−16.9°. A measured table that
falls outside those windows after the routed-length term is removed is a
FINDING, not a measurement. **No SPDT alternative publishes phase data of any
kind** — the word does not occur in BGS12WN6's document — which is why only
one part could support this ADR at all.

**If no VNA is available**, the release ships the routed lengths and the
derived delays and states plainly that `S21` and the leakage matrix are
**UNMEASURED**. A partial result honestly reported is worth more than a
passing claim.

## Consequences

- **`03_src/rules/nets.yaml` carries `RF50` as one class of eleven nets**, and
  its `intent:` states that the width is an IMPEDANCE width — widening an RF
  class "to be safe" detunes the line and is as wrong as narrowing it.
- **The routing rules for the fan are constraints, not preferences**: L1 only,
  no vias, no layer changes, solid L2 underneath, ground-via fence at
  ≤1.37 mm (λg/20 at 6 GHz). They are what mechanism (c) above buys.
- **`RX1_TAP_MID` carries a ≤1.37 mm span budget.** It is the interior of a
  lumped element; longer than λg/20 and the two-resistor arm stops being one
  lumped element and starts being a transmission line with its own delta.
- **A CPL constraint exists before there is a CPL**: `R_T1` and `R_T2` at
  identical rotation. It goes on the placement checklist now, because at
  export time it is invisible.
- **The release cannot claim P8 met without the table.** `CHECKLIST.md`
  carries it as a release gate, and BRIEF acceptance criterion G-P8 stays
  `unmet` until the artifact exists.
- **If the leakage matrix comes back materially worse than Table 3's minima**,
  the cause is the ten-barrel SMA field, not the switch — and that is the
  measurement `02_parts/README.md` already records as OWED. A −21.5 dB switch
  behind a −18 dB connector field is a −18 dB board.
