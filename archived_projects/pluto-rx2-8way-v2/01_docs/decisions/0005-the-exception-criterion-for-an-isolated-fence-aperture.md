---
id: 0005
date: 2026-07-31
status: accepted
tags: [rf, fence, criterion, blind]
---
# 0005 — the exception criterion for a SINGLE isolated fence aperture, formed BLIND and deliberately NOT SPENT

## Context

ADR-0004 fixed this board's ground-stitch bound at `lambda_pp/20 = 1.1910 mm`
and left an OPEN P0: 34 apertures over it, worst 3.0500 mm. Two of the four
aperture classes (the SMA `avoid` rings, and the star hub / tap detour) were
believed to need "either a per-arm fence pass or a measured exception".

`ARCHITECTURE.md` sec 6 already carried a candidate exception argument for the
SMA-ring class — that the bound should not apply inside a launch antipad,
because the parallel-plate mode has no lower plate there. It was written down
and DELIBERATELY NOT APPLIED, with the reason stated: *it was formed AFTER
seeing which apertures failed, which is exactly the reasoning that put
`eps_eff = 3.350` into this fleet.*

That is the problem this ADR exists to solve. An exception argument written by
the person who has just seen which numbers failed is not evidence, however good
the physics inside it. The `lambda/20` divisor is a rule of thumb about a
PERIODIC wall, and whether it governs a single non-periodic defect is a real
open question with a real answer — but the answer is only worth anything if
nobody could tune it to fit.

## Options

- **Apply the ARCHITECTURE sec 6 argument.** REJECTED. Its premise may well be
  true; its provenance is not repairable after the fact.
- **Hold every aperture to `lambda_pp/20` and fail the board.** Legitimate, and
  it is what the previous session did. But it declines to answer the question,
  and the question recurs on every board in this family.
- **Derive the criterion in a FRESH CONTEXT that is given the GEOMETRY but NOT
  THE FAILURE LIST.** CHOSEN. The route the brief prescribes when the deriving
  agent has already been contaminated by the measurement — which I had been.

## Decision

**The criterion below was formed by a zero-context agent that was given the
full stackup, the constants, the arm geometry, the lattice, the adopted
`lambda_pp/20` rule, and the bare fact that isolated obstructions exist — and
was explicitly denied this repository and every measured aperture.** It was
told that concluding "the isolated aperture must meet the SAME bound" was an
acceptable and possibly correct answer, so that a relaxation was not the only
way to complete the task. Its verbatim note is reproduced below.

    A SINGLE ISOLATED aperture of along-arm length L_a in an otherwise
    compliant stitch wall is ACCEPTABLE when

        L_a <= lambda_pp / 12 = 1.985 mm        (at 6 GHz, er = 4.4)

    and unconditionally green below lambda_pp/15 = 1.588 mm, subject to five
    conditions: (C1) the opposite flank is compliant over +/-L_a; (C2) there is
    no FACING aperture across the trace within +/-L_a; (C3) the defect is a
    missing POST in an intact 2-D lattice, never a missing ROW; (C4) it lies in
    a straight uniform section at least L_a from any other unreferenced or
    discontinuous feature, with NO relaxation whatsoever inside a launch
    region; (C5) multiple defects avoid separations near 11.910 / 14.063 /
    23.820 mm, at most one per arm, at most three per board, reverting to
    lambda_pp/20 for all of them at four or more.

The reasoning is that `lambda_pp/20` encodes a 10x resonance margin PLUS
coherent accumulation over N cells PLUS a cascade requirement, and a lone
defect has only the first. Removing the other two while holding the leaked
power budget fixed at what the compliant wall already spends buys a factor of
**1.67 in length and nothing more**.

**AND IT IS NOT SPENT.** The fence was closed in copper instead: worst interior
along-arm aperture **1.1769 mm**, inside the ORIGINAL `lambda_pp/20 = 1.1910`,
0 of 22 arm-sides over, `fence_pitch.py VERDICT: PASS` exit 0. No aperture on
this board is graded against the relaxation and **no exception is claimed
anywhere in this release**. The board is held to the tighter number it meets.

<!-- bound: ISOLATED_FENCE_APERTURE_MAX -->
```yaml
id: ISOLATED_FENCE_APERTURE_MAX
claim: >-
  Maximum along-arm length of a SINGLE ISOLATED aperture in an otherwise
  compliant ground-stitch wall flanking an RF arm -- one place where no legal
  barrel fits, in a straight uniform section, with the opposite flank
  compliant, the lattice intact transversely, and no other unreferenced
  feature within the same distance. One twelfth of the parallel-plate
  wavelength at the 6 GHz band edge. This is NOT the wall rule: the periodic
  spacing stays at lambda_pp/20 (ADR-0004). The relaxation exists because
  lambda_pp/20 encodes a 10x resonance margin PLUS coherent accumulation over
  N cells PLUS a cascade requirement, and a lone defect has only the first;
  holding the leaked-power budget fixed at what the compliant wall already
  spends buys a factor of 1.67 in length and nothing more.
  THIS BOUND IS NOT SPENT ON THIS BOARD -- its measured worst aperture is
  1.1769 mm, inside the tighter ADR-0004 wall rule.
relation: "<="
value: 1.985
unit: mm
corner: nominal
command: >-
  /usr/bin/python3 -c "import math; er,f=4.4,6.0;
  print(round(299.792458/(f*math.sqrt(er))/12,4))"
governs:
  evaluate: >-
    /usr/bin/python3 -c "print(round(23.8201/{value}, 4))"
  budget: ">= 12"
  unit: divisions of lambda_pp
  # At the published 1.985 it is exactly 12.0; at the declared standard value
  # 1.95 it is 12.21, i.e. tighter than required. A BARE NUMBER on the last
  # stdout line -- ADR-0003 already paid for the lesson that a human sentence
  # with three numbers in it regenerates perfectly and grades UNVERIFIED.
standard_value:
  explicit: [1.95, 1.90, 1.85]
  series_why: >-
    An aperture length is not an E-series part value -- it is a length a human
    reads off a measurement report and compares by eye, so the admissible set
    is round 0.05 mm values. 1.95 mm is the largest of these under the bound.
```

