---
id: 0004
date: 2026-07-30
status: accepted
tags: [rf, provenance, fence]
---
# 0004 — the arms are COPLANAR, so the fence shorts a different mode, and the bound gets tighter

## Context

ADR-0003 derived this board's whole RF constant set — `eps_eff`, `t_pd`,
`lambda_g`, the phase-per-mm, and the via-fence pitch that descends from them —
for a **bare microstrip**: a 0.36 mm F.Cu strip over a solid In1.Cu reference,
with nothing lateral. It did that carefully, with a regenerable command, and it
was right to reject the fleet's three inherited values in favour of one it could
re-derive. **The derivation is sound and the cross-section is wrong.**

Measured 2026-07-30 off `04_kicad/pluto_rx2_8way_v2.kicad_pcb` through pcbnew
(`03_src/line_type.py` -> `line_type.txt`; it rebuilds each RF net's
centreline from its OWN track segments, samples every 0.05 mm, and marches a
perpendicular ray at 0.0005 mm into the F.Cu GND zone FILL, so every number is a
distance to realized copper and no rule file is read):

| what | measured |
|---|---|
| trace width, every RF segment | **0.360 mm** |
| GND pour gap, edge-to-edge, BOTH sides | **0.2005–0.2010 mm** (median 0.2010 over 6007 side-samples, min 0.2005) |
| `g/h` | **0.955** |
| `g/w` | **0.558** |
| both sides within 0.25 mm, per arm | ANT5 66.9 %, RX1_MAIN 61.3 %, ANT4 76.7 %, ANT1 77.2 %, ANT6 78.4 %, RX2_OUT 78.4 %, ANT2 84.5 %, ANT3 85.2 %, ANT7 87.7 %, RX1_TAP 93.2 % — **mean 75.2 %** |
| In1.Cu beneath each arm | **continuous**, with exactly ONE void per arm |

The pour did not merely come near the line — it ran to the 0.200 mm DRC
clearance and stopped, on both sides, for three quarters of every arm. At
`g ~= h` the coplanar ground carries a real share of the return current. **These
arms are a conductor-backed (grounded) coplanar waveguide.**

And the residue is not microstrip either. The 8–29 % of each arm that is NOT
two-sided-coplanar is a single interval 1.40–1.75 mm long at the SMA end, and it
coincides *exactly* with the In1.Cu void (ANT1 s = 0.00–1.75, ANT2 0.00–1.67,
ANT4 12.62–14.32, ANT7 12.40–13.80, …). That interval is the LAUNCH — the
>= 3.5 mm bottom-plane antipad, where there is neither a coplanar ground nor a
reference plane. **There is no bare-microstrip section anywhere on this board.**
ADR-0003's constant set describes a cross-section this board does not contain.

`03_src/rules/nets.yaml` states the opposite in writing, under
`scoped_clearances/rf_launch`: *"a coplanar ground would pull Z0 down if it ran
alongside the line — it does not."* It does, for essentially the whole line.
That sentence is deleted by this ADR.

## Options

- **Keep ADR-0003's microstrip set and pull the pour back to >= 0.46 mm** (the
  gap at which the CBCPW model reproduces `eps_eff 3.3286`). REJECTED as the
  primary route, though it is a legitimate engineering answer: it is a
  board-wide zone-clearance change that re-opens routing on a board already at
  DRC 0/0/0, it throws away the coplanar ground's real benefit (tighter lateral
  confinement, better inter-arm isolation), and it makes the *documents* right
  by moving the *copper*, which is the more expensive direction. Recorded
  because it is the alternative a reviewer will ask about.
- **Publish the microstrip set with a note that the realized line is coplanar.**
  REJECTED. The board's headline artifact is a phase table in degrees per
  millimetre; a 2.6 % error in `t_pd` is a published error, not a caveat.
- **Re-derive the constant set for the MEASURED cross-section, and re-derive
  what the fence must DO for it.** CHOSEN.
