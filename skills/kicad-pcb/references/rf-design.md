# RF / radio board design

Canon for boards whose deliverable is a **radio property** — impedance, phase,
isolation — rather than connectivity plus DRC. Two boards in this fleet are of
that kind and both found the pipeline had no gate for the thing they sell.

## READ THE THREE VOICES SEPARATELY

Every item below is tagged **[SOURCED]** with a URL, **[MEASURED]** with the
number and the board it came from, or **[DERIVED]** with the closed form, its
inputs, and the stackup field each input came from. **Never blend them.** The
defect this rule exists for is local: `pluto-cal-switch` ADR-0010 solved its
constants once at eps_r 4.3, published "0.35 mm = 50 ohm", and later ADRs
re-cited that headline as though it had been measured — while the board's own
generated `nets.yaml` said `0.35 -> 51.0 ohm` the whole time.

**THE THIRD VOICE WAS ADDED 2026-07-30, AND ITS ABSENCE IS WHY THIS FILE
PUBLISHED A WRONG CONSTANT.** With only two tags a COMPUTED number has nowhere
to live, so `eps_eff 3.350` was filed in section 4 — a section whose heading
reads *"What this fleet MEASURED"* — while being a closed-form evaluation
nobody had ever re-run. Not one sentence in the file was false. The number was
wearing the wrong voice, and **a reader who wants provenance stops asking once
a thing is labelled measured.** A derivation is not a measurement and it is not
a citation: it is a third thing, and it is the only one of the three a reader
can check without leaving the desk. Section 4A is what checking it found.

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

**THE ANSWER, STATED PLAINLY, BECAUSE "all three are conservative" LEFT IT
AMBIGUOUS AND A BOARD THEN SHIPPED AGAINST THE WRONG ONE.** [DERIVED] A via
fence sits in the substrate beside a microstrip. What it must sample is the
wave ON THE LINE, not a wave in air, so the governing wavelength is the
**GUIDED** one:

    lambda_g = lambda_0 / sqrt(eps_eff)        eps_eff > 1, so lambda_g < lambda_0

Free-space `lambda_0/20` is therefore the LOOSER bound, and satisfying it says
nothing about the guided one — on `JLC04161H-7628` at 6 GHz the two differ by
`sqrt(3.32) = 1.82x` (2.5 mm vs 1.37 mm). The BULK `eps_r` wavelength is a
third thing and is not a bound at all: it uses the permittivity of the
laminate rather than the mix of laminate and air the field actually sees, so
it OVERSTATES eps and understates lambda_g, which happens to be conservative
here and is still not a derivation.

**MEASURED, `pluto-rx2-8way-v2`, 2026-07-30 — the case that made this
ambiguity cost something.** Its ARCHITECTURE sec 6 requires a fence at
`<= 1.35 mm` (the largest round value under its own derived
`lambda_g/20 = 1.3693 mm`, ADR-0003), and it ships at **2.0 mm =
lambda_g/13.7**. That is inside the free-space rule and OUTSIDE its own guided
one: **the bound is NOT MET.** The cause was not judgement — the shared
stitcher stepped its grid with `range(int(...))`, so the only expressible
pitches were 1 mm and 2 mm and `1.35` was unsayable. Fixed 2026-07-30
(`route_and_stitch_generic.py p_stitch_grid` / `_grid_axis`, pinned by
`tests/t2_route_stitch.py t_grid_fractional_pitch`); **the board is not
re-fenced by that fix and remains at 2.0 mm until it is regenerated with a
fractional pitch declared.** Reported, not silently closed.

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

Gaps a general RF guide will not fill. All measured 2026-07-29, except (d),
which turned out not to be a measurement at all — see 4A.

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
the other at the declared Dk 4.4. Phase runs at **~13.2 deg/mm** at 6 GHz, so a
1% constant error is a real published error on a board whose artifact is a
picosecond figure.