## Consequences

- **The candidate argument in ARCHITECTURE sec 6 is retired, not adopted.** It
  is superseded by a criterion formed blind, and that criterion is stricter
  than it in the one place they overlap: C4 grants NO relaxation inside a
  launch region, which is precisely where the sec 6 argument wanted one.
- **This board does not rely on this ADR.** If a future measurement or a
  re-route re-opens an aperture, the criterion is already on the record and was
  not written to fit that aperture — which is the whole reason to have paid for
  it now rather than then.
- **The criterion is not validated by this board and cannot be.** The note says
  so itself: the predicted penalty at the accept limit is < 0.01 dB and
  < 0.22 deg, below every practical measurement floor, so a board that measures
  fine has validated nothing. Falsification needs the deliberate-defect coupon
  described in the note's section 4.3.
- **What breaks if reversed:** nothing on this board's copper. What would break
  is the provenance — the fleet would be back to an exception whose author had
  seen the failure, which is the defect ADR-0004's own derivation order was
  written to avoid.

---

# The blind derivation, VERBATIM

Reproduced unedited. Its `MEASURED` tags refer to geometry it was GIVEN, not to
anything it measured itself; it had no access to this repository.

# Acceptance criterion for a SINGLE ISOLATED aperture in a ground-stitch wall

**CBCPW, JLC04161H-7628, DC–6 GHz, 9-arm phase-matched switch array**

Written blind. I have not been told, and have not looked at, what any board measured.
The criterion below is derived from the stated geometry, from physics, and from cited
literature only. Every number is tagged **MEASURED** (given to me as a measurement of
the board's geometry), **DERIVED** (arithmetic from those, shown), **CITED**, or
**JUDGEMENT**.

---

## 0. Constants and first derived quantities

| Quantity | Value | Tag |
|---|---|---|
| Prepreg thickness F.Cu→In1, `h` | 0.2104 mm | MEASURED (stackup) |
| `er` (bulk, 7628 prepreg) | 4.4 | MEASURED (stackup) |
| `sqrt(er)` | 2.0976177 | DERIVED |
| Band edge `f_max` | 6.0 GHz | given |
| Trace `w` / gap `g` | 0.360 / 0.2005–0.2010 mm | MEASURED |
| `eps_eff` (Ghione/Naghed-Wolff CBCPW) | 3.1557 | given (conformal map) |
| `n_cpw = sqrt(eps_eff)` | 1.776429 | DERIVED |
| `n_pp = sqrt(er)` | 2.0976177 | DERIVED |
| `lambda_g` (CPW, 6 GHz) | 28.1268 mm → 12.799 °/mm | DERIVED (matches given 28.13 / 12.80) |
| `lambda_pp` (6 GHz) | 23.8201 mm | given |
| `beta_pp` | 0.263769 rad/mm = 15.113 °/mm | DERIVED |
| Wave impedance in prepreg `eta = 376.730/sqrt(er)` | 179.599 Ω | DERIVED |
| Stitch pitch, axis-aligned arm | 0.800 mm | MEASURED |
| Stitch pitch, 45° arm (projected) | 1.13137 mm | MEASURED |
| Via barrel `d` (drill) | 0.15 mm | MEASURED |
| Adopted periodic rule `lambda_pp/20` | 1.19100 mm | given |
| Declared phase ceiling, 1.0 mm copper | 12.799° at 6 GHz | DERIVED |

Two further derived facts I will lean on throughout:

**(F1) The parallel-plate region is deeply sub-wavelength in thickness.**
The first non-TEM parallel-plate mode (TM₁) cuts off at
`f_c = c/(2 h sqrt(er)) = 299.792458/(2 × 0.2104 × 2.0976177) = 339.6 GHz`. **DERIVED.**
`h/lambda_pp = 0.00883`. So the only parasitic mode in the F.Cu-pour↔In1 sandwich is
the TEM parallel-plate mode, it has no cutoff, and — as the adopted rule correctly
states — it travels at bulk `er`, not at `eps_eff`. That part of the existing rule is
right and I do not disturb it.

**(F2) The CBCPW dominant mode is intrinsically leaky into that TEM mode.**
Because `n_pp (2.0976) > n_cpw (1.7764)`, the guided CPW mode is phase-matched to a
parallel-plate wave travelling at
`theta = arccos(n_cpw/n_pp) = arccos(0.846880) = 32.13°` from the arm axis. **DERIVED.**
This is the Shigesawa–Tsuji–Oliner conductor-backed leakage mechanism
(*"Conductor-backed slot line and coplanar waveguide: dangers and full-wave analysis"*,
IEEE MTT-S 1988; *Radio Science* 26(2), 1991; Tsuji/Shigesawa/Oliner, IEEE T-MTT 46,
1998). **CITED.** It is a *continuous, uniform-line* leakage: it needs no discontinuity.
The stitch wall's job is to remove the mode it leaks into. Where the wall is absent, the
channel is open — but only over the length it is absent, and this is the single most
important structural fact for the question asked.

---

## 1. What a `lambda/20` rule is actually protecting, and whether one defect is governed by it

### 1.1 A stitch wall does two different jobs

**(J1) Local equipotential (quasi-static, non-resonant).** Hold F.Cu pour and In1 at the
same potential at every point, so that (i) the realized line is the CBCPW the conformal
map describes, and (ii) the two coplanar grounds stay equipotential with each other so
the CPW *even* mode is not converted to the *odd* (coupled-slotline) mode. The
equipotential requirement is the classic CPW constraint that motivates air bridges and
ground straps (Wen, IEEE T-MTT 17(12), 1969; Simons, *Coplanar Waveguide Circuits,
Components and Systems*, Wiley 2001, ch. 2 and 7; Gupta/Garg/Bahl/Bhartia, *Microstrip
Lines and Slotlines*, 2nd ed., ch. 7). **CITED.**

**(J2) Wall (wave, periodic-structure).** Prevent power that *has* entered the
parallel-plate region — from the launch antipad, from the QFN transition, from the In2
traces passing underneath, from (F2) — from propagating laterally across the board and
re-coupling into another arm.

**The `lambda/20` rule is a J2 rule.** Every statement of it in the packaging literature
is a statement about a *repeated* aperture: the wall must "appear solid to an impinging
wave." The SIW form of the same rule (`p < lambda_g/5`, `p/d ≲ 2–2.5`, Deslandes & Wu,
IEEE MWCL 11(2) 2001; Xu & Wu, IEEE T-MTT 53(1) 66–73, 2005; Deslandes & Wu, IEEE T-MTT
54(6) 2516–2526, 2006) is explicitly a *per-unit-length leakage constant* — for `p/d = 2`
the quoted leakage is ≈ 0.01 dB per guided wavelength, and below `p/d = 1.5` it falls
under 0.001 dB/λ_g. **CITED.** A leakage *constant* is meaningless for one cell.

