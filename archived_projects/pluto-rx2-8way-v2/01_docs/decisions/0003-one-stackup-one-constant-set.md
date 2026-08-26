---
id: 0003
date: 2026-07-30
status: superseded-by-0004
tags: [rf, provenance]
---
# 0003 — v2 derives its own microstrip constant set, because the fleet publishes three

## Context

Every RF number this board will publish — the via-fence pitch, the phase
budget, the drift tolerance, the impedance width — descends from ONE quantity:
`eps_eff`, the effective permittivity of a 0.36 mm F.Cu microstrip over the
solid In1.Cu reference on `JLC04161H-7628`.

`skills/kicad-pcb/references/rf-design.md` section 4(d) makes this a canon rule
— *"ONE STACKUP MUST HAVE ONE CONSTANT SET"* — after two boards on this same
laminate carried different constants. **On inspection today, the situation is
worse than the canon records, and the disagreement is INSIDE one board.**

Measured 2026-07-30, reading v1's own files and deriving independently:

| source | eps_eff | t_pd (ps/mm) | lambda_g @6 GHz | deg/mm | lambda_g/20 |
|---|---|---|---|---|---|
| v1 `nets.yaml` **phase block** (line ~374-6) | 3.350 | 6.105 | 27.29 mm | 13.19 | 1.3645 |
| `rf-design.md` **4(d)**, the canon | 3.350 | 6.105 | 27.29 mm | 13.19 | 1.3645 |
| v1 `nets.yaml` **RF50 netclass comment** (line ~73-4) | *(3.3229, implied)* | — | **27.41 mm** | — | **1.3705** |
| **my own Hammerstad-Jensen derivation** | **3.3286** | **6.0857** | **27.387 mm** | **13.145** | **1.3693** |
| the commissioning brief for this board | 3.328 | — | — | — | 1.37 |

Two things follow. First, **v1 carries two disagreeing constant sets in one
file**, and the netclass comment's 27.41 mm is the one the "1.37 mm" fence was
actually computed from — so the fence number in use across this family traces to
the number v1 does NOT use for phase. Second, **only my derivation is
reproducible from the stackup v1 declares.** I swept w in {0.35, 0.36, 0.37} and
copper thickness in {0, 0.035} mm; eps_eff 3.350 does not appear at any of the
six combinations. Its closest neighbour is 3.3356 (w = 0.37, t = 0.035), and
that is not the width this board routes.

This is not a rounding quarrel. Phase runs at ~13.1 deg/mm at 6 GHz, so the
board's headline artifact — a picosecond/degree table — is quoted in a unit that
a 0.4 % constant error moves. It is exactly the class of defect canon M-BOUND
exists for: *a published bound is REGENERATED, not typed*.

## Options

- **Inherit 3.350 from v1 and the canon.** REJECTED. I cannot reproduce it from
  the declared stackup, and I could find no measurement it is attributed to. To
  inherit it is to inherit a number whose provenance is a re-typed copy — canon
  M4's "an inherited waiver is a defect", applied to a constant. It also
  perpetuates the disagreement rather than resolving it.
- **Inherit 27.41 mm from v1's netclass comment** (which is what the "1.37 mm"
  fence actually came from). REJECTED for the same reason, plus it is the value
  v1's OWN phase block contradicts.
- **Re-derive from the declared stackup and publish the derivation.** CHOSEN.
- **Escalate and stop until someone finds 3.350's provenance.** REJECTED as
  disproportionate: the three values agree to 0.7 %, nothing downstream is
  unsafe at any of them (the fence gets *tighter* at larger eps_eff, and 1.3693
  is the middle value anyway), and the user is absent. It is recorded as an
  OWED question in BRIEF A6 instead.

## Decision

**v2 derives `eps_eff` ONCE, from the declared stackup, with Hammerstad-Jensen
including the Wheeler thickness correction, and every v2 document cites the
derived value rather than a re-typed copy.** The derivation is a command, not a
number. Where v2 disagrees with v1 or with the canon, v2 uses its own value and
says so here.

    w = 0.360 mm   (RF50 impedance width, unchanged from v1)
    h = 0.2104 mm  (JLC04161H-7628 top prepreg, v1 ADR-0003)
    er = 4.4       (declared Dk)
    t = 0.035 mm   (1 oz outer copper)
    ->  eps_eff  = 3.3286      Z0 = 50.29 ohm
        t_pd     = 6.0857 ps/mm
        lambda_g = 27.387 mm @ 6 GHz
        phase    = 13.145 deg/mm @ 6 GHz