**THE CONSTANTS THIS ITEM ITSELF PUBLISHED — eps_eff 3.350, t_pd 6.105 ps/mm,
lambda_g 27.29 mm, 13.19 deg/mm — ARE WITHDRAWN, 2026-07-30.** They came from a
closed form that does not exist. And the rule as worded above was too weak to
catch even its own violation: it says a stackup has one constant set and says
nothing about WHICH cross-section or WHICH form, so by the day this was checked
the fleet was publishing **five** sets for this one laminate, two of them inside
one file. **Section 4A is what this item should have said**, and it is a
section rather than a rewrite because five live board documents cite this file
by section number.

**(e) MEASURE THE PRIZE, DO NOT INHERIT IT.** An SMA bottom-plane antipad was
claimed at ~9 dB and re-derived at **5.6 dB** of return loss at 6 GHz (RL 8.9 ->
14.5). Both numbers were "known"; only one was measured.

## 4A. WHERE THIS REPO DISAGREES WITH ITSELF — one stackup, FIVE constant sets

Section 3 is the EXTERNAL axis: the published sources against us. This is the
internal one, and it is the more dangerous of the two, because an external
disagreement announces itself and an internal one gets re-cited as
corroboration. Numbered `4A` rather than renumbered into place on purpose: five
live board documents cite this file as `4(d)`, `3(b)`, `3(d)`, `section 1` and
`section 5`, and **silently renumbering canon that boards cite is the exact
drift this section is about.**

### What the fleet published for `JLC04161H-7628`, w = 0.36 mm, 6 GHz

All rows re-checked 2026-07-30 by reading each file and re-running its stated
arithmetic. `lambda_g/20` is shown because it is the via-fence pitch every
board in this family inherits.

| where | eps_eff | t_pd ps/mm | lambda_g mm | deg/mm | lg/20 | the method ACTUALLY used |
|---|---|---|---|---|---|---|
| 4(d) above (withdrawn) + `pluto-rx2-8way` `nets.yaml` phase block | 3.350 | 6.105 | 27.29 | 13.19 | 1.365 | a HYBRID closed form — (i) |
| `pluto-rx2-8way` `nets.yaml` netclass comment, SAME FILE | *(3.3229)* | — | **27.41** | — | 1.371 | 3.328 divided into a lambda_0 ROUNDED to 50 mm — (iv) |
| `pluto-rx2-8way` ADR-0003 / DETAIL_DESIGN | 3.328 | 6.09 | *(27.39)* | — | 1.369 | H-J eps_eff at a single Wheeler `w_eff` — (ii) |
| `pluto-rx2-8way-v2` ADR-0003 | 3.3286 | 6.0857 | 27.387 | 13.145 | 1.369 | same method, more digits |
| `pluto-cal-switch` (re-derived the same day) | **3.383** | 6.135 | 27.17 | 13.25 | 1.359 | **2D field solve, AS FABBED** — (iii) |
| **this section, derived independently** | **3.3226** | **6.0802** | **27.411** | **13.133** | **1.371** | H-J + H-J's OWN thickness correction, BARE |

**(i) 3.350 HAS a provenance, and finding it IS the answer: it is a closed form
that does not exist.** [DERIVED] It is recorded verbatim in
`copper_length_audit.py`'s own docstring, so nothing was hidden —

    eps_eff = (er+1)/2 + (er-1)/2 / sqrt(1 + 10h/w)
            = 2.70 + 1.70/sqrt(1 + 5.844) = 2.70 + 0.650 = 3.350

The arithmetic is correct and the formula is not. The constant **10** is
Hammerstad-Jensen's, whose exponent is **-a(u)*b(er)**; the exponent **-1/2**
is Schneider/Wheeler's, whose constant is **12**. The expression takes one term
from each parent. Evaluate both parents on the same inputs (h 0.2104 mm,
er 4.4, w 0.36 mm, t 0, so u = w/h = 1.7110):

    Hammerstad-Jensen  (1 + 10/u)^-a(u)b(er),  a*b = 0.54170   ->  3.2999
    Schneider/Wheeler  (1 + 12/u)^-0.5                         ->  3.3005
    the hybrid                                                 ->  3.3498