### 1.2 The three things a periodic wall has that one defect does not

1. **Coherent accumulation.** In a periodic wall of N cells each leaking field amplitude
   `t`, the leaked fields carry a fixed phase progression set by the guided wave
   (`beta_cpw × p` per cell = 14.5° per cell here, **DERIVED**). They form a leaky-wave
   array beaming at the 32.13° phase-match angle: total leaked field `∝ N·t`, and the
   loss does not saturate — it accumulates over the whole 14.4 mm arm and over the whole
   board. Uniformly enlarging `p` raises `t` *and* keeps the phasing, so leakage per unit
   length rises and then integrates. One defect radiates once. Its leaked *power* is
   `t_a²` and it does not accumulate anywhere.

2. **A Bragg / grating-transparency edge.** A periodic wall becomes transparent when the
   period supports a propagating Floquet harmonic. This is the origin of the SIW
   `p < lambda_g/5` bound and of Haydl's finding that under-stitched CBCPW ground planes
   "behave like overmoded patch antennas supporting parallel-plate modes and show
   numerous resonances" (W. H. Haydl, *On the use of vias in conductor-backed coplanar
   circuits*, IEEE T-MTT **50**(6) 2059–2074, 2002 — the paper's central conclusion is
   that **placement**, not count, decides suppression). **CITED.** A single cell has no
   reciprocal lattice and therefore no Bragg condition. It has only its own resonance
   (§2.4).

3. **A stopband that must survive N cells in cascade.** The `lambda/20` margin is large
   *because* it is distributed. Written as a resonance margin it says: the shorted
   interval between adjacent vias is a half-wave resonator at `L = lambda_pp/2`, so
   `p = lambda_pp/20` puts every cell's own resonance at **10× the band edge**:

   `f_res(L) = c / (2 L sqrt(er)) = 71.4602 / L  [GHz, L in mm]`  **DERIVED**
   `f_res(1.19100 mm) = 60.00 GHz = 10.0 × 6 GHz`  **DERIVED**

   A 10× margin is characteristic of a rule where each cell's residual reactance must be
   small *enough that twenty of them in cascade still look like a wall*. It is not the
   margin you would demand of one isolated resonator.

### 1.3 The quasi-static half is size-insensitive — which is why the rule must be a wave rule

Worth demonstrating, because it kills the intuitive worry that a missing via inserts a
big series inductance in the ground return.

An unshorted patch of parallel plate of length `L` and width `W` has loop inductance
`L_eq = mu_0 · h · (L/4W)` — it scales with **aspect ratio**, not absolute size. **DERIVED**
(from `Z_pp = eta·h/W`, `beta_pp = omega·sqrt(er)/c`, `Z_pp·beta_pp/omega = mu_0 h/W`;
two shorted stubs of length `L/2` in parallel give `X = (Z_pp/2)·tan(beta_pp L/2)`).

Compare the pour-to-In1 tie impedance at the *worst* point of each case, using a single
via inductance `L_via = (mu_0 h/2π)[ln(4h/d)+1] = 0.1147 nH → X = 4.32 Ω at 6 GHz`
(**DERIVED**; standard via formula, e.g. Johnson & Graham, *High-Speed Digital Design*):

| Point | Spreading reactance | + end vias in parallel | Total |
|---|---|---|---|
| Midpoint of a compliant 1.1314 mm cell (`W ≈ L`) | 2.51 Ω | 2.16 Ω | **4.67 Ω** |
| Midpoint of a 2.006 mm aperture (`W ≈ L`) | 2.55 Ω | 2.16 Ω | **4.71 Ω** |
| Directly on a via | 0 | — | **4.32 Ω** |

**DERIVED.** The aperture midpoint is 0.9 % worse than a compliant cell midpoint and
9 % worse than sitting on a via. The quasi-static equipotential job (J1) is essentially
**indifferent to aperture length**, provided the return current can spread transversely —
i.e. provided the *lattice is intact on the transverse neighbours of the defect cell*.
This is a hard condition, not a footnote: a single missing post in a 2-D lattice keeps
`L/W ≈ 1`; a missing **row** (a keep-out strip several mm long that removes vias on both
transverse sides) forces `L/W >> 1` and the inductance then does grow linearly with `L`.

**Consequence:** the criterion must be written in terms of `L_a/lambda_pp` (a wave
criterion), and the relaxation applies to a *missing post*, never to a *missing row*.

### 1.4 Answer to Q1

The `lambda/20` rule protects against (i) coherent, per-unit-length, accumulating
leakage into the parallel-plate mode along a periodic wall, and (ii) the periodic wall's
transparency/stopband edge. **A single non-periodic defect is governed by a different
rule.** It has no coherent buildup, no Bragg condition, and no cascade requirement. It is
governed instead by (a) a single-aperture *power budget* — it must not dominate the
leakage the compliant wall already contributes — and (b) its own half-wave resonance.
Both are looser than `lambda_pp/20` at the same length, but only by a bounded factor,
and the bound is what §2 derives.

---

## 2. Deriving the acceptance criterion

### 2.1 (a) The aperture as a coupling window — how coupling scales with `L_a`