- **Re-derive a LOOSER fence bound the board can hold.** REJECTED — and it is
  worth recording that this was not rejected on taste. It is *impossible*: the
  correct GCPW bound comes out TIGHTER (below). ARCHITECTURE sec 6 previously
  offered "an ADR-0003 amendment that re-derives the bound the board can
  actually hold" as one of three ways out. **That exit is closed by physics**,
  and this ADR closes it explicitly so no successor spends a session looking
  for it.

## Decision

### The constant set

**[DERIVED]**, identified by the canon tuple `(stackup, w, cross-section,
method)` that `rf-design.md` 4A's rule requires — never by the stackup alone:

    stackup        JLC04161H-7628, h = 0.2104 mm top prepreg, er = 4.4,
                   t = 0.035 mm (1 oz outer)      [DECLARED stackup fields]
    w              0.360 mm                       [MEASURED, every segment]
    cross-section  CONDUCTOR-BACKED COPLANAR WAVEGUIDE, s = 0.2005 mm both
                   sides, BARE (no solder-mask term)  [s MEASURED]
    method         quasi-static conformal mapping, Ghione / Naghed-Wolff
                   CBCPW form, ZERO conductor thickness

    a = w/2 = 0.18000        b = w/2 + s = 0.38050
    k1 = a/b                          = 0.473062    K/K'(k1) = 0.757743
    k3 = tanh(pi a/2h)/tanh(pi b/2h)  = 0.878560    K/K'(k3) = 1.312738
    q  = K'(k1)K(k3) / K(k1)K'(k3)    = 1.732432
    ->  eps_eff  = (1 + er q)/(1 + q) = 3.1557
        Z0       = 60pi/sqrt(ee)/(K/K'(k1) + K/K'(k3)) = 51.249 ohm
        t_pd     = 5.9255 ps/mm
        lambda_g = 28.1269 mm @ 6 GHz
        phase    = 12.7991 deg/mm @ 6 GHz

Against ADR-0003's microstrip set: `eps_eff` **3.3286 -> 3.1557 (−5.19 %)`,
`t_pd` 6.0857 -> 5.9255 (−2.63 %), `phase` 13.145 -> 12.799 deg/mm. On a
14.366 mm arm that is **−4.97 deg of absolute phase at 6 GHz**. `Z0` moves
50.29 -> 51.25 ohm (+1.9 %), so the *impedance* survives the correction and the
*phase constant* does not — which matters, because phase is what this board
sells.

Tagged **[DERIVED]**, not [MEASURED]. That distinction is canon
(`rf-design.md` sec 7, "READ THE THREE VOICES SEPARATELY") and it exists
because this exact fleet filed a computed `eps_eff 3.350` under a heading
reading *"What this fleet MEASURED"*.

Two treatments are NOT adopted and are recorded so nobody re-litigates them:

- **Finite conductor thickness.** The Gupta/Garg/Bahl/Bhartia CPW correction
  gives `delta = (1.25 t/pi)(1 + ln(4 pi w/t)) = 0.08163 mm`, i.e.
  `delta/s = 0.407`. That formula assumes `t << s`; at `t/s = 0.175` and a
  correction eating 41 % of the gap it is outside its own validity, and it
  returns `Z0 = 42.99 ohm`, which is not credible for a line whose bare value
  is 51.2. Printed as a sensitivity by `gcpw_constants.py`, not used.
- **Solder mask.** `rf-design.md` 4A(iii) measured, by 2D field solve on this
  exact laminate, that a 0.020 mm conformal mask adds **+6.3 %** to `eps_eff` —
  larger than the entire microstrip-vs-coplanar correction this ADR makes. It
  is not applied because the fleet does not declare mask-opened-or-not as a
  stackup field, and inventing the field here would put a fifth unverifiable
  constant set into circulation. **The cross-section above says BARE, and that
  word is the disclosure.** This is a real, stated, unclosed gap.

Independent corroboration: the r2 zero-context layout lens, working alone from
the same board with its own script, published `eps_eff 3.1552`. This ADR
derives 3.1557 — 0.016 % apart, from two agents who shared no code.

### What the fence must DO — and it is not what it was doing

A via fence beside a **microstrip** is a LATERAL SHIELD. `lambda_g/20` keeps it
acting as a continuous wall rather than a periodic structure with a passband;
that is what ADR-0003's `VIA_FENCE_PITCH` claim says in so many words.