**The two parents agree with each other to 0.02%.** So 3.350 is not a value
sitting between two models that disagree — it is 1.5% above two models that
AGREE, and it matches neither. No measurement is cited for it anywhere in the
tree and none exists; under canon M6 it outranks nothing. **Withdrawn.** The
lesson is not "check the arithmetic" — the arithmetic was checkable and
correct. It is that **a formula is an input too, and only the inputs were
tagged.**

**(ii) The SECOND fork is the thickness treatment, and it is why two honest
agents land on 3.3226 and 3.3286.** [DERIVED] Here t/h = 0.035/0.2104 = 0.166,
so copper thickness is not a rounding term. Hammerstad-Jensen carries its own
correction and it produces TWO corrected widths, not one:

    du1 = (t/h)/pi * ln(1 + 4e / ((t/h) * coth^2(sqrt(6.517*u))))  ->  u1 = 1.9329
    dur = 0.5 * (1 + 1/cosh(sqrt(er - 1))) * du1                   ->  ur = 1.8562

`u1` feeds Z0, `ur` feeds eps_eff, and `ur < u1` because only PART of the extra
fringing a thick strip captures sits in the dielectric — that
`0.5*(1 + 1/cosh(sqrt(er-1)))` = 0.656 factor is the dielectric's share.
Feeding one Wheeler `w_eff = w + (t/pi)(1 + ln(2h/t)) = 0.3988 mm` (u = 1.8957)
into the eps_eff formula instead spends the WHOLE increment on the dielectric
term and lands 0.18% high. Both are defensible engineering; only one is
internally consistent with the formula it feeds. H-J's own gives **eps_eff
3.3226 and Z0 49.79 ohm at the 0.36 mm these boards actually route** — landing
on 50 ohm at an independently chosen width is the corroboration that matters.

**(iii) AND THE ENTIRE ARGUMENT IS SMALLER THAN THE TERM NO CLOSED FORM
CARRIES.** [MEASURED] `pluto-cal-switch`, 2026-07-30, 2D finite-difference
field solve on this exact cross-section, one term at a time at w 0.35 mm:

    bare rectangular trace                       Z0 51.64 ohm
    + trapezoidal etch (top -0.02 mm)            Z0 52.11 ohm   (+0.46)
    + conformal solder mask 0.020 mm, Dk 3.8     Z0 50.09 ohm   (-1.55)

Convert the mask row to permittivity — and it converts EXACTLY, because
`Z0 = Z0_air / sqrt(eps_eff)` and `Z0_air` is a function of GEOMETRY ONLY, which
that row holds fixed:

    eps_eff_masked / eps_eff_bare = (51.64 / 50.09)^2 = 1.063     ->  +6.3%

**Every closed form in the table above is a BARE-TRACE model, and no board in
this fleet fabricates a bare trace.** On a mask-covered 0.36 mm run the bare
3.3226 implies roughly **3.53** before the trapezoid gives a little back. So
the correction this section makes is REAL but it is not the biggest one
available, and **the derivable number is not automatically the true number** —
3.350 was wrong for a bad reason and wrong in the RIGHT DIRECTION, while every
bare closed form is right about a cross-section nobody builds. Two consequences,
both stated rather than resolved:

- **A constant set is meaningless without its CROSS-SECTION.** "Mask-opened
  over the RF run" or not is a stackup field, and the fleet does not declare
  it. It is worth more than the 1.5% everyone has been arguing about.
- **OWED, and reported rather than fixed** (this is a project record, not
  canon): `pluto-cal-switch`'s own per-term Z0 table implies a masked eps_eff
  near 3.52 at w 0.35, while the composite it publishes is 3.383 at w 0.36.
  Those do not reconcile from the record as written, because the record gives
  Z0 per term and eps_eff only for the composite. The field solve is also the
  only method in the table with **no re-runnable command** — best method,
  weakest regenerability, which is its own M-BOUND finding.