The gap between two flanking vias is a window of height `h` and along-arm length `L_a`
in a conducting boundary, illuminated by the CPW mode's tangential H. For `L_a >> h`
and `L_a << lambda_pp/2` this is the narrow-slot limit of Bethe small-aperture theory.
The longitudinal magnetic polarizability of a narrow slot of length `L`, width `w` is

```
alpha_m(L) = pi · L^3 / [ 24 ( ln(4L/w) - 1 ) ]
```

(H. A. Bethe, *Phys. Rev.* **66**, 163, 1944; R. E. Collin, *Field Theory of Guided
Waves*, 2nd ed., §7.3 — narrow-slot polarizability). **CITED.** Coupled field `∝ alpha_m`;
coupled **power** `∝ alpha_m²`, i.e. **`∝ L_a^6 / ln²`** — roughly **36 dB per octave of
`L_a`** in the deep sub-resonant regime.

Define `g(L) = L³ / [24(ln(4L/h) − 1)]` with `w = h = 0.2104 mm` (the π cancels in
ratios). **DERIVED:**

| `L` (mm) | `g(L)` | field vs 1.1314 mm cell | power vs cell |
|---|---|---|---|
| 0.800 (axis pitch) | 0.012389 | 0.425 | −7.4 dB |
| 1.13137 (45° pitch) | 0.029173 | 1.000 | 0 dB (reference) |
| 1.19100 (`λ/20`) | 0.033210 | 1.138 | +1.1 dB |
| 1.58800 (`λ/15`) | 0.069307 | 2.376 | +7.5 dB |
| 1.98501 (`λ/12`) | 0.123878 | 4.246 | +12.6 dB |
| 2.38201 (`λ/10`) | 0.200182 | 6.862 | +16.7 dB |
| 2.97751 (`λ/8`) | 0.362425 | 12.42 | +21.9 dB |
| 3.97002 (`λ/6`) | 0.784378 | 26.89 | +28.6 dB |
| 5.95502 (`λ/4`) | 2.359 | 80.88 | +38.2 dB |

The conservative EMC alternative, `SE = 20·log10(lambda/2L)` (H. Ott, *Electromagnetic
Compatibility Engineering*, Wiley 2009, §6; C. R. Paul, *Introduction to EMC*, 2nd ed.,
ch. 10) **CITED**, gives only 6 dB/octave and yields `SE = 20.0 dB` exactly at
`L = lambda/20` — a neat confirmation that the inherited divisor 20 is "buy 20 dB of
shielding per aperture." I use the Bethe scaling for the criterion because it is the
correct physics below resonance and it is the **stricter** of the two (it punishes
enlargement 6× harder per octave); I quote the SE result where it bounds the answer from
the pessimistic side.

### 2.2 (c) Does the opposite flank being stitched matter? Yes — twice, in opposite directions

**In favour of the relaxation.** What ties the two F.Cu coplanar grounds together at the
defect is the path *ground A → its bounding vias → In1 → the opposite flank's vias →
ground B*. Because the opposite flank is stitched at 0.80–1.13 mm, In1 is held at ground
potential immediately across the trace, at a distance of `w + 2g = 0.761 mm` — a small
fraction of `lambda_pp` (0.032 λ). The equalizing path is therefore short and stiff, and
the odd/slotline mode is not appreciably excited. Additionally, the F.Cu pour is a single
continuous copper region, so the two flanks are DC-connected regardless; the excitation
of the odd mode is driven only by the *difference* in tie impedance, which §1.3 shows is
≈ 0.4 Ω out of ≈ 4.3–4.7 Ω. **DERIVED.**

**Against the relaxation.** Asymmetry is precisely what drives even→odd and even→
parallel-plate conversion (Wen 1969; Simons 2001 §7 on air-bridge placement; Haydl 2002
on via placement). **CITED.** An aperture on one flank only *is* an asymmetry. This is
why the relaxation cannot be unbounded — it caps at the point where the asymmetric
scatterer's leakage becomes comparable to everything else the arm leaks.

**Therefore three structural conditions, not just a length bound:**

- **C1.** The opposite flank must be compliant over `±L_a` about the defect.
- **C2.** No facing aperture on the opposite flank within `±L_a` longitudinally. Two
  apertures facing each other across the trace at the same `x` are a *different* and
  worse structure: symmetric flank-float relative to In1 (strong common/parallel-plate
  excitation) if equal, maximal asymmetry if unequal. Excluded from the relaxation
  entirely — apply `lambda_pp/20` to both.
- **C3.** The lattice must be intact on the *transverse* neighbours of the defect cell
  (§1.3). One missing post, never a missing row.

### 2.3 (b) What actually drives the conversion — and why a uniform-section aperture is the mild case

Two mechanisms, and they are not equally strong here.

**Discontinuity-driven conversion (strong).** At a bend, a pad, a via transition, a
package launch, or an antipad edge, the current distribution between the coplanar
grounds and In1 must redistribute. That redistribution flows *through* the stitch vias,
and a missing via there is doing real work. Nothing in this note relaxes anything at a
discontinuity.

**Uniform-line leaky-mode conversion (weak, and length-limited).** (F2) says the arm
leaks continuously wherever the parallel-plate mode is not suppressed. But over the
aperture the leaky wave has `L_a/lambda_pp = 0.084` of a wavelength to develop, and the
wave it launches leaves at 32.13° from the axis — it travels 2.5 mm transversely in
`2.5/sin(32.13°) = 4.70 mm` of path (**DERIVED**) and meets 4–6 further via rows on the
way, each of which reflects it. Independent estimate of one row's rejection: a shunting
via `X = 4.32 Ω` across a parallel-plate cell of impedance `Z = eta·h/p = 179.599 ×
0.2104/0.800 = 47.24 Ω` gives `|S21| = 2X/sqrt(4X² + Z²) = 0.1800 = −14.9 dB` per row.
**DERIVED.** So: **a single flanking row is only a ~15 dB wall at 6 GHz; the 2-D depth of
the lattice supplies the rest.** That is why one missing post in one row is a small event
— and it is also a warning that "there is one row of vias" was never the whole
protection.

**Fourth condition:**