**On a GCPW that job is already discharged, and not by the fence.** The
coplanar ground is solid copper at 0.2005 mm from the trace edge — an aperture
of ZERO, by construction, which no discrete via wall at any pitch improves on.
Lateral confinement is not the open question on this board.

The fence's remaining job is the VERTICAL one, and it is the one that actually
matters for this cross-section. A conductor-backed CPW has **two** grounds: the
F.Cu coplanar pour and the In1.Cu reference. Those two sheets form a
parallel-plate waveguide with **no cutoff frequency**. Any asymmetry — a bend,
the launch, a discontinuity, an unequal excitation of the two coplanar grounds —
puts a voltage between them and launches the parasitic parallel-plate /
slotline mode, which carries power out of the line and couples arm to arm. This
is the well-known and dominant leakage mechanism of conductor-backed CPW, and
it is the reason a GCPW is stitched at all. Ground vias SHORT the two sheets
together; a via wall is a short only where it is **electrically short against
that mode** — not against the mode travelling on the line.

### The bound

The parallel-plate mode fills the dielectric between two conducting sheets, so
its effective permittivity is the **bulk `er`**, not the line's `eps_eff`:

    lambda_0  = c/f          = 299.792458/6.0     = 49.9654 mm
    lambda_pp = lambda_0/sqrt(er) = 49.9654/sqrt(4.4) = 23.8201 mm
    BOUND: along-arm ground-stitch spacing <= lambda_pp/20 = 1.1910 mm

The divisor **20 is unchanged** — it is the fleet's inherited via-wall divisor
(`rf-design.md` sec 2, from rfessentials). What changes is the WAVELENGTH it is
applied to, which is precisely the correction `rf-design.md` 3(b) already made
once, when it moved microstrip from `lambda_0` to `lambda_g` and said *"what it
must sample is the wave ON THE LINE, not a wave in air."* Applied to a GCPW
stitch the same sentence reads: what it must sample is the wave IT SHORTS OUT.
Four candidates at 6 GHz:

