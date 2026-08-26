# DETAIL_DESIGN — pluto-cal-switch

Every component value, derived, with its equation and its margin. A value in
the schematic with no line here is UNJUSTIFIED.

Conventions: **[DS]** = read from a manufacturer datasheet with the citation
given. **[DERIVED]** = computed here from [DS] inputs. **[EST]** = an estimate
with no datasheet behind it — every one is named, and §3.6 states which of
them the conclusion is sensitive to.

---

## 1. The stackup constants everything else rests on

JLCPCB `JLC04161H-7628`, 4-layer 1.6 mm. L1→L2 prepreg **0.2104 mm**,
**Dk 4.4** (JLC published, and used throughout — see the amendment note),
tan δ 0.02, 1 oz Cu (t = 0.035 mm).

| quantity | value | source |
|---|---|---|
| 50 Ω microstrip width, L1 over L2 | **0.36 mm** | [DERIVED] 2D finite-difference field solve on the AS-FABBED cross-section (trapezoidal etch + 0.020 mm solder mask), bracketed by Hammerstad-Jensen on the bare trace — see `03_src/rules/nets.yaml` "WIDTH DERIVATION" |
| Z₀ at 0.36 mm | **49.93 Ω** as fabbed / 51.03 Ω bare | [MEASURED, field solve] RL 62.5 dB / 39.8 dB |
| 90 Ω differential pair (USB) | **0.33 mm / 0.25 mm gap** ⇒ ~89 Ω | [DERIVED] `Zdiff ≈ 2·Z0·(1 − 0.48·e^(−0.96·s/h))` |
| ε_eff | **3.383** | [DERIVED] field solve, as fabbed |
| propagation delay | **6.135 ps/mm** | [DERIVED] `tpd = √ε_eff / c` |
| λg at 6 GHz | **27.17 mm** | [DERIVED] (13.25 °/mm) |
| λg/20 at 6 GHz (lumped-element ceiling) | **1.36 mm** | [DERIVED] |
| λg/12 at 6 GHz (via-fence pitch) | **2.26 mm** → use **≤2.0 mm** | [DERIVED] |

> **AMENDED 2026-07-30.** This section previously read "Dk 4.4 (JLC
> published), **ε_r taken as 4.3**" and published 0.35 mm / ε_eff 3.26 /
> 6.0 ps/mm. Three things were wrong and they compounded:
> 1. **The permittivity dispute was decided against the fab's own number.**
>    ADR-0010's stackup table says 4.4; this said 4.3. It is now **4.4
>    everywhere**. The dispute never rescued 0.35 mm anyway — at 4.3 the line
>    is *further* from 50 Ω, not closer.
> 2. **The width was one method run twice.** Both prior derivations were
>    Hammerstad closed-form (canon M1: the checker and the checked shared a
>    method). An independent field solve disagrees by 3.4 % on the same bare
>    cross-section, and the solder mask — carried by neither closed form — is
>    worth −1.55 Ω, more than the whole correction.
> 3. **The row above already contradicted itself**: it called 0.35 mm the 50 Ω
>    width and then tabulated "0.35 → 51.0 Ω" in its own source column.
>
> The widths are now closed-form **and** field-solve. **They must still be
> re-confirmed against JLCPCB's own impedance calculator for the exact stackup
> ordered, before release.** Recorded as a CHECKLIST item.

### 1.1 Microstrip loss — the term the sourcing spike got wrong by 2.7×

Conductor loss (∝√f) plus dielectric loss (∝f), for w = 0.36 mm:

```
α_d = 27.3 · [εr(ε_eff−1)] / [√ε_eff·(εr−1)] · tanδ / λ0
    = 27.3 · (4.4×2.383)/(1.8393×3.4) · 0.02/λ0 = 0.9154/λ0   dB/m
    @6 GHz (λ0 = 49.97 mm):  18.3 dB/m = 0.183 dB/cm

Rs  = √(π·f·µ0/σ),  σ_Cu = 5.8e7 S/m
    @6 GHz: Rs = 0.02021 Ω/sq
α_c = K · 8.686·Rs/(Z0·w),  K = 1.6 (edge current crowding, narrow line)
    @6 GHz: 1.6 × 8.686×0.02021/(50×0.00036) = 15.6 dB/m = 0.156 dB/cm
```

> **Recomputed 2026-07-30 at Dk 4.4 / ε_eff 3.383 / w 0.36 mm** (was 4.3 /
> 3.26 / 0.35 mm). The two terms move in OPPOSITE directions and very nearly
> cancel: dielectric loss rises 17.8 → 18.3 dB/m, conductor loss falls
> 16.1 → 15.6 dB/m on the wider line. **Total 33.9 dB/m before, 33.9 dB/m
> after** — unchanged to three figures. The published **0.036 dB/mm @6 GHz**
> therefore stands, and with it the 1.91 dB loopback figure, the 3.09 dB chain
> tilt, and the attenuator values ADR-0004/ADR-0016 derived from that tilt.
> **Nothing downstream of the loss constant moves.** Stated explicitly because
> a permittivity change that silently re-opened the attenuator decision would
> be exactly the kind of unnoticed cascade ADR-0011 §2 warns about.

| | 70 MHz | 6 GHz |
|---|---|---|
| this derivation | 0.0019 dB/mm | **0.0339 dB/mm** |
| independent Hammerstad estimate (sourcing spike, SMA function) | — | 0.036 dB/mm |
| **budgeted (the conservative of the two)** | **0.0019** | **0.036 dB/mm** |

**The sourcing spike budgeted 0.013 dB/mm** — the figure for a WIDE (≈3 mm)
line on a 1.6 mm substrate. But 1.6 mm two-layer is refuted for this board
(ARCHITECTURE §7: a 3 mm trace does not fit a 2 mm splitter triangle and
overlaps the SMA ground pads at NEGATIVE clearance), and the 0.2104 mm
prepreg that makes every pad on the board land correctly costs 2.7× the loss
per millimetre. That single correction **doubles the chain tilt**, from the
spike's 1.64 dB to 3.09 dB, and it moves the pad value.

---

## 2. Routed lengths assumed by the budget

The board is not placed yet, so these are the design TARGETS the floorplan
must meet. Every one is an [EST] until the board exists; §3.6 sizes their
influence.

| segment | length | why |
|---|---|---|
| `TX_PLUTO` SMA → PAD_A1 in | 10 mm | the port is now placed where the RF wants it, not at a foreign pitch (ADR-0015) |
| **PAD_A1 internal cascade** | **12 mm** | **NEW: 4 × 3 mm between the five chips of the 25.8 dB pre-split pad (ADR-0016). Five chips in series is not free and it is budgeted, not waved away** |
| PAD_A1 out → splitter vertex | 22 mm | the splitter is on the mirror axis between the two RX ports; TX enters from the side |
| splitter arm → PAD_A2 in | 8 mm | ×2, mirrored |
| PAD_A2 out → switch RF2 | 8 mm | ×2, mirrored |
| switch RFin → `RX_PLUTOn` SMA | 5 mm | switch hugs its port |
| **total, TX jack → each RX jack** | **65 mm** | |
| switch RF1 → `RX_ANTn` SMA | 20 mm | ×2, antenna edge |