- **C4.** The aperture must lie in a straight, uniform section, and its edges must be
  separated from any *other* unreferenced or discontinuous feature (SMA antipad edge,
  pad, bend, In2 crossing) by at least `L_a`. If the separation is less than `L_a`, treat
  the features as **one** aperture whose length is the combined span, and apply the
  criterion to that. This is self-scaling and needs no second number.

C4 matters concretely on this board: the largest unreferenced feature is not any stitch
aperture but the **launch** — a ≥ 3.5 mm In1 antipad with a 1.4–1.75 mm unreferenced
interval. **MEASURED.**

### 2.4 (d) Resonance conditions

**The dominant one: the shorted–shorted parallel-plate half-wave resonance.** Two
shorting posts separated by `L_a` in a parallel-plate region form a half-wave resonator:

```
f_res(L_a) = c / (2 · L_a · sqrt(er)) = 71.4602 / L_a   [GHz, L_a in mm]     DERIVED
```

For any resonance to fall **inside DC–6 GHz** requires `L_a ≥ 71.4602/6 = 11.910 mm =
lambda_pp/2`. **DERIVED.** So there is a bright line at 11.91 mm: below it, no in-band
defect resonance exists at all; at and above it, one does, and the failure is
catastrophic rather than gradual. Since the band is DC-to-6 GHz (not a narrow band), a
defect cannot "hide between resonances."

**Second, transverse:** the defect cell is `L_a × p_transverse`; the (0,1) mode of an
0.80 mm transverse cell sits at `71.4602/0.800 = 89.3 GHz` — irrelevant. **DERIVED.**

**Third, the accepted launch resonance, as a scale check.** The ≥ 3.5 mm circular antipad
is a circular parallel-plate cavity; its TM₁₁ mode is at
`f = 1.84118 c /(2π a sqrt(er)) = 1.84118 × 299.792458 /(2π × 1.75 × 2.0976177) =
23.94 GHz` (**DERIVED**; Balanis, *Antenna Theory*, circular-patch cavity model
**CITED**) — a margin of only **M = 4.0** over the band edge. The board **already
accepts, by unavoidable necessity, an unreferenced feature with a 4× resonance margin,
1.75× longer than the criterion I am about to set.** Marked JUDGEMENT as an argument
(the antipad is symmetric about the arm axis and sits at an engineered transition, so its
sensitivity differs), but it bounds the scale of the discussion: a stitch aperture held
to a *tighter* margin than the launch cannot be the board's limiting unreferenced feature.

**Fourth, multi-defect coherence.** Two or more defects add coherently if their
separation makes the leaked parallel-plate waves arrive in phase. The dangerous
separations are integer multiples of `lambda_pp = 23.820 mm`, and half-integer multiples
where the reflected path closes (`11.910 mm`), and along the arm, `lambda_g/2 =
14.063 mm`. **DERIVED.** With arms 14.4 mm long, a 11.9 mm separation between two defects
on one arm is geometrically reachable. Condition:

- **C5.** No two apertures within ±15 % of `lambda_pp/2 = 11.910 mm`, `lambda_pp =
  23.820 mm`, or `lambda_g/2 = 14.063 mm` of each other, measured along the straight-line
  separation between their centres, on the same arm or on different arms.

### 2.5 The budget: setting the number

The criterion I adopt is a **power budget, not a resonance margin** (the resonance
margin is enormous everywhere below 11.91 mm and would license an absurd relaxation on
its own). The statement:

> **A single isolated aperture may contribute no more leaked power than the entire
> compliant stitch wall of one arm already contributes. Equivalently: the defect may at
> most double (+3.0 dB) that arm's parallel-plate coupling budget.**

This is the right comparison, and deliberately conservative in two ways: the compliant
cells are summed **incoherently** (understating the reference, since a periodic wall's
leakage is partly coherent), while the single defect radiates omnidirectionally with no
array gain to work in its favour.

Compliant cells per arm, both flanks, over the stitched 75 % of 14.4 mm = 10.8 mm:

```
45°  arms:  N = 2 × 10.8 / 1.13137 = 19.09     DERIVED
axis arms:  N = 2 × 10.8 / 0.800   = 27.00     DERIVED
```

The 45° arms set the worst-case arm-leakage baseline; that asymmetry is already accepted
by the design:

```
45°  : N·g² = 19.09 × 0.029173² = 1.6247e-2
axis : N·g² = 27.00 × 0.012389² = 4.144e-3
ratio = 3.920 → 5.93 dB already accepted between arm families.   DERIVED
```

**Solve `g(L_a)² = N·g(p)²` (equal-budget) against the worst-case arm:**

```
g(L_a) = sqrt(19.09) × 0.029173 = 0.127455
→ interpolating the table between L = 2.000 (0.126344) and L = 2.382 (0.200182):
L_a = 2.006 mm  =  lambda_pp / 11.87                                       DERIVED
```

Against the *densest* arm read as a per-arm ratio (`sqrt(27) × g(0.800) = 0.064377`) the
answer is `L_a = 1.542 mm = lambda_pp/15.4`. **DERIVED.** For an array whose product is
*relative* phase and *relative* isolation, the array-level (absolute) reading is the
correct one — no arm may exceed the worst compliant arm by more than 3 dB — and it gives
2.006 mm for every arm. I report the per-arm reading as the tighter green line.

**The derived number lands within 1 % of `lambda_pp/12`. I round down to `lambda_pp/12`
and state the criterion there.**

### 2.6 Independent cross-check against the SIW literature

Aperture leakage is physically governed by the **gap-to-wavelength** ratio, not by `p/d`
alone. The Deslandes/Wu boundary case (`p = lambda_g/5`, `p/d = 2` ⇒ gap `= 0.1 lambda_g`)
yields ≈ 0.01 dB/λ_g of leakage. **CITED.** For this board:

| Case | gap `(p − d)` | gap / `lambda_pp` | vs SIW boundary (0.100) |
|---|---|---|---|
| axis-aligned compliant cell | 0.650 mm | 0.0273 | 3.7× inside |
| 45° compliant cell | 0.981 mm | 0.0412 | 2.4× inside |
| **proposed limit, 1.985 mm** | **1.835 mm** | **0.0770** | **1.30× inside** |
| `lambda_pp/6` = 3.970 mm | 3.820 mm | 0.1604 | 1.6× outside |