**(iv) THE FENCE PITCH WAS RIGHT BY LUCK, TWICE, FROM TWO UNRELATED ERRORS.**
[DERIVED] `lambda_g = 27.41 mm` — the figure the family's `lambda_g/20 =
1.37 mm` via fence was actually computed from — is `50 / 1.8242`, i.e.
`lambda_0` rounded from **49.9654 mm** to 50 mm at 6 GHz. From the same
eps_eff 3.328 the honest quotient is 27.389. And this section's independent
derivation, by a different route entirely, gives **27.411 mm**. The three-digit
agreement is a COLLISION, not a corroboration, and it is the specimen worth
keeping: a number can survive two independent errors and still be quoted as
confirmed. The fence stands at 1.37 mm; every rung of its derivation was wrong.

**(v) NOTHING SHIPPED IS UNSAFE, AND THAT IS NOT THE POINT.** [DERIVED] The
laminate's own Dk window is 4.2-4.6, which moves eps_eff **3.187 -> 3.458** and
the pitch **1.399 -> 1.344 mm**. Every disagreement above lives INSIDE that
window; the fence is conservative at all of them. Dispersion (Kirschning-Jansen
at 6 GHz) adds +0.30%, and does not reach 3.350 either. **What is at stake is
regenerability, not accuracy** — canon M-BOUND. A constant nobody can re-derive
survives every review, because reviewing it requires re-deriving it, which is
the work everyone assumes was already done.

### THE RULE

> **ONE STACKUP, ONE CONSTANT SET — AND THE SET IS IDENTIFIED BY THE TUPLE
> `(stackup, w, cross-section, method)`, NEVER BY THE STACKUP ALONE.** A board
> publishes eps_eff / t_pd / lambda_g ONCE, with the formula, every input, and
> the stackup field each input was read from, so the number is a COMMAND and
> not a digit. Two documents may hold different constants for one laminate only
> when the tuple differs and both tuples are printed. A re-typed copy is not a
> citation; a formula assembled from two sources is not a formula; and a number
> whose method is not named cannot be compared to another number at all.

Because the failure is now WITHIN one file rather than between two boards, this
is canon M8's second strike and the rule is a gate candidate.

**PROPOSED CHECK ID: `M-BOUND-EPS`** (extends `adr_bound_provenance.py` /
M-BOUND). Collect every published eps_eff / t_pd / lambda_g / deg-per-mm in a
project, re-derive from the declared stackup + netclass width, and FAIL on
disagreement beyond a stated tolerance; FAIL a set that names no method or no
cross-section; FAIL two sets for one tuple. It catches 4(d), 3(b) and every row
of the table above from source alone. **NOT IMPLEMENTED HERE, DELIBERATELY** —
`smc0985-cooksense` is mid-seal, and a board mid-seal pins its gates: changing
a checker underneath it moves the numbers its seal is being graded on. The gate
lands after that seal, and this proposal is the handoff.

## 5. Protocol — what an RF board does differently, by stage

Mapped onto `skills/pcb-design/SKILL.md`.

The executable applicability/requirements home is `03_src/rules/rf.yaml`,
graded by `scripts/rf_contract_check.py`. New boards keep the file even when RF
is disabled, with a rationale. When enabled, it names the exact artifact and
requirement IDs for three independent phases; zero requirements is a failure:

- RF schematic: `references/rf-schematic-review-protocol.md`;
- RF PCB: `references/rf-pcb-review-protocol.md`;
- plotted fab output: `references/rf-fab-review-protocol.md`.

Risk tier follows electrical length and the claimed performance (impedance,
phase, loss, isolation), not a frequency label alone. A slow clock edge can be
an RF problem and a high carrier inside a fully integrated shielded module may
not create a board-level controlled-impedance path.

- **Stage 2/3 (parts, source).** Choose the most integrated part (rule 2). Copy
  the vendor reference layout (rule 4) and RECORD the comparison — deviating
  here is how both fleet land defects happened. Declare the stackup ONCE and
  derive eps_eff / t_pd / lambda_g from it, **printing the formula, the inputs
  and the CROSS-SECTION (mask-opened or not) alongside the number**; every ADR
  cites the derived constants, never a re-typed copy (4d, 4A; canon M-BOUND).
  If a closed form is the method, name WHICH — the fleet has shipped a formula
  assembled from two of them (4A(i)).
- **Stage 4 (schematic).** Declare `length_match:` groups now, with
  `max_spread_mm` derived from DRIFT (4b) and the phase constants attached. A
  matched set that does not exist as a schema cannot be graded. Then run the
  independent RF schematic review; a missing/partial requirement set or
  `design_verdict: DEFECTIVE` returns to schematic work before placement.
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
  transform is per-net and the gate cannot tell them apart. Run the independent
  RF PCB review on the exact board hash before layout seal.
- **Stage 7 (fab).** The published RF artifact (a delta, a spread) is MEASURED
  from routed copper, never asserted from placement. Review the exact plotted
  Gerber/drill zip in an independent viewer and bind that hash to
  `fab_package_verdict: READY`; JLC is not expected to design-review it.
- **First article.** A fab-ready package authorizes a prototype, not production.
  VNA/TDR the declared calibration plane and compare every measurement with the
  numeric `first_article.acceptance` list. Production remains HOLD until those
  measurements pass or a documented redesign/review loop closes the miss.

## 6. Gate proposals, ranked — and what was rejected

This repo carries **73 check-IDs across 32 gates**. Every gate is maintenance and
every one can itself go vacuous, so this list is short on purpose.

1. **Min landable width per pad vs the netclass floor** (extend
   `escape_check.py`). Two boards asked independently — canon M8's two-strike is
   met. Highest leverage: refuses at authoring time a board that otherwise fails
   after a full race, and needs only footprint + netclass.
2. **One stackup, one constant set — `M-BOUND-EPS`** (extend
   `adr_bound_provenance.py` / M-BOUND). Cross-check every published eps_eff /
   t_pd / lambda_g against the value derived from the declared stackup, and
   REFUSE a set that names no method or no cross-section. Catches 4d, 3b and
   every row of 4A's table from source alone. `length_match.<G>.phase.*` is
   already declared OWED in the `03_src/rules` contract for this reason — the
   resolution is a CROSS-CHECK, never having the gate READ the declared number.
   **Promoted to first-ranked-by-evidence 2026-07-30**: the defect recurred
   INSIDE a single file (canon M8's second strike) and the fleet was measured
   carrying FIVE sets for one laminate. **Deliberately not built yet** — a
   board is mid-seal and a board mid-seal pins its gates.
3. **Reference-plane continuity under a matched group** — assert the layer
   beneath a `length_match:` group carries no routed net. Rule 1 made executable,
   and it is the failure that silently destroys phase.

**Rejected, with reasons.** *A field solver* — the right answer to 3c but a large
dependency; the honest interim is to state that we do not model coplanar loading.
*A via-fence pitch gate* — all three fleet values are already conservative
against the SOURCE, and the defect was the DERIVATION, which proposal 2 catches.
**Amended 2026-07-30 and left rejected, with the amendment stated:** the
rejection rested on "already conservative", which is true only against the
free-space rule. Measured against the GUIDED bound each board sets for itself,
`pluto-rx2-8way-v2` is OUTSIDE its own (`2.0 mm` shipped vs `<= 1.35 mm`
required, 3(b)) — so the premise was half wrong. It stays rejected because the
cause was not a missing gate but an UNEXPRESSIBLE NUMBER: the stitcher floored
its grid pitch to a whole millimetre, so no board could have declared 1.35 and
a gate would only have reported an impossibility. Fixing the stepper is the
repair; revisit this proposal only if a board misses its guided bound with a
fractional pitch available to it.
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