**65 mm × 6.135 ps/mm = 399 ps** nominal one-way loopback delay per arm, ON
THE BOARD (was 390 ps at the superseded 6.0 ps/mm — §1). The D4 artifact is
the measured per-arm length and the arm-to-arm DELTA, converted with the
6.135 ps/mm constant pinned to the ordered stackup.

**A8 added a SECOND, LARGER delay term the board cannot measure: the cables.**
0.3 m of RG316-class coax is ~1.5 ns each, four times the whole on-board run,
and the arm-to-arm delta is now dominated by how well the two RX cables match
rather than by how well the two microstrips do. That does not weaken D4 — it
relocates it. **The release publishes the board's delta and states its
measurement plane (this board's SMA jacks); the cable pair is the user's to
match or to measure.** A matched pair of cables is a purchasable object, which
is a better place for the requirement than a routing negotiation.

---

## 3. The loss budget — TX_PLUTO to EACH RX_PLUTO, control ON

**Measurement plane, stated with the number (ADR-0013's surviving rule):** the
budget below runs from the **Pluto's own SMA jacks**, so the two user-supplied
cables are inside it. **The release publishes its measured curve at THIS
BOARD's SMA jacks** — a different plane, ~0.4 dB apart at 70 MHz and ~3.0 dB
apart at 6 GHz, and the difference is the user's cables, which this project
neither supplies nor measures.

### 3.1 Every term

| # | element | 70 MHz | 6 GHz | source |
|---|---|---|---|---|
| 1 | Pluto jack ↔ cable plug, TX side | 0.02 | 0.08 | [EST] — see §10 |
| 2 | **SMA cable, TX side** (0.3 m RG316-class, **USER-SUPPLIED**) | **0.20** | **1.50** | **[EST, ×2 bar]** — see §10 N1 |
| 3 | cable plug ↔ board jack + THT launch, TX | 0.05 | 0.25 | [EST] |
| 4 | µstrip 10 mm | 0.019 | 0.36 | [DERIVED] §1.1 |
| 5 | **PAD_A1** | *A1* | *A1* | [DS] §4 |
| 5b | **PAD_A1 internal cascade, 4 × 3 mm** | **0.023** | **0.43** | [DERIVED] — five chips in series (§4.2) |
| 6 | µstrip 22 mm | 0.042 | 0.79 | [DERIVED] |
| 7 | resistive delta 2-way split | **6.021** | **6.021** | [DERIVED] EXACT, §5.1 |
| 8 | splitter mounting-parasitic excess | 0.00 | 0.35 | [EST] modelled; the measured reference (Mini-Circuits ZFRSC-183-S+ REV D p.1, a DC–18 GHz coax resistive divider) runs 6.05 dB @500 MHz → 6.36 dB @6 GHz, i.e. +0.31 dB |
| 9 | µstrip 8 mm | 0.015 | 0.29 | [DERIVED] |
| 10 | **PAD_A2** | *A2* | *A2* | [DS] §4 |
| 11 | µstrip 8 mm | 0.015 | 0.29 | [DERIVED] |
| 12 | SPDT insertion loss | 0.20 | 0.65 | [DS] §3.2 |
| 13 | µstrip 5 mm | 0.010 | 0.18 | [DERIVED] |
| 14 | board jack + THT launch ↔ cable plug, RX | 0.05 | 0.25 | [EST] |
| 15 | **SMA cable, RX side** | **0.20** | **1.50** | **[EST, ×2 bar]** |
| 16 | cable plug ↔ Pluto jack, RX | 0.02 | 0.08 | [EST] |
| | **NON-PAD SUBTOTAL** | **6.89** | **13.02** | |

**Chain tilt = 6.13 dB**, up from 3.09 dB. It is irreducible, and **the two
cables are now the single largest non-pad term at the top of the band**:

| contributor | 70 MHz | 6 GHz | Δ |
|---|---|---|---|
| the two SMA cables (A8) | 0.40 | **3.00** | **+2.60** |
| microstrip, 65 mm | 0.13 | 2.34 | +2.21 |
| SPDT | 0.20 | 0.65 | +0.45 |
| four coax interfaces | 0.14 | 0.66 | +0.52 |
| splitter parasitics | 0.00 | 0.35 | +0.35 |
| resistive split (flat by construction) | 6.02 | 6.02 | 0 |

**A8 nearly doubled the tilt, and A9's specification absorbed it without
changing.** That is the strongest practical argument for a minimum over a
scalar: a minimax pad referenced to ≈3.0 GHz would have had to move.

### 3.2 The switch term, stated honestly

The switch IL is the one datasheet term with a measurement-method problem.

- **BGS12WN6** (the primary, ADR-0002) Table 4, PDF p6 / printed p4: typ
  **0.15 dB** @50–698 MHz, **0.62 dB** @5925–7125 MHz (max 0.25 / 1.00 over
  the full temperature and supply range). But footnote 1 to that table reads
  verbatim *"Measured on prober station to exclude board effects, without any
  matching components."* **These are die-level numbers.**
- **BGS12P2L6** (the pin-identical alternate) Table 5, PDF p6 / printed p5:
  typ **0.20 dB** @617–960 MHz, **0.51 dB** @5150–5925 MHz, footnote
  *"Measured on Application board"*. Its table has **no row containing
  70 MHz and no row containing 6.000 GHz** — both ends of this board's band
  are uncharacterized on that part.

Budgeted: **0.20 dB @70 MHz** (WN6 die-level typ 0.15 + a 0.05 board
allowance, which lands exactly on P2L6's application-board 0.20) and
**0.65 dB @6 GHz** (WN6 die-level typ 0.62 + 0.03). The board allowance is
small because the launch and trace contributions are already carried
separately in rows 4/11/13 — a small deliberate double-count in the
conservative direction.

Worst case over temperature and supply: **0.25 / 1.00 dB** [DS].

### 3.3 The loss curve

| f | µstrip 65 mm | switch | coax IFs | **cables** | splitter par. | split | **L(f)** |
|---|---|---|---|---|---|---|---|
| 70 MHz | 0.13 | 0.20 | 0.14 | **0.40** | 0.00 | 6.02 | **6.89** |
| 648 MHz¹ | 0.50 | 0.20 | 0.17 | **1.10** | 0.04 | 6.02 | **8.03** |
| 2 GHz | 1.05 | 0.24 | 0.25 | **1.82** | 0.12 | 6.02 | **9.50** |
| 3 GHz | 1.40 | 0.32 | 0.31 | **2.19** | 0.18 | 6.02 | **10.42** |
| 4.5 GHz | 1.89 | 0.43 | 0.42 | **2.63** | 0.26 | 6.02 | **11.65** |
| 6 GHz | 2.34 | 0.65 | 0.66 | **3.00** | 0.35 | 6.02 | **13.02** |

¹ 648 MHz = √(70 × 6000), the geometric mean of the band. Cable loss is
interpolated as `0.40·(f/70 MHz)^0.4527`, the exponent fitted to the two
endpoint [EST]s — a blend of the √f conductor term and the f dielectric term,
which is the right SHAPE for coax even when the endpoints are estimates.

### 3.4 Choosing the pad — sizing a MINIMUM is a different problem

**A9 replaced the scalar with a floor** (ADR-0016). Sizing a floor inverts the
method: instead of centring a pad on a target, you take the **LOWER BOUND of
every loss term** and require the sum to clear 40 dB. Anything the real board
does better than that bound only pushes the total UP, which is the safe
direction.

Taken to its logical end, the design credits **nothing it does not control**:

| term | credited | why |
|---|---|---|
| pad | **datasheet MIN column** | the only thing the vendor guarantees |
| resistive split | **5.97 dB** | 6.017 exact (§5.1) less 0.043 for ±1 % parts |
| both SMA cables | **0** | user-supplied, unknown length, not on this BOM |
| four coax interfaces | **0** | [EST], strictly positive |
| 65 mm of microstrip | **0** | [DERIVED], strictly positive |
| SPDT insertion loss | **0** | [DS], strictly positive |
| splitter parasitics | **0** | [EST], strictly positive |

```
required pad MIN  =  40 − 5.97  =  34.03 dB      (guaranteed, at the worst frequency)
```

Realizable from the two Mini-Circuits YAT values with VERIFIED stock:

**`A1 = 2 × YAT-10A+ + 3 × YAT-2A+` pre-split; `A2 = YAT-10A+ + YAT-2A+` per
arm** ⇒ the TX→RX path crosses **3 × YAT-10A+ + 4 × YAT-2A+**.

Datasheet min/typ/max columns [DS], YAT-10A+ p.2 and YAT-2A+ p.2:

| | DC–5 GHz | 5–15 GHz |
|---|---|---|
| YAT-10A+ | 9.6 / 9.97 / 10.4 | 9.5 / 9.98 / 10.5 |
| YAT-2A+ | 1.5 / 1.92 / 2.3 | 1.4 / 1.85 / 2.3 |
| **path total (3×10 + 4×2)** | **34.8** / 37.6 / 40.4 | **34.1** / 37.3 / 40.7 |

```
guaranteed minimum, 70 MHz – 5 GHz :  34.8 + 5.97  =  40.77 dB
guaranteed minimum, 5 – 6 GHz      :  34.1 + 5.97  =  40.07 dB   <-- BINDS
```

**≥ 40.07 dB across 70 MHz – 6 GHz, worst frequency 6 GHz.** The step at 5 GHz
is the YAT min column changing band, not anything physical. Credit only the
terms the geometry FORCES (≥25 mm of trace = 0.9 dB at 6 GHz, SPDT IL ≥0.2 dB)
and it is ≥41.2 dB.

**Why not one chip less.** The next build down, `3 × YAT-10A+ + 3 × YAT-2A+`,
has a 5–15 GHz min of 32.7 dB ⇒ **38.67 dB — it FAILS.** The last YAT-2A+ is
what buys the guarantee, and it costs $3.40.

**Why not an all-YAT-10A+ build.** `4 × YAT-10A+` in the path clears the floor
easily (45.4 dB) but lands the TYPICAL at 48.7 dB at 70 MHz — 8.7 dB above
spec — and the fourth 10 dB chip would have to come out of A2, dropping
inter-channel isolation from 29.9 dB to 26.0 dB and the open-cable masking
from 24 dB to 20 dB. **The chosen build is the one that clears 40 dB
guaranteed while sitting CLOSEST to it typically, without touching A2.**

### 3.5 The published curve, and the envelope around it

The MEASURED typical-performance tables (YAT-10A+ REV B p.4, YAT-2A+ REV B
p.4, read from the PDFs vendored in `02_parts/`) give the pad's own curve:
**37.70 dB at 70 MHz falling to 37.14 dB at 6 GHz — the pad contributes only
0.56 dB of the chain's 6.13 dB tilt**, and it tilts the other way.

| f | L(f) | + pad (measured typ) | **total, typical** |
|---|---|---|---|
| 70 MHz | 6.89 | 37.70 | **44.59 dB ← the typical minimum** |
| 648 MHz | 8.03 | 37.61 | 45.64 dB |
| 2 GHz | 9.50 | 37.43 | 46.93 dB |
| 3 GHz | 10.42 | 37.34 | 47.76 dB |
| 4.5 GHz | 11.65 | 37.20 | 48.85 dB |
| 6 GHz | 13.02 | 37.14 | **50.16 dB** |

**Guaranteed envelope, across band AND unit-to-unit: 40.1 dB to 53.7 dB**
(floor from §3.4; ceiling = 40.7 dB max pad + 13.02 dB typical chain at
6 GHz). It is a wide envelope and it is honest: **the release publishes the
measured curve of the unit it ships**, exactly as ADR-0013 required and as D4
requires of the length delta. A calibration board's product is a KNOWN number,
and a number known to be a curve ships as a curve.

**Note which frequency binds in which sense — it is not a contradiction.** The
TYPICAL minimum is at **70 MHz**, where the chain loses least. The GUARANTEED
floor dips at **6 GHz**, where the YAT min column steps down. Both are ≥40 dB,
and the specification is met in both readings.

**The typical sits 4.6 dB above the floor at 70 MHz, and that is a CHOICE, not
slack.** A build centred so that the TYPICAL is 40 dB would have a guaranteed
minimum near 36 dB — i.e. the spec would be met by an average unit and missed
by a bad one. For a pad whose whole job is surviving a misconfiguration, the
worst-case reading is the only one that means anything (ADR-0016).

### 3.6 Sensitivity — and why it no longer threatens the specification

| [EST] term | value @6 GHz | if it were HALF | if it were DOUBLE |
|---|---|---|---|
| the two cables | 3.00 dB | typical → 48.7 dB | typical → 53.2 dB |
| microstrip loss (0.036 dB/mm) | 2.34 dB | typical → 49.0 dB | typical → 52.5 dB |
| coax interfaces (rows 1,3,14,16) | 0.66 dB | typical → 49.8 dB | typical → 50.8 dB |
| splitter parasitic excess | 0.35 dB | typical → 50.0 dB | typical → 50.5 dB |

**Every cell is still far above 40 dB, and none of them can move the GUARANTEE
at all**, because the guarantee credits all four at zero. Compare the old
22 dB minimax build, where this same table decided which YAT part went in the
arm: an estimate wrong by 2× moved the BOM. **That coupling is gone.** The
estimates now only sharpen the published typical curve.

**TRIGGER TO RE-DERIVE (deliberately weakened):** once the board is routed,
replace rows 4/5b/6/9/11/13 with the actual lengths and re-run §3.3/§3.5. That
is now a documentation refresh, not a design risk — **no measured interconnect
value can invalidate the ≥40 dB minimum, because there is nothing below zero.**

---

## 4. The attenuator — why chips, why split, why these values

### 4.1 Chip over discrete: decided on FLATNESS, not on spread

A calibration reference sells a KNOWN number across a swept band.

| option | tilt, 70 MHz → 6 GHz | 6 GHz spread over plausible parasitics | cost |
|---|---|---|---|
| YAT cascade | **0.56 dB over 37.7 dB** [DS] measured typical-performance tables, YAT-10A+ REV B p.4 + YAT-2A+ REV B p.4 (vendored) | 34.1–40.7 dB (a datasheet-**GUARANTEED** window, and the reason the ≥40 dB minimum can be CLAIMED at all) | ~$30.6/board |
| cascaded 11.5 dB 0402 pi ×3 | ~1.7 dB [EST] modelled | an **UNKNOWN** — depends on ground-via inductance the fab does not guarantee | ~$0.09/board |
| single high-value 0402 pi | **collapses** [EST] | 18.1–22.0 dB at a 23 dB nominal | ~$0.03/board |

**A9 sharpened this comparison rather than changing its verdict.** Under a
guaranteed-MINIMUM specification the discrete option is not merely worse — it
is **inadmissible**, because it has no min column. You cannot promise ≥40 dB
with a part whose spread is modelled. The chip's guaranteed window IS the
deliverable now, not just a nicety; it was the weaker half of the argument
under the 30 dB scalar and it is the whole argument under the 40 dB floor.

The single pi collapses for a reason worth writing down: a 23 dB pi needs a
348 Ω series element, and an 0402's own end-to-end parasitic capacitance
(~0.05 pF) is ~530 Ω at 6 GHz — **the resistor is half-shorted by its own
package.** This is why discrete pads above ~15 dB stop working at multi-GHz,
and it is why the arm pads are built as 10 + 2 rather than as one 12.

Note the honest comparison, which A9 partly overturns: **the chip's GUARANTEED
window is WIDER than the discrete's MODELLED spread.** Under the 30 dB scalar
the chip therefore did not win on spread — it won on flatness. **Under a
guaranteed MINIMUM the comparison is no longer symmetric**: a modelled spread
cannot support a promise, so the chip wins on the axis that now matters most,
and the fallback below is demoted from "equivalent with a flatness penalty" to
"a different specification".

Discrete remains fully specified as the zero-stock-risk fallback: each 11.5 dB
pi is 3× 86.6 Ω 0402 1% (E96 rounds shunt/series/shunt 86.25/87.31/86.25 to
one value); stock verified C158969 (5202), C227253 (4450), C830266 (1038).
**Taking it would mean re-stating the specification as typical-with-a-modelled-
spread, and saying so to the user.**

### 4.2 Split 25.8 dB pre / 11.9 dB per arm — four independent reasons

The obvious build is one big pad before the split. It is wrong — and note
which half of that sentence A9 touched: **the whole 18 dB increase DID go
pre-split** (one part protects both arms, and a pre-split pad is upstream of
every downstream fault), while `A2` stayed at 11.9 dB because the four reasons
below pin it independently of the total.

**(a) Inter-channel isolation.** A resistive split gives 6.02 dB port-to-port
and that is a theorem (§5.3), not a part limitation. Attenuation placed AFTER
the split counts TWICE, because a wave reflected off one RX port traverses
that arm's pad twice while the wanted signal traverses it once:

```
isolation(RX1↔RX2) = 6.02 + 2·A2
    A2 = 0     →   6.02 dB
    A2 = 11.9  →  29.9 dB     ← chosen, and UNCHANGED by A9
```

**This is why the increase went pre-split.** Isolation is set by `A2` alone,
so raising the total through `A1` leaves it exactly where three arguments had
already put it.

At a realistic RX return loss of 10 dB, contamination of RX1 by RX2's
reflection is −16.0 dBc with no arm pad (**±1.4 dB and ±9.0° of ripple
versus frequency**) and −39.8 dBc with 12 dB arms (±0.09 dB, ±0.6°).

**(b) An unplugged RX cable corrupts the OTHER channel, silently.** With
port 3 open and port 2 terminated, KCL on the delta gives V3 = (V1+V2)/2 and
V1 + V3 = 3·V2, so V2 = 0.6·V1 and **Zin = 83.3 Ω**; the surviving RX
receives 0.375·Vs instead of 0.250·Vs = **+3.52 dB**, with no error
indication anywhere. With 12 dB arm pads the open is masked by 24 dB
(|Γ| = 0.063) and the error falls to **~0.2 dB**. On a bench adapter whose
only product is amplitude accuracy, a loose SMA must not produce a
confidently wrong answer.

**(c) In ANTENNA mode the splitter presents an OPEN to TX.** Both switches
are REFLECTIVE — *"The isolated port is a reflective short"* [DS, both
datasheets]. With both arms shorted and no arm pad, the delta's node
equations give I12 = I23 = −I13 ⇒ **Iin = 0 ⇒ Zin = ∞, Γ = +1**: a Pluto PA
driven in antenna mode sees full reflection. With 12 dB arm pads the arm
reflection reaching the splitter is |Γ| = 10^(−24/20) = **0.063**, and the
splitter stays matched. **The arm pads are what make it safe to transmit in
antenna mode at all.**

**(d) The contamination is NON-STATIONARY.** The AD936x RX input match moves
with the internal LNA/attenuator gain index, so the reflection at RX1/RX2
changes as the AGC moves. A term that moves with gain cannot be calibrated
out. This kills the "we'll calibrate the 6 dB isolation away" escape.

**The cost, stated:** two independent pad chains can differ. Worst case on
the datasheet windows is |A2a − A2b| ≤ **1.6 dB** (DC–5 GHz) / **1.9 dB**
(5–15 GHz); typical is far smaller and no unit-to-unit σ is published. That
imbalance is STATIC and MEASURABLE — which is exactly what brief D4 already
obliges the release to publish. A known imbalance is benign; unknown,
gain-dependent cross-coupling is not.

Mitigations that cost nothing: same reel / same lot for the two arms'
matching parts, and **identical rotation, not mirrored rotation** — mirrored
placement turns solder-fillet and pick-orientation asymmetry into phase
error (0.1 nH of mounting-inductance mismatch ≈ 3.8 Ω ≈ 2° at 6 GHz).

### 4.3 Power dissipation and the board's TX ceiling

At the **CITED** +8 dBm (6.31 mW) maximum PlutoPlus TX (`spf/`
`ad936x_tx_max_output_power`; AD9363 Rev. D p.4 of 32):

| element | power in | dissipation | rating [DS] | margin |
|---|---|---|---|---|
| PAD_A1, FIRST chip (YAT-10A+) | 6.3 mW | 5.7 mW | 1.7 W @25 °C | **24.8 dB** |
| splitter, hottest resistor | 0.02 mW | 0.005 mW | 62.5 mW @70 °C | **41 dB** |
| PAD_A2 (YAT-10A+) | 0.005 mW | 0.004 mW | 1.7 W | 56 dB |
| SPDT | 0.0004 mW | — | P_RF 26 dBm CW [DS WN6 Table 3] | 62 dB |

Everything downstream of PAD_A1 got 16 dB colder when A9 moved 18 dB into the
pre-split pad — the splitter's hottest resistor went from 27.4 dB of margin to
41 dB. **The first chip of PAD_A1 is now the only element that sees any real
power at all, and it always was.**

**Board TX absolute ceiling — UNCHANGED at +27 dBm.** The binding element is
still PAD_A1's first chip at **+32.3 dBm** (1.7 W); the SPDT's 26 dBm CW limit
is now unreachable by a further 37 dB of pad. Declared board ceiling:
**TX ≤ +27 dBm (0.5 W)**, a 5.3 dB guard band below PAD_A1's rating.

> **AND HERE IS THE RESULT THAT MATTERS MOST, WHICH THE 30 dB DESIGN DID NOT
> STATE.** The +27 dBm ceiling was derived to protect this BOARD's parts.
> Check it against the user's RECEIVER — the two ratings had never been put in
> one table:
>
> | pad | guaranteed min TX→RX | RX at TX = +27 dBm | margin to the +2.5 dBm rating |
> |---|---|---|---|
> | 30 dB build (ADR-0004/0013) | 27.2 dB | **−0.2 dBm** | **2.7 dB** |
> | **≥40 dB build (ADR-0016)** | **40.07 dB** | **−13.1 dBm** | **15.6 dB** |
>
> **The old board could be driven to its own declared ceiling and leave the
> user's AD936x 2.7 dB from destruction.** ≥40 dB is what makes the +27 dBm
> figure honest as a *system* ceiling rather than only a component one.
>
> Note also the discrete fallback pad is 13 dB LESS forgiving — its input
> shunt resistor reaches 62.5 mW at ~+18.7 dBm.

---

## 5. The splitter — values, realised performance, and a proof

### 5.1 Values and realised split loss

Three **49.9 Ω ±1% 0402** (`C25120`, UNI-ROYAL 0402WGF499JTCE, JLC **Basic**)
in a DELTA: one resistor between each pair of the three ports.

Driving port 1 through Z0 = 50 Ω with ports 2 and 3 terminated, symmetry puts
V2 = V3 so **no current flows in R23** — remove it:

```
Zin  = (R + Z0)/2 = (49.9 + 50)/2 = 49.95 Ω
Γin  = (49.95 − 50)/(49.95 + 50) = −5.00e−4      →  RL = 66.0 dB
V1   = Vs·Zin/(Z0+Zin) = 0.49975·Vs
V2   = V1·Z0/(R+Z0)    = 0.25013·Vs
P2/Pavail = (V2²/Z0)/(Vs²/4Z0) = 4·(0.25013)² = 0.25025   →  −6.017 dB
```

**Realised split loss 6.017 dB; realised port return loss 66.0 dB at DC.**
The ideal is 6.021 dB / ∞; using 49.9 Ω instead of 50.0 Ω costs 0.004 dB and
buys a JLC **Basic** part. Even ±5% parts would give 32 dB return loss, so
resistor tolerance is a non-issue for MATCH.

### 5.2 Amplitude balance from resistor tolerance

```
V2 ∝ Z0/(R+Z0)  ⇒  d(dB)/d(ΔR/R) = −8.686·R/(R+Z0) = −4.339 dB per unit
    ±1% part              → 0.043 dB
    two INDEPENDENT ±1%   → up to 2% differential → 0.087 dB
```

**0.087 dB worst-case arm-to-arm imbalance from the splitter alone.** Static,
calibratable, and part of the D4 published artifact. Specify all three
resistors from the same reel.

### 5.3 The 6.02 dB isolation is a THEOREM, not a part limitation

Three independent proofs, recorded so nobody re-litigates it:

1. **Eigenmode.** For any 3-fold-symmetric matched reciprocal 3-port with
   S11 = 0, the eigenvalues are 2·S12 and −S12. Demanding isolation
   (S12 = 0) zeroes all of them — a network that absorbs everything and
   transmits nothing.
2. **Uniqueness.** Allow a 2-fold-symmetric resistive network (delta
   Ra/Ra/Rb plus grounded resistors). Port-1 match forces Ra = 50 Ω; the
   port-2 match then reduces to `Rb² + 50·Rb − 5000 = 0 ⇒ Rb = 50 Ω`
   uniquely. **The 50/50/50 delta is the ONLY all-ports-matched resistive
   3-port.** You cannot trade loss for isolation.
3. **Sign.** With all-positive resistors, driving port 2 injects current into
   node 3 with the same sign via the direct path (through Rb) and via the
   indirect path (through port 1). V3 > 0 always. Cancellation requires a
   180° inverter or a negative resistance.

Confirmed empirically by the only commercial parts that span this bandwidth,
both resistive: Mini-Circuits ZFRSC-183-S+ (DC–18 GHz) states it in prose on
p.1 — *"resistive power divider do not provide a high degree of isolation
(basically isolation equals the insertion loss between ports)"* — and
measures 6.05 dB isolation @500 MHz to 6.22 dB @6 GHz.

### 5.4 Match at 6 GHz — set by mounting, not by the part

The chosen resistor is a commodity thick film with **no HF characterization,
no S-parameters and no application section**. Everything at 6 GHz rests on
the topology plus a generic mounting-parasitic model (Vishay AN 53077 p.2,
whose only HF-valid equivalent circuit carries Lp "due to the mounting" and
Cg "due to the mounting" as terms SEPARATE from the resistor).

```
Zin = (R + jωLp + Z0)/2
    Lp = 0.3 nH → +j11.3 Ω → Zin = 49.95 + j5.65 → RL 25.0 dB, VSWR 1.13
    Lp = 0.5 nH → +j18.8 Ω → Zin = 49.95 + j9.42 → RL 20.6 dB, VSWR 1.21
    Lp = 0.7 nH → +j26.4 Ω → Zin = 49.95 + j13.2 → RL 17.7 dB, VSWR 1.29
```

**If measured 6 GHz return loss comes in below ~15 dB, revisit** — the
documented remedy is a Vishay CH0402 or FC0402 HF thin-film 49.9 Ω
(characterized to 50 GHz, doc 53014 p.1), which is NOT LCSC-stocked, so
specifying it up front would be a sourcing failure.

### 5.5 Why DELTA and not STAR

Electrically identical in the ideal case. With the SAME mounting inductance
Lp = 0.5 nH at 6 GHz:

| | through path crosses | Zin @6 GHz | RL | VSWR |
|---|---|---|---|---|
| **delta**, 3× 49.9 Ω | ONE chip body | 49.95 + j9.42 | **20.6 dB** | 1.21 |
| star/wye, 3× 16.9 Ω | TWO chip bodies | 50.0 + j28.3 | 11.3 dB | 1.74 |

**9.3 dB better with identical parts**, because the delta's reactance-to-
resistance ratio is three times lower. And 49.9 Ω 0402 is a JLC **Basic**
part where 16.9 Ω (C82287) is Extended with **17 pieces in stock** — the star
costs more to assemble for a worse result. Also: the delta is inherently
mirror-symmetric about the axis through the input vertex, which is precisely
the geometry brief D4 wants. Rejected on all three counts. ADR-0003.

One consequence of the delta that must reach the layout: **it has no ground
node**, so keep the reference plane CONTINUOUS underneath — the small Cg at
each vertex partially cancels the series Lp, forming a pi-section that mimics
50 Ω line. (The opposite advice — void the plane under the node — applies to
the STAR.)

### 5.6 Wilkinson: refuted twice, independently

- **Size.** εeff = 2.70 + 1.70·13^−0.5 = 3.17 for a 70.7 Ω line on 1.6 mm
  FR4 ⇒ λg = 2.405 m ⇒ **λg/4 = 601 mm at 70 MHz.** (Brief D1 said ~400 mm —
  correct conclusion, 50 % optimistic number.)
- **Bandwidth.** The requirement is **6000/70 = 85.7:1**. A single-section
  Wilkinson manages ~1.4:1; published multi-section designs top out around
  10–20:1. Each section would be λ/4 at f_gm = 648 MHz = 65 mm, so six or
  seven meandered sections plus six or seven isolation resistors would consume
  400+ mm and STILL fall short.

No reactive splitter technology spans 85.7:1: ferrite/transformer types die
above ~2–3 GHz, LTCC and GaAs-IPD lumped types need impractical L and C below
~700 MHz, distributed types are λ/4-bound. Every LCSC-stocked 2-way splitter
was swept and rejected on band (ADR-0003). **Resistive is not settling — it
is what the industry does at this bandwidth.**

---

## 6. What lands at the Pluto RX input

At the **CITED** +8 dBm maximum PlutoPlus TX, with the ≥40 dB pad:

| f | total loss | RX level |
|---|---|---|
| 70 MHz | 44.59 dB | **−36.6 dBm** |
| 3.0 GHz | 47.76 dB | −39.8 dBm |
| 6 GHz | 50.16 dB | **−42.2 dBm** |
| **worst case (min pad, everything else credited at zero)** | **40.07 dB** | **−32.1 dBm** |

**Read the last row as what it is: the design point.** The pad is not sized to
hit the rows above it — those are where a typical unit happens to land. It is
sized so that the WORST row cannot hurt anything, because the pad's job is to
survive a misconfiguration (ADR-0016).

### 6.1 Damage margin — both governing numbers now CITED

**AD9363 RX absolute maximum input = +2.5 dBm PEAK**
[DS] AD9363 data sheet **Rev. D, printed page 15 of 32**, ABSOLUTE MAXIMUM
RATINGS, row `RF Inputs (Peak Power)`. Retrieval path and grade:
`spf/plutoplus_hardware/`, consumed through `03_src/rules/mates.yaml`.

**PlutoPlus TX maximum = +8 dBm**
[DS] same data sheet, **printed page 4 of 32**, TRANSMITTERS 800 MHz,
`Maximum Output Power`, *"1 MHz tone into 50 Ω load"*.

> **THIS SECTION USED TO CARRY A PARAGRAPH APOLOGISING FOR A SECONDARY
> SOURCE.** Both figures are now read from the vendor document with a page
> number, and three things came out of doing it properly:
>
> 1. **The secondary source was RIGHT.** +2.5 dBm is the number. The
>    EngineerZone answer the old text leaned on matched the datasheet exactly.
>    Confirming a figure that turns out to be correct is not wasted work — it
>    is the only way to know which of your numbers are the correct ones.
> 2. **The row says PEAK power, not average.** For the CW calibration tone
>    peak = average and it costs nothing. For a modulated stimulus it does not,
>    and anyone driving this fixture with modulation should size against peak.
>    The old text carried the value without the qualifier.
> 3. **TX max is +8 dBm, not +7.** The brief's "~+7 dBm" is the LOWEST of the
>    three characterized bands (8.0 / 7.5 / 7.0 dBm at 800 MHz / 2.4 GHz /
>    3.5 GHz), and it was being carried as if it were a ceiling. The design was
>    1 dB optimistic about its own input. **≥40 dB absorbs it without a
>    change**; 30 dB would also have absorbed it, so this is a correctness fix
>    rather than a rescue — but it is exactly the class of quiet error that
>    sizing against "intended" instead of "maximum" produces.
>
> **WHAT IS STILL OWED, and it is the honest residual:** both figures are the
> TRANSCEIVER's, not the SMA PORT's. The +8 dBm bounds the port only if the
> Pluto's TX front end is passive, and **nobody has established that on a
> PlutoPlus** (`spf/plutoplus_hardware/plutoplus_tx_frontend_active`, graded
> OWED). **What the design assumes meanwhile:** that the path from die to
> panel is passive (balun + match + filter), as it is on the original
> ADALM-Pluto, so +8 dBm is a hard ceiling. **What it costs if that is wrong:**
> the ≥40 dB minimum holds RX below the +2.5 dBm rating for any TX up to
> **+42.5 dBm**, and this board's own declared abuse ceiling is +27 dBm — so
> **19 dB of undiscovered TX gain** would have to exist before the board's own
> limit binds, and 34.5 dB before the receiver's does. The gap is bounded, and
> a power meter closes it in five minutes.

**Margin at the worst case: +2.5 − (−32.1) = 34.6 dB.** At the board's own
declared +27 dBm abuse ceiling it is still **15.6 dB** (§4.3) — which under
the 30 dB build was 2.7 dB.

**Assembly-fault ladder.** If BOTH arm pads were absent, RX = 8 − 6.89 −
25.78 = **−24.7 dBm**, 27 dB below the rating. If ALL FIVE chips of PAD_A1
were absent, RX = **−10.8 dBm**, 13.3 dB below. If EVERY pad were absent,
RX = **+1.1 dBm** — still below the +2.5 dBm absolute maximum, though above
the front end's ~0 dBm P1dB. **Under the 30 dB build the same all-pads-absent
case landed at +0.5 dBm, i.e. inside 2 dB of the rating; it is now inside
1.4 dB of it at a 1 dB higher TX.** The conclusion is unchanged and worth
restating: no credible assembly fault damages the Pluto, and the absurd one
produces a compressed, wrong measurement rather than a dead radio.

### 6.2 Linearity and SNR — what the extra 10 dB actually cost

- **Linearity.** The AD936x RX in-band 1 dB compression point is ≈0 dBm at
  minimum gain. At −33 to −42 dBm the AGC selects a mid gain index and nothing
  compresses — the cal path does not generate the distortion it exists to
  measure. The extra pad moved this further into the clear, not closer to it.
- **SNR.** Thermal floor at NF 5 dB: −109 dBm in 1 MHz, −96 dBm in 20 MHz.

| case | RX level | SNR in 1 MHz | SNR in 20 MHz |
|---|---|---|---|
| typical, 70 MHz | −36.6 dBm | **72 dB** | 59 dB |
| typical, 6 GHz | −42.2 dBm | **67 dB** | 54 dB |
| worst-case unit, 6 GHz (53.7 dB total) | −45.7 dBm | 63 dB | 50 dB |

The AD936x's 12-bit converter chain delivers ~65–70 dB in-band. So:

**In a 1 MHz analysis bandwidth the measurement stays CONVERTER-limited across
the band** — repeatability is set by the ADC, not by how warm the room is. **In
a 20 MHz span the top of the band becomes NOISE-limited**, at 50–54 dB. That is
the price of the extra 10 dB, stated rather than hidden, and it is the
recoverable side of the asymmetry the decision was made on: **16× averaging
returns 12 dB, offline and free**, and a phase-calibration measurement is
averaged anyway.

**Under the old 30 dB build the same rows read 86 / 73 dB and the design sat
in the middle of the window rather than at its lower edge.** The trade was
made deliberately: SNR you can buy back with time, a destroyed receiver you
cannot.

---

## 7. Isolation budget — including the one the board does NOT solve

| path | 70 MHz | 6 GHz | derivation |
|---|---|---|---|
| RX1 ↔ RX2 (loopback mode) | **29.9 dB** | 29.6 dB | 6.02 + 2·A2 §4.2(a) — **UNCHANGED by A9** |
| antenna → Pluto, loopback mode | 43 dB | 20 dB | switch RFin→RF1 isolation, min [DS WN6 Table 5] |
| TX port return loss, loopback mode | **23.6 dB typ** | **27.2 dB typ / 11.7 dB guaranteed** | PAD_A1's own VSWR [DS YAT-10A+ REV B p.2: 1.09 typ / 1.25 max DC–5 GHz, 1.10 typ / **1.70 max** 5–15 GHz; measured p.4: 1.14 @10 MHz, 1.03 @5 GHz, 1.09 @8 GHz]. **Still set by the FIRST chip of PAD_A1, which is still pre-split — the one surviving argument of the all-pre-split position, and A9 only strengthened it** |
| **loopback → Pluto, ANTENNA mode, TX ON** | **−73 dBm** | **−50 dBm** | see below |
| **TX → any RX, ANY switch state, ANY switch fault** | **≥40.07 dB** | ≥40.07 dB | **the pad chain is UPSTREAM of both switches** — §7.2 |

### 7.1 The limitation the board does not fix, and why that is correct

In ANTENNA mode with TX driven at +8 dBm, the loopback arm sits at
8 − 38.0 = **−30.0 dBm** on the switch's deselected RF2 throw. Switch
isolation is 43 dB min at 70 MHz and 20 dB min at 6 GHz [DS], so
**−73 dBm / −50 dBm** reaches RX_PLUTO — 23 to 46 dB above a Pluto RX noise
floor of ≈−96 dBm in 20 MHz.

**Transmitting while receiving on antennas will still contaminate the receive
path**, by 9 dB less than under the 30 dB build. No single stocked SPDT fixes
it, and A9 did not set out to — but note that raising the pre-split pad is the
one change that improves this leakage as a side effect, because the leakage
path also starts at TX_PLUTO and also crosses PAD_A1.

The brief's two states are "antenna→Pluto" and "TX→both RX". Simultaneous
transmit-and-antenna-receive is not among them, so the SIMPLEST reading that
satisfies the stated requirement is taken (SKILL.md SPEC-CHECK rule) and the
limitation is documented rather than engineered away. **If the user later
needs it**, the fix is cheap and named: a THIRD BGS12WN6 gating TX, one throw
on a 50 Ω 0402 terminator, adds 20–43 dB for ~$0.25 and one control bit.
ADR-0004 records the rejection.

### 7.2 The pad is UPSTREAM of the switch — asked explicitly, and it matters

`TX_PLUTO` connects to exactly one thing: PAD_A1's input. Every path from
there to an RX port crosses **A1 → the split → an A2 → the switch**, in that
order. **The complete pad chain lies between the TX port and either switch**,
so:

| case | what reaches RX_PLUTO |
|---|---|
| loopback throw (RF2), normal | TX − (A1 + 6.02 + A2) = **≥40.07 dB down** |
| antenna throw (RF1), normal | the same chain PLUS 20–43 dB of switch isolation |
| **switch STUCK in either throw** | one of the two rows above — the chain is not bypassed |
| **switch DESTROYED, die shorting RFin–RF1–RF2** | still the full chain: **≥40.07 dB down** |

**No switch state and no switch failure can present raw TX to a receiver.** If
the pads had sat downstream of the switch instead, a stuck or shorted switch
would put TX_PLUTO on an RX port at the splitter's 6.02 dB alone — RX at
+2 dBm from a +8 dBm TX, i.e. **at the absolute-maximum rating**, and a dead
receiver regardless of what the total attenuation said.

**This property was already bought, and by an argument that had nothing to do
with faults.** ADR-0004 put A2 *in the arm* — between the splitter and the
switch — on isolation, open-cable masking, antenna-mode reflection and
AGC-dependent leakage. Fault immunity fell out for free and had simply never
been written down.

**The counterpart, stated so it is not mistaken for coverage.** The ANTENNA
path carries **no pad at all**: `RX_ANT → 1 nF block → SW.RF1 → RFin →
RX_PLUTO`, ≈0.3 dB. A transmitter connected to an antenna port reaches the
Pluto's receiver essentially unattenuated. That is what an antenna port IS, it
is outside the two states the brief specifies, and ADR-0009's input-protection
posture is what covers it. **≥40 dB protects the CALIBRATION path. Nothing
protects the antenna path, by construction.**

---

## 8. DC coupling — closed by derivation, not left open

Both switch datasheets state `V_RFDC = 0 V max`, *"No DC voltages allowed on
RF-Ports"*, with footnote 1: *"There is also a DC connection between switched
paths."* So **every RF port on both switches, plus all three splitter ports,
is ONE galvanic node.** A single DC fault anywhere violates the rating
everywhere at once.

**Where the node's DC reference comes from.** A DC–18 GHz absorptive YAT pad
is a thin-film pi with through-wafer vias to ground; for a 10 dB pi,
R_shunt ≈ 96.2 Ω and R_series ≈ 71.2 Ω, so **each RF port presents ≈70 Ω of
DC resistance to ground.** With PAD_A1 and both PAD_A2 chains in the network,
the entire internal RF node is DC-tied to ground through the pads. **The node
sits at 0 V DC by construction — V_RFDC = 0 is satisfied without any DC
blocking capacitor on the loopback path.**

**Where a block IS needed: the two ANTENNA ports.** `RX_ANT1` and `RX_ANT2`
are user-facing and are the one place an unknown DC source can appear — an
active antenna or bias-tee'd LNA. Without a block, that bias would be shorted
to ground through the switch die and the pads, driving fault current through
a 0.7 × 1.1 mm part.

**Fitted: 1 nF 0402 C0G/NP0, 50 V, in series with each `RX_ANT` port.**

```
70 MHz: Xc = 1/(2π·70e6·1e−9) = 2.27 Ω
        Γ = jXc/(Xc + 2·Z0) → |Γ| = 0.0227 → RL 32.9 dB, IL 0.002 dB
6 GHz:  0402 ESL ≈ 0.4 nH → XL = 15.1 Ω, Xc = 0.027 Ω → net +j15.0 Ω
        |Γ| = 0.150 → RL 16.5 dB, IL 0.05 dB
```

Value choice: 1 nF is the compromise across 85.7:1. 100 pF gives 22.7 Ω at
70 MHz (RL 12.9 dB, IL 0.22 dB) — worse at the bottom. Package choice: an
**0201** would give ESL ≈ 0.25 nH ⇒ +j9.4 Ω ⇒ **RL 20.6 dB** at 6 GHz, 4 dB
better; 0402 is specified for assembly robustness on a low-volume bench
board, with 0201 recorded as the documented upgrade if measured antenna-port
return loss disappoints. **The block sits on the ANTENNA path only — the
calibration path carries no capacitor**, which is the whole point of choosing
a DC-through switch.

**Still open (O6): confirm the PlutoPlus RX/TX SMAs are DC-free.** They are
almost certainly balun-coupled, but nobody has asserted it. If they are not,
blocks are needed on the three Pluto-facing SMA ports too and the calibration path
inherits ~0.05 dB and a 16.5 dB local return loss at 6 GHz.

---

## 9. Control-path component values

| ref | value | derivation |
|---|---|---|
| `R_CTRL1/2` series at each switch CTRL | **1 kΩ** | I_Ctrl max 10 nA [DS] ⇒ drop 10 µV against a V_Ctrl,H floor of 1.0 V. Upper bound R < 0.01·(3.3−1.0)/10 nA = 2.3 MΩ, so 1 kΩ is three orders inside. Chosen for RF damping, not for level |
| `C_CTRL1/2` shunt at each switch CTRL | **1 nF 0402 X7R** | Infineon's own measurement board carried 1 nF CTRL–GND and 1 nF VDD–GND (Table 6 fn 2). With the 1 kΩ this makes the shared control net RF-dead: at 1.5 GHz — λ/4 of a 25 mm control stub on this stackup, i.e. mid-band — the 1 nF is ≈0.1 Ω plus j2.4 Ω of ESL, an effective short. **Without it the control trace is a resonator, not a wire** |
| | | RC = 1 µs, so the state transition takes ≈2.2 µs against the switch's own 220 ns [DS WN6 Table 10]. The brief states no switching-speed requirement; a bench cal switch does not need microseconds |
| `R_CTRL_PD1/2` pulldown at each switch | **10 kΩ** | Must hold CTRL below V_Ctrl,L = 0.45 V against I_Ctrl max 10 nA ⇒ R_max = 45 MΩ; 10 kΩ is chosen for noise immunity. Load check: two in parallel = 5 kΩ ⇒ 0.66 mA from the MCU at 3.3 V, inside even the 2 mA drive setting (VOH ≥ 2.62 V) [DS] |
| `R_HDR_S` header series | **3.3 kΩ** | With `R_HDR_G` forms a ÷2.5 divider (§9.1). Also bounds a reverse fault: an MCU pin wrongly driving 3.3 V into a Zynq pin clamped at ~2.3 V sources (3.3−2.3)/3.3k = **0.303 mA**, inside any IO clamp |
| `R_HDR_G` header shunt to GND | **2.2 kΩ** | Divider ratio (R_S+R_G)/R_G = (3.3+2.2)/2.2 = **2.5**. Also the pull-down that makes an UNCONNECTED header read 0 V = antenna mode. Loading on a 1.8 V driver: 1.8/5.5 kΩ = 0.33 mA |
| ADC threshold (firmware) | **0.36 V** | Half of the 1.8 V case. Header levels at the pin: 1.8 V→0.72 V, 3.3 V→1.32 V, 5.0 V→2.00 V, all inside the 0–3.3 V ADC range; a 12-bit LSB is 0.81 mV |
| `R_LED` ×2 | **680 Ω** | (3.3 − 2.0)/2 mA = 650 Ω → E24 680 Ω ⇒ 1.9 mA |

### 9.1 Why the header divider exists at all

**PlutoPlus IO is 1.8 V; the MCU's VIH is a flat 2.0 V** [DS RP2040 Table 625
§5.5.3.4 p.615 — *not* 0.65·IOVDD]. A Zynq HR bank at VCCO = 1.8 V has a
worst-case VOH of VCCO − 0.45 = **1.35 V**. A direct connection reads
permanently LOW and the board silently stays in antenna mode forever.

**This failure is FAIL-SAFE**, which is exactly what makes it dangerous: it
passes any bench test that asks "can it spuriously enter loopback", and is
found only as "the GPIO control doesn't work" — plausibly after seal.

The ADC path (ARCHITECTURE §4.2) removes it for two resistors, accepts 1.8 V
/ 3.3 V / 5.0 V logic without a translator or a second rail, and is
**input-only by construction** — an ADC-configured pin has its digital output
disabled, so no firmware bug can drive 3.3 V into a Zynq pin whose absolute
maximum is ≈VCCO + 0.55 = 2.35 V. ADR-0008.

---

## 10. Open numeric items

| # | number | status |
|---|---|---|
| **N1** | **SMA CABLE insertion loss (rows 2, 15)** | **[EST] 0.20 dB @70 MHz / 1.50 dB @6 GHz each, ×2 bar**, for a 0.3 m RG316-class assembly. **The cables are USER-SUPPLIED and not on this BOM**, so no vendor number is asserted and none is needed: **ADR-0016's ≥40 dB minimum credits them at ZERO**, and the release publishes the measured curve with whatever cables the user runs. This is the largest [EST] on the board and it cannot move the specification |
| N1b | Board SMA launch and cable-plug mated-pair loss (rows 1, 3, 14, 16) | **[EST] 0.02–0.05 / 0.08–0.25 dB each.** No vendor publishes an insertion-loss figure for `KH-SMA-KE-Z`; what IS on its datasheet p.1 is **VSWR ≤1.35 over DC–6 GHz**, and ADR-0007 RULE 2 carries the pessimistic ~11–15 dB launch return loss at 6 GHz rather than a modelled 22.3 dB. Also credited at zero in the guarantee |
| ~~N2~~ | AD9363 RX absolute-maximum input, +2.5 dBm | **CLOSED 2026-07-27 — now [DS] CITED**, Rev. D printed p.15 of 32, `RF Inputs (Peak Power)`. The secondary source was correct. See §6.1 for the PEAK-vs-average qualifier that came with it |
| **N2b** | PlutoPlus TX maximum, **+8 dBm** | **[DS] CITED**, Rev. D printed p.4 of 32 — and 1 dB HIGHER than the +7 dBm this document carried. **Residual: it is the TRANSCEIVER's maximum, not the PORT's** (`plutoplus_tx_frontend_active`, OWED). §6.1 states what is assumed meanwhile and bounds it: 19 dB of undiscovered TX gain before the board's own +27 dBm ceiling binds |
| N3 | 50 Ω / 90 Ω trace widths | closed-form, not a field solve. **Re-confirm against JLCPCB's calculator for the ordered stackup** before release |
| N4 | Routed lengths (§2) | design targets, not measurements. Re-run §3.3/§3.5 after placement — **a documentation refresh now, not a design risk (§3.6)** |
| N5 | BGS12WN6 board-level IL/RL | **does not exist.** Infineon publishes prober-station numbers only (Table 4 fn 1). Any board-level figure is an estimate |
| ~~N6~~ | RF axis height above the Pluto PCB | **CLOSED by A8** — cables have no Z relationship, and the Pluto is cased so its PCB was never the reference. The fact stays OWED in `spf/`; this board no longer spends it |
| **N7** | Mid-value YAT stock (15A+ / 12A+ / 5A+ / 3A+) | **UNVERIFIED.** PAD_A1 is a five-chip cascade only because YAT-10A+ and YAT-2A+ are the values with checked stock. **A substitute's own MIN column must be read** — the ≥40 dB guarantee is built on min columns and cannot rest on an unverified one |