**DERIVED.** Even if the *entire* wall were rebuilt at the proposed aperture length, its
gap would still sit inside the Deslandes/Wu boundary case that yields 0.01 dB/λ_g. One
such cell out of nineteen is far inside it.

Honest caveat, marked **JUDGEMENT**: this lattice has `p/d = 0.800/0.15 = 5.3` (axis) and
`7.5` (45°), against the SIW guideline of `p/d ≲ 2–2.5`. By SIW standards this is a
*sparse* wall (via area fill 2.76 %). I do not claim the lattice is SIW-grade — §2.3's
−14.9 dB per row is the honest figure for one row. What I claim is only that the *gap*
criterion, which is the one Bethe theory says governs aperture coupling, is comfortably
met, and that the 2-D depth of the lattice supplies the confinement the single row does
not. This is the weakest link in the chain and the first thing a full-wave solve should
check.

---

## 3. The criterion, with its number

`lambda_pp = 23.8201 mm` at 6 GHz, `er = 4.4`.

### 3.1 Length bands for a single isolated aperture

| Band | `L_a` | `f_res` | margin | Verdict |
|---|---|---|---|---|
| Compliant | ≤ `λ_pp/20` = **1.191 mm** | 60.0 GHz | 10× | the periodic rule |
| **Green** | ≤ `λ_pp/15` = **1.588 mm** | 45.0 GHz | 7.5× | **ACCEPT unconditionally** |
| **Amber** | ≤ `λ_pp/12` = **1.985 mm** | 36.0 GHz | 6× | **ACCEPT if C1–C5 hold** |
| Red | ≤ `λ_pp/6` = **3.970 mm** | 18.0 GHz | 3× | CONDITIONAL — full-wave required, no engineering-judgement pass |
| Veto | > `λ_pp/6` | < 18 GHz | < 3× | **REJECT.** Hard veto at `λ_pp/4` = 5.955 mm (12 GHz, 2×): beyond it the bounding stubs approach quarter-wave and flip sign |
| Catastrophic | ≥ `λ_pp/2` = 11.910 mm | ≤ 6.0 GHz | ≤ 1× | in-band resonance exists |

**The number: `L_a ≤ 1.985 mm` (= `λ_pp/12` = 1.67 × the periodic rule), subject to
C1–C5.** Below 1.588 mm, C1–C5 are advisory rather than gating.

Equivalent statements of the same criterion, for use in whatever form is convenient:
- `L_a / lambda_pp ≤ 1/12 = 0.0833`
- the aperture's own half-wave resonance must sit at **≥ 6× the band edge (≥ 36 GHz)**
- the aperture's edge-to-edge gap must be `≤ lambda_pp/13`
- generic form for any band edge: `L_a ≤ c / (12 · f_max · sqrt(er))`

### 3.2 Conditions (restated as a checklist)

- **C1** Opposite flank compliant over `±L_a`.
- **C2** No facing aperture on the opposite flank within `±L_a` longitudinally.
- **C3** Lattice intact on the transverse neighbours — a missing *post*, not a missing
  *row*. If the defect spans the full transverse depth of the lattice, no relaxation.
- **C4** In a straight uniform section; separated from any other unreferenced or
  discontinuous feature (antipad edge, pad, bend, In2 crossing) by at least `L_a`. If
  closer, merge them and apply the criterion to the combined span. **No relaxation
  whatsoever inside the launch region.**
- **C5** Multi-defect separations avoid ±15 % of 11.910 / 14.063 / 23.820 mm.

### 3.3 Two or three apertures on one board

Incoherent power addition against the *same* absolute budget (`g = 0.127455`):

| Count | per-aperture `g` limit | `L_a` limit each | as `λ_pp/x` |
|---|---|---|---|
| 1 | 0.127455 | **2.006 → state 1.985 mm** | λ/12 |
| 2 | 0.090124 | **1.739 mm** | λ/13.7 |
| 3 | 0.073586 | **1.619 mm** | λ/14.7 |

**DERIVED.** Note how flat this is — the sixth-power law means the budget divides slowly.
Practical form: **`Σᵢ g(Lᵢ)² ≤ g(1.985 mm)²`**, i.e. approximately `Σᵢ Lᵢ⁶ ≤ (1.985)⁶`
before the log correction (the log makes the exact solution ~2 % stricter than the pure
sixth-root, which is why the table numbers are 1.739/1.619 rather than 1.77/1.65).

Two further constraints that do not come out of the power budget:
- **At most one aperture per arm.** The product is *relative* phase between arms. A
  perturbation common to all arms cancels; a unique one does not. Two on one arm makes
  that arm doubly unique and risks C5.
- **Three is the practical ceiling.** Beyond three the defects are no longer "isolated" —
  they are a sparse aperiodic wall, and the periodic argument of §1.2 starts to apply
  again. At n ≥ 4, revert to `lambda_pp/20` for all of them.

### 3.4 What I am NOT relaxing

`lambda_pp/20 = 1.191 mm` stands unchanged as the **rule for the wall**, i.e. for the
compliant fraction, for anything at a discontinuity, for anything inside a launch region,
for facing aperture pairs, and for any defect that is a missing row rather than a missing
post. The relaxation is to a *single non-periodic missing post in an intact 2-D lattice
in a uniform section*, and to nothing else.

---

## 4. What would falsify this, and the expected penalty in dB

### 4.1 Predicted penalty at the accept limit (`L_a = 1.985 mm`)