The **via-fence pitch is guided lambda_g/20**, not free-space lambda/20 (which
would be 2.5 mm — the external `rfessentials` figure) and not the bulk-eps_r
wavelength (which is what `pluto-cal-switch` used and mislabelled). The choice
of guided is `rf-design.md` 3(b)'s explicit instruction: *"Pick guided lambda_g
and say so."* This ADR is the saying.

<!-- bound: VIA_FENCE_PITCH -->
```yaml
id: VIA_FENCE_PITCH
claim: >-
  Maximum centre-to-centre spacing of the ground-via fence flanking any RF arm,
  so the fence acts as a continuous wall rather than a periodic structure with
  a passband: one twentieth of the GUIDED wavelength at the 6 GHz band edge on
  this board's own stackup.
relation: "<="
value: 1.3693
unit: mm
corner: nominal
command: >-
  /usr/bin/python3 -c "import math; w,h,er,t,f=0.36,0.2104,4.4,0.035,6.0;
  w+=(t/math.pi)*(1+math.log(2*h/t)); u=w/h;
  a=1+(1/49)*math.log((u**4+(u/52)**2)/(u**4+0.432))+(1/18.7)*math.log(1+(u/18.1)**3);
  b=0.564*((er-0.9)/(er+3))**0.053;
  ee=(er+1)/2+(er-1)/2*(1+10/u)**(-a*b);
  print(round(299.792458/(f*math.sqrt(ee))/20,4))"
governs:
  evaluate: >-
    /usr/bin/python3 -c "print(round(27.387/{value}, 4))"
  budget: ">= 20"
  unit: divisions of lambda_g
  # Prints a BARE NUMBER, and that is not cosmetic: adr_bound_provenance
  # requires the last stdout line to carry exactly one number, and a first
  # version of this line printed a human sentence with three numbers in it
  # ("fence pitch 1.3693 mm is lambda_g/20.0"). The bound regenerated
  # perfectly and the GOVERNS check was unevaluable — which the gate reports
  # as UNVERIFIED, not as a pass.
  # What it asks: at the published pitch, how many divisions of the guided
  # wavelength is the fence? Must be >= 20. At 1.3693 it is exactly 20.0; at
  # the declared standard value 1.35 it is 20.29, i.e. tighter than required.
standard_value:
  explicit: [1.35, 1.30, 1.25]
  series_why: >-
    A via fence pitch is not an E-series part value — it is a placement grid the
    stitch pass emits, so the admissible set is the round numbers a human will
    actually type into route.yaml. 1.35 mm is the largest of these under the
    bound and is what v2 will declare; 1.30 and 1.25 are listed because the
    stitch grid may be forced to a coarser board-wide pitch and the next value
    down must be known in advance rather than improvised at stage 6.
```

## Consequences

- **Committed to:** every v2 document quotes 3.3286 / 6.0857 / 27.387 / 13.145,
  and the fence pitch is declared as **1.35 mm** (the largest round value under
  the derived 1.3693 bound), not the inherited 1.37. The difference is
  cosmetically small and the point is not the 0.0193 mm — it is that the number
  now has a command behind it.
- **v2 and v1 will publish slightly different phase-per-mm figures for the same
  laminate.** That is a real, visible inconsistency between two boards a reader
  will compare, and it is deliberate: the alternative was to make v2 agree with
  a number neither of us can regenerate. Recorded here so the reader who spots
  it finds the answer instead of assuming one of us made an arithmetic slip.
- **What breaks if reversed:** nothing physically — the three candidate values
  span 0.7 % and the fence is conservative at all of them. What is lost is the
  provenance, which is the whole point of the ADR.
- **OWED, and it is a real debt, not a formality:** nobody has shown what
  measurement 3.350 came from. If it has one — a TDR run, a vendor impedance
  coupon, a field solve — then it OUTRANKS my closed-form derivation (canon M6:
  the manufacturer's own measurement wins over your derivation) and this ADR
  should be superseded rather than quietly kept. **A proposed patch to
  `rf-design.md` 4(d) is reported to the caller; `skills/` was not edited** (a
  sibling agent is live in that tree).
- Re-verified at stage 5, not assumed: the fence pitch is a PLACEMENT/STITCH
  parameter and v2 has not reached that stage. This ADR fixes the constant; the
  `route.yaml` value is written when the board is placed.
