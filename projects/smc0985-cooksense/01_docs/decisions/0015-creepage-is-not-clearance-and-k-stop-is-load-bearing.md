# ADR-0015 — Creepage is not clearance, and K_STOP is load-bearing geometry

- **Status:** accepted, 2026-07-26
- **Supersedes:** nothing. **Amends:** ADR-0012 (non-conductive enclosure), whose
  method note is vindicated here.

## Context

The H4 mounting hole's keypad-to-SELV isolation was ruled a FAIL and then
un-ruled the same day. Nothing about the board changed. What changed was
which **quantity** the number was understood to be.

`cooksense.kicad_dru`:

```
(rule "keypad_isolation_6mm"
  # brief section 4/7 + ADR-0001: ... must hold >=6mm creepage
  (condition "A.NetClass == 'KEYPAD_ISO' && B.NetClass != 'KEYPAD_ISO' && B.NetName != ''")
  (constraint clearance (min 6.0mm)))
```

The comment requires **creepage**. The constraint is written in `clearance`
because KiCad's DRU language **has no creepage primitive**. The rule therefore
requires one property and measures another.

## Decision 1 — the notch counts, because it is a notch and not a groove

IEC 60664-1 defines a minimum groove width **X** (1.5 mm at pollution degree 3)
below which a groove is **not** credited toward creepage — the path is measured
straight across. That rule governs a **groove: a channel with material at the
bottom**, where the question is whether contamination bridges it.

**The notch is 1.000 mm wide** (y[48.800, 49.800]), i.e. **below X**. State that
plainly: omitting it is what allowed the groove rule to be applied here at all.
The rule still does not apply, for a reason unrelated to width.

H4's feature is a **through-notch reaching the east board edge** —
`x[191.500, 200.000]` where 200.000 **is** the board edge, which is exactly why
ADR-0012 records it as OUTLINE geometry with no router-bit minimum and no
internal-cutout surcharge. There is no surface across it to creep along,
nothing to bridge, and it drains at the open end. **Creepage genuinely goes
around it.**

Two clarifications, both because getting them wrong is how the false ruling
happened:

- The provision reducing X to one third of the associated clearance applies where
  the associated **clearance** is below 3 mm. It is not needed here, and it must
  not be checked against the 6 mm **creepage** requirement — an earlier note did
  exactly that.
- The 3.000 mm disc **overhangs the notch by 0.800 mm** (centre y52.000 vs notch
  south edge y49.800). A disc roofing a *blind* slot would be a capillary trap;
  this notch is open at the board edge and the disc spans only x[190.000,
  196.000] of a notch running x[191.500, 200.000], so **4.000 mm stays open and
  it drains**. The overhang does reshape the creepage path, and the derivation
  below accounts for it.

Applying the groove rule to it was the error. The two figures are:

| figure | method | question | requirement | verdict |
|---|---|---|---|---|
| **6.5984 mm** | **creepage** — surface path around the notch | how far along a surface? | **>= 6.000 mm** | **PASS** |
| 4.0286 mm | clearance — straight line | how far through air? | << 1 mm at 30 V, PD3, mat. group IIIa | PASS wide |

They were never in conflict.

### The geodesic, re-derived independently (canon M1)

The taut path is **not** the naive one, because the fastener disc overhangs the
notch: |disc centre → notch SW corner| = 2.6627 mm < the 3.000 mm disc radius, so
a straight run at the NW corner would cross the void. The path skirts the west
edge:

| leg | from → to | length |
|---|---|---|
| 1 | disc boundary at x=191.500, y = 52 − √(3² − 1.5²) = 49.4019, up the notch's west edge | 0.6019 mm |
| 2 | notch NW corner (191.500, 48.800) → `K_STOP.3` pad edge (197.450, 45.620, r 0.750) | 5.9965 mm |
| | **total** | **6.5984 mm** |

Agrees with the `I-HW` gate's 6.598 mm to 0.0004 mm by a different construction.

**ADR-0012's method note was right for the reason it was dismissed.** It said a
straight-line metric "measures the pre-notch and notched boards identically at
4.031 mm". That is correct **and not a defect**: a straight line measures
clearance, and the clearance really is the same on both boards. The notch changes
the creepage, which is what the rule requires.

## Decision 2 — every isolation figure states its method beside it

Binding for this board. Before this ADR the release had shipped three numbers
with the metric implicit — the ISO pair (bbox vs true-polygon vs all-copper), the
I-HW table, and the H4 geodesic — and the third one cost a false FAIL ruling and
three re-races.

**CHECK WHICH QUANTITY THE REQUIREMENT NAMES BEFORE MEASURING.** Creepage and
clearance are different properties and a notch affects exactly one of them.

Corollary for gates: `keypad_isolation_6mm` returning 0 violations is **not
evidence about creepage**. `I-HW`, which models the fastener and walks the board
surface, is what measures it. A gate whose measurement is not the property is the
same failure family as `A-EVID` and the `row_kind` blind spot.

## Decision 3 — K_STOP may not be moved to "fix" H4

Established by three re-races before the ruling was reversed. Kept because it is
permanently true of this board and was not previously written down anywhere.

- **`K_STOP.1`'s NORTH PAD EDGE IS A CREEPAGE CONSTANT.** Pad centre y30.380,
  radius 0.750 → north edge **y29.630**, which is already `route.yaml`'s
  *"gap pads 29.63"*. Against the keypad band cap at y23.200 it sets the
  **PRIMARY** keypad↔SELV creepage: **29.630 − 23.200 = 6.430 mm by
  construction.** Moving K_STOP north eats it 1:1, so **north travel is capped at
  0.430 mm by the barrier the move would be protecting.**
- **East travel is capped at 1.500 mm** by the board edge.
- Far enough north also puts `K_STOP.1` inside `route.yaml`'s full north band
  (User.2, `y[9.9, 29.4]`) where logic copper is forbidden, so `5V_STOP` cannot
  reach it at all — reproduced twice, not stochastic.

**K_STOP is load-bearing geometry, not a free part.**

## Decision 4 — a corridor is a routing resource, not margin

The **1.800 mm** between K_STOP's east pads and the board edge is not slack:
`RSTOP_MID` and `KP_U6` **climb it** to reach the keypad domain. Taking 1.000 mm
of it leaves 0.100 mm after the 0.700 mm `edge_band`; the router then routes
around the west side and past the SELV coil pads, measured as
2 × `keypad_isolation_6mm` (5.2700 mm, 5.4246 mm vs 6.000 mm) and 3 unconnected.

Generalise before reading any inter-part gap as available space: **ask what
currently travels through it.**

## Consequences

- H4 **passes** at 6.5984 mm creepage. v1.3 is orderable and no copper changed.
- The H4 notch stays. It is load-bearing after all — it is what makes the
  creepage path 6.5984 mm instead of the pre-notch 4.031 mm.
- Any future attempt to reclaim space around K_STOP or its east corridor must
  re-derive Decisions 3 and 4 first.