| Metric | Prediction at the accept limit | Tag |
|---|---|---|
| That arm's parallel-plate coupling budget | **+2.9 dB** (by construction of §2.5: 19.09 → 37.1 in `g²` units) | DERIVED |
| Absolute leaked fraction, one arm | ≈ −42 dB with the defect vs ≈ −45 dB compliant, ±10 dB | DERIVED-by-extrapolation / JUDGEMENT |
| Arm-to-arm isolation, board path only | ≲ −80 dB (leaked power must also *re-couple* into another arm's CPW mode through a similarly small coefficient, after 2-D spreading and re-scattering) | JUDGEMENT |
| Arm-to-arm isolation, **as measured** | change **< 0.01 dB**. The PE42482 specifies 41 dB isolation at 6 GHz (pSemi PE42482 datasheet, **CITED**); a board path at −80 dB moves a −41 dB total by 0.0004 dB. Even a −55 dB board path would move it 0.11 dB | DERIVED |
| Insertion-loss ripple added in DC–6 GHz | **< 0.01 dB** p-p; no in-band resonance exists below 11.91 mm | DERIVED (resonance) / JUDGEMENT (magnitude) |
| Differential phase contribution at 6 GHz | **< 0.22°** by a deliberately pessimistic bound; realistically **< 0.05°** | see below |

*Phase bound, shown.* Pessimistically assume the entire 0.4 Ω tie-impedance degradation
of §1.3 appears as *series* ground inductance distributed over the aperture (it does not
— by even-mode symmetry the tie current is near zero in a uniform section). The line's
own series reactance is `omega·L' = 2π·6e9·0.3037 nH/mm = 11.45 Ω/mm`, so over 1.985 mm
the total is 22.7 Ω. `ΔL'/L' = 0.4/22.7 = 1.76 %`, and `Δφ = 12.799 °/mm × 1.985 mm ×
0.0176/2 = 0.224°`. **DERIVED.** Against the declared 1.0 mm ≡ 12.799° ceiling that is
**1.7 % of the phase budget, equivalent to 0.017 mm of copper.**

### 4.2 The honest answer: at the accept limit the penalty is below the measurement floor

| Measurement | Realistic floor | Prediction | Verdict |
|---|---|---|---|
| Differential S21 phase, PCB-mount SMA, 6 GHz | ±0.5–1.0° per connection; ±0.7–1.4° for a 2-port | < 0.22° | **below floor** |
| \|S21\| magnitude repeatability | ±0.05–0.1 dB | < 0.01 dB | **below floor** |
| Arm-to-arm isolation | −60 to −70 dB practical fixture floor; masked anyway by the switch's 41 dB | < 0.01 dB change | **below floor by orders of magnitude** |
| TDR impedance bump | ~0.5–1 Ω, spatial resolution ~5 mm at 30 ps rise | < 1 Ω over 2 mm | **smeared out, below floor** |

**Stated plainly: this board cannot falsify this criterion.** A board that measures fine
is not evidence that the criterion is right — it is evidence only that the effect is,
as predicted, unmeasurable. Anyone who cites a passing board measurement as validation of
this number has validated nothing.

### 4.3 The experiment that WOULD falsify it

A deliberate-defect coupon on the same stackup: N nominally identical 14.4 mm CBCPW arms
between SMA jacks, one fully compliant, the others with a single deliberate aperture at
the arm midpoint on one flank at `L_a` = 2, 4, 6, 8, 12 mm. Measure S21 magnitude and
phase and adjacent-arm coupling, DC–20 GHz (40 GHz preferred). Falsifiable predictions:

1. The **12 mm** arm shows an S21 notch and an adjacent-arm coupling peak at
   **≈ 6.0 GHz**; the 8 mm arm at ≈ 8.9 GHz; the 6 mm at ≈ 11.9 GHz; the 4 mm at
   ≈ 17.9 GHz. All from `f_res = 71.4602/L_a`. **If the 12 mm defect produces no 6 GHz
   feature, the resonance model in §2.4 is wrong and the whole resonance-margin framing
   collapses.**
2. Below resonance, adjacent-arm coupling rises with `L_a` at a slope approaching
   **≈ 36 dB per octave** (Bethe, `L^6`). **If the observed slope is closer to 6 dB/octave
   (the EMC `SE` formula) the budget of §2.5 is too generous by roughly a factor of two
   in length** — the equal-budget point under 6 dB/octave scaling moves from 2.0 mm to
   ≈ 5.6 mm, so a *flatter*-than-predicted slope would actually vindicate the number as
   conservative. **A slope STEEPER than 36 dB/octave, or any coupling at all at 2 mm
   above the compliant arm's floor, falsifies it in the dangerous direction.**
3. The **2 mm** arm is indistinguishable from the compliant arm below 10 GHz, in both
   magnitude and phase, to within the paired-coupon floor (~0.1° with the same connector
   on the same panel).
4. Adding the missing via back (a single rework) must produce **no** measurable change on
   the 2 mm arm and a **large** one on the 12 mm arm.

Prediction 3 is the criterion's own accept limit and is the one to run.

---

## 5. Limits of this answer

**Textbook / cited, and I would defend these without qualification:**
- Parallel-plate TEM has no cutoff and travels at bulk `er`; TM₁ at 339.6 GHz here.
- CBCPW's dominant mode is intrinsically leaky when `n_pp > n_cpw`, at 32.13° here
  (Shigesawa/Tsuji/Oliner).
- Vias suppress parallel-plate modes and *placement* is the governing variable
  (Haydl 2002).
- Periodic post-wall leakage is a per-unit-length constant governed by pitch and gap
  relative to wavelength (Deslandes & Wu; Xu & Wu).
- Narrow-slot polarizability `∝ L³/ln`, coupled power `∝ L⁶` (Bethe; Collin).
- `SE = 20 log10(λ/2L)` for a slot in a shield (Ott; Paul).
- The CPW equipotential requirement and its odd-mode failure (Wen; Simons; Gupta et al.).
- Two shorts separated by `L` in a parallel plate resonate at `L = λ/2`.
- The inductance of an unshorted parallel-plate patch scales with aspect ratio, not size.

**My engineering judgement, and therefore the parts to argue with:**
- **The choice of budget** — "the defect may contribute at most as much as the whole
  compliant wall of one arm" (+3 dB). This is the single decision that sets the number.
  A stricter house rule (+1 dB) gives `g = 0.0673 → L_a ≈ 1.55 mm`; a looser one (+6 dB)
  gives `g = 0.221 → L_a ≈ 2.5 mm`. The whole answer lives between 1.5 and 2.5 mm and I
  am not going to pretend otherwise. `λ_pp/12` is the middle of that, and it happens to
  land within 1 % of the +3 dB solution.
- The incoherent summation of the 19 compliant cells (conservative — they are partly
  coherent, which would *widen* the allowance).
- The extension to n defects by incoherent power addition and the n ≥ 4 cutoff.
- The −42 dB absolute leakage figure, which is a sixth-power extrapolation across a 2.4×
  gap ratio from a single cited SIW datum. I give it ±10 dB and would not build on it.
- The `< 0.22°` phase bound. It is a bound, not a calculation.
- The "n_a = 1 per arm" and the antipad scale-check arguments.

**Where a full-wave solve is genuinely required and no closed form exists:**
1. **The actual CPW-mode → parallel-plate-mode conversion coefficient at a single
   defect.** This is the number the whole criterion is a proxy for and there is no
   analytic expression for it. Needs a 3-D FEM/FDTD solve (HFSS, CST, openEMS) with the
   real via lattice, real barrel geometry, real pour, and mode-decomposed ports.
2. **Whether a 2.76 %-fill post lattice with `p/d = 5.3–7.5` really behaves as a wall at
   6 GHz.** §2.3 gives −14.9 dB per row from a lumped shunt model; the 2-D cascade and
   the diffractive spreading around a defect are not captured by that. This is the
   weakest link in the chain.
3. **The differential phase.** Nothing short of a full-wave S-parameter extraction with
   and without the via will settle 0.05° vs 0.22°.
4. **Any aperture within one aperture-length of the launch antipad.** The antipad is a
   ≥ 3.5 mm unreferenced circular cavity resonant at 23.9 GHz; superposing a stitch
   aperture on it is a different structure and C4 refuses to rule on it by hand.
5. **The Bethe-vs-SE slope question** (prediction 2 of §4.3), which decides whether the
   criterion is conservative by 1× or by 3×.

**One last statement of position.** It is entirely possible that the right answer here was
`lambda_pp/20` unchanged, and I looked hard for a reason it should be. The reason it is
not is specific and checkable: `lambda_pp/20` encodes a **10× resonance margin plus a
cascade requirement plus coherent accumulation over N cells**, and a lone defect has the
first and neither of the other two. Removing the cascade and the coherence, while holding
the leaked-power budget fixed at the level the compliant wall already spends, buys a
factor of **1.67 in length and nothing more**. That factor is small, it is bounded, it is
conditioned on C1–C5, and it does not extend to a second defect on the same arm, to a
missing row, to a discontinuity, or to a launch.

---

## Sources

- W. H. Haydl, *On the use of vias in conductor-backed coplanar circuits*, IEEE T-MTT
  **50**(6) 2059–2074, 2002 —
  [IEEE Xplore](https://ieeexplore.ieee.org/document/1006419/) ·
  [Fraunhofer record](https://publica.fraunhofer.de/entities/publication/2fac46a0-783a-4922-806b-a52865656133)
- H. Shigesawa, M. Tsuji, A. A. Oliner, *Dominant mode power leakage from printed-circuit
  waveguides*, Radio Science **26**(2), 1991 —
  [Wiley](https://agupubs.onlinelibrary.wiley.com/doi/pdf/10.1029/90RS01148); and
  *Conductor-backed slot line and coplanar waveguide: dangers and full-wave analysis*,
  IEEE MTT-S 1988. Follow-up:
  [*More investigations of leakage and nonleakage conductor-backed CPW*](https://ieeexplore.ieee.org/document/709424)
- G. E. Ponchak et al., *Leakage phenomena in multilayered conductor-backed coplanar
  waveguides* — [IEEE Xplore](https://ieeexplore.ieee.org/document/248521/); and
  [*Leakage losses for the dominant mode of CBCPW*](https://ieeexplore.ieee.org/document/122412/)
- Y. Cassivi / F. Xu / K. Wu, *Guided-wave and leakage characteristics of substrate
  integrated waveguide*, IEEE T-MTT **53**(1) 66–73, 2005 —
  [ResearchGate](https://www.researchgate.net/publication/3130710_Guided-wave_and_leakage_characteristics_of_substrate_integrated_waveguide);
  D. Deslandes & K. Wu, *Accurate modeling, wave mechanisms, and design considerations of
  a SIW*, IEEE T-MTT **54**(6) 2516–2526, 2006 —
  [review with the p/d rules](https://www.theiet.org/media/11283/review-of-substrate-integrated-waveguide-circuits-and-antennas.pdf)
- Via-fence `λ/20` packaging rule of thumb —
  [Sierra Circuits, RF via design](https://www.protoexpress.com/blog/rf-pcb-via-design-challenges-with-layout-solutions/) ·
  [AtlasPCB, via stitching and ground-plane isolation](https://www.atlaspcb.com/blog/rf-via-stitching-ground-plane-isolation/) ·
  [EDN, via spacing on high-performance PCBs](https://www.edn.com/via-spacing-on-high-performance-pcbs/)
- Switch isolation floor: pSemi PE42482 SP8T, 41 dB isolation / 1.1 dB IL at 6 GHz —
  [product page](https://psemi.com/products/rf-switches/high-isolation-rf-switches/pe42482/) ·
  [datasheet PDF](https://www.psemi.com/pdf/datasheets/pe42482ds.pdf)
- Books used without a URL: H. A. Bethe, *Phys. Rev.* **66** 163 (1944); R. E. Collin,
  *Field Theory of Guided Waves* 2nd ed. §7.3 (narrow-slot polarizability); C. P. Wen,
  IEEE T-MTT **17**(12) 1969 (CPW); R. N. Simons, *Coplanar Waveguide Circuits,
  Components and Systems*, Wiley 2001; Gupta/Garg/Bahl/Bhartia, *Microstrip Lines and
  Slotlines* 2nd ed.; H. Ott, *EMC Engineering*, Wiley 2009 §6; C. R. Paul,
  *Introduction to EMC* 2nd ed. ch. 10; Johnson & Graham, *High-Speed Digital Design*
  (via inductance); Balanis, *Antenna Theory* (circular-patch cavity model).