| candidate | value | why it is not the bound |
|---|---|---|
| microstrip guided `lambda_g/20` (ADR-0003) | 1.3693 mm | the wrong cross-section |
| CBCPW guided `lambda_g/20` (this line's own mode) | 1.4063 mm | the line's mode is confined by the pour, not by the fence |
| **parallel-plate `lambda_pp/20`** | **1.1910 mm** | **BINDING** |
| free space `lambda_0/20` (rfessentials as written) | 2.4983 mm | not in the substrate |

**THE BOUND GOES DOWN: 1.3693 -> 1.1910 mm, 13 % TIGHTER.** Stated plainly,
because the honest direction is the whole value of this ADR: correcting the
line type does **not** relieve this board. It makes the requirement harder, and
it does so across the entire declared Dk window (er 4.2 -> 1.2190 mm,
er 4.6 -> 1.1648 mm), so no corner of the laminate spec recovers the old
number.

**The derivation order is on the record** (`01_docs/journal/05_verify.md`,
entries 23:20 and 23:35): the line type was measured, then the constants were
derived, then the bound was fixed and written into the journal, and only then
was `fence_pitch.py` re-run against it. Nothing here was adjusted after seeing
an aperture. The check on that claim is the direction of the result — a bound
tightened by 13 % against a board already failing the looser one is not where
motivated reasoning lands.

<!-- bound: GCPW_GROUND_STITCH_PITCH -->
```yaml
id: GCPW_GROUND_STITCH_PITCH
claim: >-
  Maximum along-arm centre-to-centre spacing of the ground vias stitching the
  F.Cu coplanar ground to the In1.Cu reference alongside any RF arm, so the
  via wall is an electrical short against the parasitic parallel-plate mode
  between those two sheets rather than a periodic structure that lets it
  propagate: one twentieth of the parallel-plate wavelength at the 6 GHz band
  edge, which travels at the BULK permittivity of the laminate because the
  mode fills the dielectric between two conducting planes.
relation: "<="
value: 1.1910
unit: mm
corner: nominal
command: >-
  /usr/bin/python3 -c "import math; er,f=4.4,6.0;
  print(round(299.792458/(f*math.sqrt(er))/20,4))"
governs:
  evaluate: >-
    /usr/bin/python3 -c "print(round(23.8201/{value}, 4))"
  budget: ">= 20"
  unit: divisions of lambda_pp
  # What it asks: at the published spacing, how many divisions of the
  # PARALLEL-PLATE wavelength is the stitch? Must be >= 20. At 1.1910 it is
  # exactly 20.0; at the declared standard value 1.15 it is 20.71, i.e.
  # tighter than required.
  # Prints a BARE NUMBER on the last stdout line -- adr_bound_provenance
  # requires exactly one number there, and ADR-0003 already paid for the
  # lesson that a human sentence with three numbers in it regenerates
  # perfectly and grades as UNVERIFIED.
standard_value:
  explicit: [1.15, 1.10, 1.05]
  series_why: >-
    A stitch spacing is not an E-series part value -- it is a placement grid
    the stitch pass emits, so the admissible set is the round numbers a human
    will type into route.yaml. 1.15 mm is the largest of these under the
    bound. The value that must actually be DECLARED is the square-lattice
    pitch, which is a different number: on a 45-degree arm one lattice row
    projects at p*sqrt(2), so p <= 1.1910/sqrt(2) = 0.8422 and the lattice
    pitch is 0.80 mm (down from the 0.95 mm this board carries).
```

## Consequences

- **`eps_eff 3.1557 / t_pd 5.9255 / lambda_g 28.1269 / 12.7991 deg-per-mm` is
  now this board's ONE constant set**, and `ARCHITECTURE.md` sec 5 and every
  downstream document quote it with the tuple attached. ADR-0003's numbers are
  superseded, not deleted: they remain the correct answer to a question about a
  bare microstrip, which this board does not have.
- **`03_src/rules/nets.yaml`'s "it does not" sentence is falsified and removed.**
  A rule file that asserts a cross-section is asserting something the board can
  contradict, and this one did.
- **The fence bound is 1.1910 mm and the board does not meet it.** MEASURED with
  `fence_pitch.py` (which reads the saved `.kicad_pcb` through pcbnew and never
  reads `route.yaml`, so a declared pitch cannot certify itself): worst interior
  along-arm aperture **3.0500 mm at ANT4 sideW, s = 7.12..10.17** — `lambda_pp/7.81`,
  **2.56x the bound** — with **17 of 20 arm-sides over** (it was 11 of 20 at the
  superseded 1.35 mm). This is an OPEN P0 and this ADR does not close it; see
  ARCHITECTURE sec 6 for the classified apertures and what each class needs.
- **The declared lattice pitch must fall 0.95 -> 0.80 mm** when this board is
  re-stitched. 0.95*sqrt(2) = 1.3435 mm is the projection a 45-degree arm sees,
  and 12 of the 34 over-bound apertures are exactly that number with no
  occupier at all — pure lattice, no obstruction. 0.80*sqrt(2) = 1.1314 mm
  clears the bound. This is expressible only because the shared stitcher's
  whole-millimetre grid floor was fixed on 2026-07-30 (`rf-design.md` 3(b));
  before that fix neither 0.95 nor 0.80 could have been declared.
- **What breaks if reversed:** the board would be graded against a bound 13 %
  looser than its physics, and would publish a phase constant 2.6 % off the
  copper it describes. Nothing becomes unsafe — every candidate constant in
  play sits inside the laminate's own Dk window — but the published property
  set would describe a line that is not on the board, which is the same defect
  ADR-0003 was written to fix, one cross-section further down.
- **OWED, and named rather than closed:** the solder-mask term. `rf-design.md`
  4A(iii) measures it at **+6.3 % on eps_eff**, which is larger than this ADR's
  entire correction. Until the fleet declares mask-opened-or-not as a stackup
  field, every constant set here — ADR-0003's and this one's — is a bare-trace
  model of a board that ships with mask. The word BARE in the tuple is the
  disclosure, and it is not a substitute for the field.
