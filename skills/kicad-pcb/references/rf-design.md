# RF / radio board design

Canon for boards whose deliverable is a **radio property** — impedance, phase,
isolation — rather than connectivity plus DRC. Two boards in this fleet are of
that kind and both found the pipeline had no gate for the thing they sell.

## READ THE TWO VOICES SEPARATELY

Every item below is tagged **[SOURCED]** with a URL, or **[MEASURED]** with the
number and the board it came from. **Never blend them.** The defect this rule
exists for is local: `pluto-cal-switch` ADR-0010 solved its constants once at
eps_r 4.3, published "0.35 mm = 50 ohm", and later ADRs re-cited that headline as
though it had been measured — while the board's own generated `nets.yaml` said
`0.35 -> 51.0 ohm` the whole time.

---

## 1. Ossmann's five rules [SOURCED]

Michael Ossmann (HackRF, Ubertooth, Great Scott Gadgets), *Simple RF Circuit
Design*, Hackaday Superconference 2015. Corroborated across
[Hackaday](https://hackaday.com/2016/03/23/michael-ossmann-makes-you-an-rf-design-hero/),
[rtl-sdr.com](https://www.rtl-sdr.com/micheal-ossmanns-talk-on-rf-circuit-design/)
and [OSH Park](https://hackaday.io/page/3545-michael-ossmanns-rf-design-rules).

1. **Use four layers.** *"Four-layer PCB prices have gone way down, and having
   unbroken power planes on the inside of your board makes your design
   simpler."* Keep *"RF traces all on top and power planes in the middle."*
2. **Use the most integrated components you can find.** *"Pick an integrated
   transceiver IC that's got everything in silicon."* Do not roll your own RLC
   filters; he favours SAW filters.
3. **Design for 50 ohms everywhere.** *"Most manufacturers' parts are built for
   50 ohm inputs and outputs."* The unbroken plane *"makes the same trace width
   work everywhere."*
4. **Follow manufacturer recommendations.** *"Unless they don't want your
   business, the manufacturer will provide you with a reference circuit"* —
   layout specifications often *"down to the part numbers."* In his own words:
   *"the RF section was the easiest to lay out — I just copied it from the data
   sheets!"*
5. **Route RF first**, keep traces *"short, relative to the frequency of
   interest"*, then keep digital away from the RF.

**The rules are deliberately number-light and that IS the contribution.** They
are optimised for getting a working radio without a VNA or a field solver. Do not
mistake the absence of numbers for incompleteness — section 2 is where numbers
live and section 3 is where they conflict.

**The one rule this repo is NOT clean on is rule 4.** Vendor lands have been
deviated from more than once (a KiCad USB-C footprint 0.375 mm off the vendor
land datum; an `SOT-223` row centre displaced 6.10 -> 6.30). Rule 4 is cheap
insurance and neither deviation was deliberate.

## 2. Numbers the external sources give [SOURCED]

| quantity | value | source |
|---|---|---|
| 50 ohm microstrip, OSH Park 4-layer | **12 mil** trace | OSH Park, above |
| via fence pitch | **< lambda/20 at the FREE-SPACE wavelength** (10 GHz: lambda 30 mm -> < 1.5 mm) | [rfessentials](https://rfessentials.com/industry-news/rf-design/rf-pcb-layout-grounding/) |
| via fence distance from trace edge | **>= 3x substrate height** (closer perturbs Z0) | rfessentials |
| ground via at a component pad | **within 10 mil of the pad edge**; via L ~0.5-1 nH; 1 nH = 63 ohm at 10 GHz | rfessentials |
| RF trace to board edge | **>= 5x substrate height** (the edge loses the ground reference) | rfessentials |
| coplanar ground clearance | the **3W rule is overly conservative**; clearance:width **0.5-2.0** is workable on Dk 4.1 | [Altium](https://resources.altium.com/p/microstrip-ground-clearance-how-close-too-close) |

## 3. WHERE THE SOURCES DISAGREE WITH THIS REPO

The most valuable section. Each item is actionable.

**(a) Board-edge clearance — WE ARE LOOSER THAN THE SOURCE.** rfessentials wants
RF traces **>= 5x substrate height** from the edge. On `JLC04161H-7628`
(h = 0.2104 mm) that is **1.05 mm**. `pluto-rx2-8way`'s `route.yaml` declares
`edge_band: 0.7` = **3.3x h**. **RESOLVED 2026-07-30 by measurement: it does not
bind.** The closest RF pad to a board edge is **4.731 mm = 22.5x substrate
height**, and the arms run INWARD from there, so the 5x rule is satisfied by
geometry with 4.5x of margin. `edge_band` is a router keepout, not the RF
clearance — the number stands and the derivation is now recorded. Worth keeping
as an example: the sourced rule was real, the concern was reasonable, and the
board was already compliant by construction. Measure before changing a number.

**(b) Via-fence pitch — THREE METHODS IN ONE FLEET, only one of them derived.**
The source uses **free-space lambda/20**: at 6 GHz that is 50/20 = **2.5 mm**.
`pluto-rx2-8way` uses **guided lambda_g/20 = 1.37 mm** computed from its own
eps_eff 3.328 — stricter than the source and correctly derived.
`pluto-cal-switch` states **lambda_g/12 = 2.0 mm**, but the arithmetic is
24.10/12, i.e. the **BULK** eps_r 4.3 wavelength, which is neither free-space nor
guided; on its own guided lambda_g it is really lambda_g/13.9. All three are
conservative against the source so nothing is unsafe — but a rule whose
parenthetical does not derive the number attached to it gets re-cited as if it
did. **Pick guided lambda_g and say so.**

**(c) Coplanar ground clearance — our blocker may have been DRC, not physics.**
`pluto-rx2-8way` could not route 6 of 11 RF nets because PE42482A-X's land leaves
**0.350 mm** to a GND pad edge while a 0.36 mm trace at the 0.200 mm DRC
clearance needs 0.380 mm — a **clearance-rule** deficit of 0.030 mm. On Altium's
data the clearance:width ratio there is **0.97**, comfortably inside the 0.5-2.0
band they measure as workable, so the RF objection to tightening is weaker than
the DRC objection — and **this repo cannot currently tell the two apart, because
it has no field solver.** The refusal to relax to <= 0.17 mm was argued on
g/h ~ 0.8 detuning the microstrip; that concern is real and is exactly what a
field solve would settle. **Owed: a field-solver step, or an explicit "we do not
model coplanar loading, so we hold 3W-ish" statement.**

**(d) Rule 1 — we AGREE, and it is load-bearing.** `pluto-rx2-8way` excludes
In1.Cu from its routing layers entirely so nine radial arms share one unbroken
reference — *"what makes their phases comparable at all"*. That is Ossmann's rule
1 arrived at independently, and it belongs here as the rule rather than as a
board-specific choice.

## 4. What this fleet measured that the sources do NOT cover [MEASURED]

Gaps a general RF guide will not fill. All measured 2026-07-29.

**(a) AN OCTILINEAR ROUTER MAKES "EQUAL LENGTH BY CONSTRUCTION" FALSE OF
COPPER.** A radial star has equal *pad* radii; the router does not have equal
*moves*. KRT routes on 45-degree multiples, so only 3 of 9 radials lie on one and
the rest pay ~7% of their radius. `pluto-rx2-8way`: Euclidean pad spread
**0.3238 mm**, octilinear FLOOR spread **1.4966 mm = 19.74 deg at 6 GHz**,
against a declared 1.0 mm ceiling. The bound is exact and needs no copper, no
stackup and no router:

    oct(dx, dy) = max(dx, dy) + 0.4142 * min(dx, dy)

Check it from PADS ALONE at authoring time (canon M-ENTRY). Three hours of
routing found this; the pads find it in milliseconds. It is NOT a lower bound on
the ACHIEVABLE spread — a router can lengthen a short member, which is what
meandering is for — so an `elongation:` opt-out must be cross-checked against a
real `length_match_group` in the route recipe.

**(b) THE GOVERNING TOLERANCE IS DRIFT, NOT STATIC MISMATCH.** A calibrated
system absorbs a static delta; it cannot absorb one that moves. Size
`max_spread_mm` from `d_tau = TC * dT * dL * t_pd` (1 mm is 0.05 deg over 40 C),
not from a desired match. **A tolerance tighter than the part's own spec is not
physics:** PE42482A-X publishes a **13.2 deg** part-to-part relative-phase window
= 1.00 mm of copper, and mounting inductance adds ~2 deg per solder fillet. A
standing "+/-0.10 mm" obligation was **1.3 deg** and was withdrawn as unreachable
by any router and unheld by any process.

**THE KNOB IS `meander_amplitude`, NOT `length_match_tolerance`.** Measured by a
15-run sweep on `pluto-rx2-8way`: tolerance {0.15, 0.10, 0.05} moved the realized
spread by **exactly zero** at all five amplitudes, while amplitude moved it
1.0 -> 1.5586, 0.8 -> 1.1586, 0.5 -> 0.6549, 0.3 -> 0.3236, 0.2 -> 0.3236 mm. An
earlier record credited the tolerance with the 1.1586 result; that is the
amplitude-0.8 row. And 0.3236 mm is not a router minimum — it is the **0.3238 mm
Euclidean pad residue**, so the elongation recovered the ENTIRE 1.4966 mm
octilinear penalty. The floor is a floor on the ROUTER'S MOVE SET, never a bound
on the achievable spread.

**(c) A VENDOR LAND CAN MAKE THE REQUIRED WIDTH UNROUTABLE — AND ON THE BOARD
THAT MOTIVATED THIS ITEM, THE REAL CAUSE WAS THE ROUTER GRID. Corrected
2026-07-30 by measurement; the original claim is kept because being wrong about
the MECHANISM while right about the SYMPTOM is the trap.**

The symptom stands: compute, per pad, the widest track that can leave without
violating clearance to its neighbours, and grade it against the netclass floor.
`pluto-cal-switch` has **eleven** pads that cannot accept their own class minimum
and nothing asked.

But on `pluto-rx2-8way` the arms did not fail for want of width. At KRT's default
`grid_step: 0.1`, **NOTHING routes the five boxed RF pads at ANY width** — 0.30,
0.25 and 0.20 all fail — because the RF land centres sit at odd multiples of
0.05 mm (y = 45.25, 46.25, ...) and a 0.1 mm grid cannot place a centreline on
them. With `grid_step: 0.05` and `clearance: 0.14` (the least relaxation that
routes: 0.145 works, 0.15 does not) the wave routes **11/11 at the full 0.36 mm
impedance width**. The earlier "11/11 at 0.25 mm" was not reproducible from the
recorded recipe.

**AND NECK-DOWN IS REFUTED AS THE REMEDY, not merely unconfigured.** Measured:
`--power-nets 'ANT*' --power-nets-widths 0.36 --neckdown-length 0.3` routes 11/11
and delivers **149.832 mm of RF copper at 0.25 mm and 0.000 mm at 0.36**. KRT's
re-widen pass only restores width where the NARROW-PLANNED path has wide
clearance — which, on a radial star leaving a QFN, it never does. This document
said otherwise for one day.

**So the ranked remedy is: grid first, then a launch-local scoped clearance,
then width.** A launch that will not route is three different questions and the
grid one is free.

**(d) ONE STACKUP MUST HAVE ONE CONSTANT SET.** Two boards on `JLC04161H-7628`
carried different eps_eff / t_pd / lambda_g because one solved at eps_r 4.3 and
the other at the declared Dk 4.4. Phase runs at **13.19 deg/mm** at 6 GHz
(eps_eff 3.350, t_pd 6.105 ps/mm, lambda_g 27.29 mm), so a 1.3% constant error is
a real published error on a board whose artifact is a picosecond figure.

**(e) MEASURE THE PRIZE, DO NOT INHERIT IT.** An SMA bottom-plane antipad was
claimed at ~9 dB and re-derived at **5.6 dB** of return loss at 6 GHz (RL 8.9 ->
14.5). Both numbers were "known"; only one was measured.

## 5. Protocol — what an RF board does differently, by stage

Mapped onto `skills/pcb-design/SKILL.md`.

- **Stage 2/3 (parts, source).** Choose the most integrated part (rule 2). Copy
  the vendor reference layout (rule 4) and RECORD the comparison — deviating
  here is how both fleet land defects happened. Declare the stackup ONCE and
  derive eps_eff / t_pd / lambda_g from it; every ADR cites the derived
  constants, never a re-typed copy (4d; canon M-BOUND).
- **Stage 4 (schematic).** Declare `length_match:` groups now, with
  `max_spread_mm` derived from DRIFT (4b) and the phase constants attached. A
  matched set that does not exist as a schema cannot be graded.
- **Stage 5 (placement).** Four layers, RF on top, unbroken reference beneath
  (rule 1, 3d) — exclude the reference layer from the routing layers so it
  cannot be cut. Check the **octilinear floor from pads alone** (4a) and the
  **landable width per pad** (4c) BEFORE routing: both refuse an impossible
  board in milliseconds. Via fence from GUIDED lambda_g (3b); edge clearance
  from a derived number (3a).
- **Stage 6 (route).** RF first (rule 5), on one layer, no vias inside a
  phase-critical arm. Where two paths must match, prefer a DETERMINISTIC
  transform over a stochastic route — but **verify WHICH transform**: on
  `pluto-cal-switch` a +14.5 mm translation and a reflection about y = 55.000
  coincide for every part A-SYM grades and diverge at the splitter, so the
  transform is per-net and the gate cannot tell them apart.
- **Stage 7 (fab).** The published RF artifact (a delta, a spread) is MEASURED
  from routed copper, never asserted from placement.

## 6. Gate proposals, ranked — and what was rejected

This repo carries **73 check-IDs across 32 gates**. Every gate is maintenance and
every one can itself go vacuous, so this list is short on purpose.

1. **Min landable width per pad vs the netclass floor** (extend
   `escape_check.py`). Two boards asked independently — canon M8's two-strike is
   met. Highest leverage: refuses at authoring time a board that otherwise fails
   after a full race, and needs only footprint + netclass.
2. **One stackup, one constant set** (extend `adr_bound_provenance.py` /
   M-BOUND). Cross-check every published eps_eff / t_pd / lambda_g against the
   value derived from the declared stackup. Catches 4d and 3b from source alone.
   `length_match.<G>.phase.*` is already declared OWED in the `03_src/rules`
   contract for this reason — the resolution is a CROSS-CHECK, never having the
   gate READ the declared number.
3. **Reference-plane continuity under a matched group** — assert the layer
   beneath a `length_match:` group carries no routed net. Rule 1 made executable,
   and it is the failure that silently destroys phase.

**Rejected, with reasons.** *A field solver* — the right answer to 3c but a large
dependency; the honest interim is to state that we do not model coplanar loading.
*A via-fence pitch gate* — all three fleet values are already conservative
against the source, and the defect was the DERIVATION, which proposal 2 catches.
*An edge-clearance gate* — one deviation on one board; fix the number, do not
build a gate for it. *A "route RF first" gate* — wave order is already declared in
`route.yaml` and reviewed; a gate would grade a comment.

---

**Sources.**
[Hackaday — Ossmann makes you an RF design hero](https://hackaday.com/2016/03/23/michael-ossmann-makes-you-an-rf-design-hero/) ·
[rtl-sdr.com — Ossmann's talk on RF circuit design](https://www.rtl-sdr.com/micheal-ossmanns-talk-on-rf-circuit-design/) ·
[OSH Park / Hackaday.io — Ossmann's RF design rules](https://hackaday.io/page/3545-michael-ossmanns-rf-design-rules) ·
[Great Scott Gadgets presentations](https://greatscottgadgets.com/presentations/) ·
[rfessentials — RF PCB layout: grounding, via fencing, trace geometry](https://rfessentials.com/industry-news/rf-design/rf-pcb-layout-grounding/) ·
[Altium — microstrip ground clearance](https://resources.altium.com/p/microstrip-ground-clearance-how-close-too-close)

**NOT VERIFIED, stated so it is not mistaken for sourced.** The full numeric
content of Ossmann's talk is in the video and was not retrievable as text: the
five rules are corroborated across three written sources, but every *number*
attributed to him here comes from OSH Park's stackup note rather than his own
words. The Analog Devices mixed-signal layout note timed out and was not read.
The `d.lij.uno` seminar notes returned HTTP 522.
