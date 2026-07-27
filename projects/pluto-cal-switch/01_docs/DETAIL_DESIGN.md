# DETAIL_DESIGN — pluto-cal-switch

Every component value, derived, with its equation and its margin. A value in
the schematic with no line here is UNJUSTIFIED.

Conventions: **[DS]** = read from a manufacturer datasheet with the citation
given. **[DERIVED]** = computed here from [DS] inputs. **[EST]** = an estimate
with no datasheet behind it — every one is named, and §3.6 states which of
them the conclusion is sensitive to.

---

## 1. The stackup constants everything else rests on

JLCPCB `JLC04161H-7628`, 4-layer 1.6 mm. L1→L2 prepreg **0.2104 mm**, Dk 4.4
(JLC published), εr taken as 4.3, tan δ 0.02, 1 oz Cu.

| quantity | value | source |
|---|---|---|
| 50 Ω microstrip width, L1 over L2 | **0.35 mm** | [DERIVED] Hammerstad-Jensen with thickness correction: 0.30 → 55.2 Ω, 0.35 → 51.0 Ω, 0.38 → 48.8 Ω, 0.40 → 47.5 Ω |
| 90 Ω differential pair (USB) | **0.33 mm / 0.25 mm gap** ⇒ ~89 Ω | [DERIVED] `Zdiff ≈ 2·Z0·(1 − 0.48·e^(−0.96·s/h))` |
| ε_eff | **3.26** | [DERIVED] |
| propagation delay | **6.0 ps/mm** | [DERIVED] `tpd = √ε_eff / c` |
| λg at 6 GHz | **27.7 mm** | [DERIVED] |
| λg/20 at 6 GHz (lumped-element ceiling) | **1.39 mm** | [DERIVED] |
| λg/12 at 6 GHz (via-fence pitch) | **2.3 mm** → use **≤2.0 mm** | [DERIVED] |

> The widths are closed-form, not a field solve. **They must be re-confirmed
> against JLCPCB's own impedance calculator for the exact stackup ordered,
> before release.** Recorded as a CHECKLIST item.

### 1.1 Microstrip loss — the term the sourcing spike got wrong by 2.7×

Conductor loss (∝√f) plus dielectric loss (∝f), for w = 0.35 mm:

```
α_d = 27.3 · [εr(ε_eff−1)] / [√ε_eff·(εr−1)] · tanδ / λ0
    = 27.3 · (4.3×2.26)/(1.8055×3.3) · 0.02/λ0 = 0.8906/λ0   dB/m
    @6 GHz (λ0 = 49.97 mm):  17.8 dB/m = 0.178 dB/cm

Rs  = √(π·f·µ0/σ),  σ_Cu = 5.8e7 S/m
    @6 GHz: Rs = 0.02021 Ω/sq
α_c = K · 8.686·Rs/(Z0·w),  K = 1.6 (edge current crowding, narrow line)
    @6 GHz: 1.6 × 8.686×0.02021/(50×0.00035) = 16.1 dB/m = 0.161 dB/cm
```

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
| `TX_PLUTO` SMP → PAD_A1 in | 10 mm | TX sits at one end of the three SMP ports (ARCHITECTURE §2) |
| PAD_A1 out → splitter vertex | 22 mm | the splitter is on the mirror axis between the two RX ports; TX enters from the side |
| splitter arm → PAD_A2 in | 8 mm | ×2, mirrored |
| PAD_A2 out → switch RF2 | 8 mm | ×2, mirrored |
| switch RFin → `RX_PLUTOn` SMP | 5 mm | switch hugs its SMP |
| **total, TX SMP → each RX SMP** | **53 mm** | |
| switch RF1 → `RX_ANTn` SMA | 20 mm | ×2, antenna edge |

**53 mm × 6.0 ps/mm = 318 ps** nominal one-way loopback delay per arm. The D4
artifact is the measured per-arm length and the arm-to-arm DELTA, converted
with the 6.0 ps/mm constant pinned to the ordered stackup.

---

## 3. The loss budget — TX_PLUTO to EACH RX_PLUTO, control ON

Measured at the **Pluto's own SMA jacks**, so the SMA→SMP adapters are inside
the budget.

### 3.1 Every term

| # | element | 70 MHz | 6 GHz | source |
|---|---|---|---|---|
| 1 | SMA→SMP adapter, TX side | 0.05 | 0.15 | [EST] — see §10 |
| 2 | SMP mated pair + board launch, TX | 0.05 | 0.20 | [EST] |
| 3 | µstrip 10 mm | 0.019 | 0.36 | [DERIVED] §1.1 |
| 4 | **PAD_A1** | *A1* | *A1* | [DS] §4 |
| 5 | µstrip 22 mm | 0.042 | 0.79 | [DERIVED] |
| 6 | resistive delta 2-way split | **6.021** | **6.021** | [DERIVED] EXACT, §5.1 |
| 7 | splitter mounting-parasitic excess | 0.00 | 0.35 | [EST] modelled; the measured reference (Mini-Circuits ZFRSC-183-S+ REV D p.1, a DC–18 GHz coax resistive divider) runs 6.05 dB @500 MHz → 6.36 dB @6 GHz, i.e. +0.31 dB |
| 8 | µstrip 8 mm | 0.015 | 0.29 | [DERIVED] |
| 9 | **PAD_A2** | *A2* | *A2* | [DS] §4 |
| 10 | µstrip 8 mm | 0.015 | 0.29 | [DERIVED] |
| 11 | SPDT insertion loss | 0.20 | 0.65 | [DS] §3.2 |
| 12 | µstrip 5 mm | 0.010 | 0.18 | [DERIVED] |
| 13 | SMP mated pair + board launch, RX | 0.05 | 0.20 | [EST] |
| 14 | SMA→SMP adapter, RX side | 0.05 | 0.15 | [EST] |
| | **NON-PAD SUBTOTAL** | **6.54** | **9.63** | |

**Chain tilt = 3.09 dB.** It is irreducible: 1.80 dB of it is microstrip loss,
0.45 dB the switch, 0.50 dB the coax interfaces, 0.35 dB splitter parasitics.
No pad value makes the total 30 dB at both ends.

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
separately in rows 3/10/12 — a small deliberate double-count in the
conservative direction.

Worst case over temperature and supply: **0.25 / 1.00 dB** [DS].

### 3.3 The loss curve

| f | µstrip | switch | coax IFs | splitter par. | split | **L(f)** |
|---|---|---|---|---|---|---|
| 70 MHz | 0.11 | 0.20 | 0.21 | 0.00 | 6.02 | **6.54** |
| 648 MHz¹ | 0.41 | 0.20 | 0.25 | 0.04 | 6.02 | **6.92** |
| 2 GHz | 0.86 | 0.24 | 0.37 | 0.12 | 6.02 | **7.60** |
| 3 GHz | 1.14 | 0.32 | 0.45 | 0.18 | 6.02 | **8.11** |
| 4.5 GHz | 1.54 | 0.43 | 0.58 | 0.26 | 6.02 | **8.82** |
| 6 GHz | 1.91 | 0.65 | 0.70 | 0.35 | 6.02 | **9.63** |

¹ 648 MHz = √(70 × 6000), the geometric mean of the band.

### 3.4 Choosing the pad — and the D5 assumption

"30 dB TOTAL" (fact-locked by A2) is a **scalar against a chain that tilts
3.09 dB**. It cannot be true everywhere. The user has not named a reference
frequency. **D5: the pad is chosen by MINIMAX** — the value that minimizes
the worst-case deviation from 30 dB, privileging no frequency:

```
P_minimax = 30 − (L(70 MHz) + L(6 GHz))/2 = 30 − (6.54 + 9.63)/2 = 21.92 dB
```

Realizable from stocked Mini-Circuits YAT parts:
`A1 = YAT-10A+`, `A2 = YAT-10A+ + YAT-2A+` per arm. From the MEASURED
typical-performance tables (YAT-10A+ REV B p.4, YAT-2A+ REV B p.4 — read from
the PDFs vendored in `02_parts/`):

| | 10 MHz | 5 GHz | 8 GHz | ⇒ at 6 GHz |
|---|---|---|---|---|
| YAT-10A+ | 9.98 | 9.96 | 9.96 | 9.96 |
| YAT-2A+ | 1.94 | 1.82 | 1.81 | 1.815 |
| **cascade A1+A2** | **21.90** | 21.74 | 21.73 | **21.74** |

**P = 21.90 dB at 70 MHz falling to 21.74 dB at 6 GHz — the pad contributes
only 0.16 dB of the chain's 3.09 dB tilt.**

| f | L(f) | + P (measured typ) | total |
|---|---|---|---|
| 70 MHz | 6.54 | 21.90 | **28.44 dB** |
| 648 MHz | 6.92 | 21.89 | 28.81 dB |
| 2 GHz | 7.60 | 21.84 | 29.44 dB |
| **≈3.0 GHz** | 8.11 | 21.82 | **29.93 dB ← 30 dB is met HERE** |
| 4.5 GHz | 8.82 | 21.78 | 30.60 dB |
| 6 GHz | 9.63 | 21.74 | **31.37 dB** |

**Result: 30 dB is met at ≈3.0 GHz; the band span is 30.0 −1.6 / +1.4 dB.**

**What changes if the user names a different reference frequency** — in every
case it is a change to ONE BOM line (the arm chain's second YAT part), same
footprint, two placements:

| reference | pad wanted | build | 70 MHz | 6 GHz | RX1↔RX2 isolation |
|---|---|---|---|---|---|
| 70 MHz or 648 MHz | 23.5 / 23.1 dB | A2 = YAT-10A+ + **YAT-3A+** (22.87 total) | 29.4 dB | 32.5 dB | 31.8 dB |
| **≈3.0 GHz (minimax — CHOSEN)** | 21.9 dB | A2 = YAT-10A+ + **YAT-2A+** (21.86) | 28.4 dB | 31.4 dB | 29.8 dB |
| 6 GHz | 20.4 dB | A2 = **YAT-10A+ alone** (19.97) | 26.5 dB | 29.6 dB | 26.0 dB |

### 3.5 The guaranteed envelope, not just the typical

Datasheet min/max columns [DS], YAT-10A+ p.2 and YAT-2A+ p.2:

| | DC–5 GHz | 5–15 GHz |
|---|---|---|
| YAT-10A+ | 9.6 / 9.97 / 10.4 | 9.5 / 9.98 / 10.5 |
| YAT-2A+ | 1.5 / 1.92 / 2.3 | 1.4 / 1.85 / 2.3 |
| A1 + A2 total | 20.7 / 21.86 / 23.1 | 20.4 / 21.81 / 23.3 |

**Total TX→RX, guaranteed envelope across band AND unit-to-unit:
27.2 dB to 32.9 dB.** That is the number the release publishes, alongside the
measured curve — not "30 dB".

### 3.6 Which estimates the conclusion is sensitive to

| [EST] term | value @6 GHz | if it were HALF | if it were DOUBLE |
|---|---|---|---|
| microstrip loss (0.036 dB/mm) | 1.91 dB | P → 22.4 (still 22 dB build) | P → 20.9 (drops to YAT-1A+ arm) |
| coax interfaces (rows 1,2,13,14) | 0.70 dB | P → 22.1 | P → 21.6 |
| splitter parasitic excess | 0.35 dB | P → 22.0 | P → 21.7 |
| **all three together** | 2.96 dB | P → 23.4 (⇒ YAT-3A+ arm) | P → 20.4 (⇒ no arm second pad) |

**The 22 dB build is robust to any single estimate being wrong by 2×, and
breaks only if all three are wrong the same way.** That is the honest
statement of confidence, and it is why the reference-frequency question (D5)
is a bigger lever than the estimate error.

**TRIGGER TO RE-DERIVE:** once the board is routed, replace rows 3/5/8/10/12
with the actual lengths and re-run §3.3/§3.4. If the measured total
interconnect at 6 GHz lands below ~1.4 dB, the arm's second YAT part changes.

---

## 4. The attenuator — why chips, why split, why these values

### 4.1 Chip over discrete: decided on FLATNESS, not on spread

A calibration reference sells a KNOWN number across a swept band.

| option | tilt, 70 MHz → 6 GHz | 6 GHz spread over plausible parasitics | cost |
|---|---|---|---|
| YAT cascade | **0.16 dB** [DS] measured typical-performance tables, YAT-10A+ REV B p.4 + YAT-2A+ REV B p.4 (vendored) | 20.7–23.1 dB (a datasheet-GUARANTEED window) | ~$17/board |
| 2× cascaded 11.5 dB 0402 pi | 0.56 dB [EST] modelled | 21.3–22.7 dB (an UNKNOWN — depends on ground-via inductance the fab does not guarantee) | ~$0.06/board |
| single 23 dB 0402 pi | **2.14 dB** [EST] | 18.1–22.0 dB | ~$0.03/board |

The single pi collapses for a reason worth writing down: a 23 dB pi needs a
348 Ω series element, and an 0402's own end-to-end parasitic capacitance
(~0.05 pF) is ~530 Ω at 6 GHz — **the resistor is half-shorted by its own
package.** This is why discrete pads above ~15 dB stop working at multi-GHz,
and it is why the arm pads are built as 10 + 2 rather than as one 12.

Note the honest comparison: **the chip's GUARANTEED window (±1.15 dB) is
WIDER than the discrete's MODELLED spread (±0.7 dB).** The chip does not win
on spread. It wins on flatness — 0.16 dB against 0.56 dB — which is the
property a swept cal reference actually sells. ADR-0004.

Discrete stays as the fully-specified zero-stock-risk fallback: each 11.5 dB
pi is 3× 86.6 Ω 0402 1% (E96 rounds shunt/series/shunt 86.25/87.31/86.25 to
one value); stock verified C158969 (5202), C227253 (4450), C830266 (1038).

### 4.2 Split 10 dB pre / 12 dB per arm — four independent reasons

The obvious build is one 22 dB pad before the split. It is wrong.

**(a) Inter-channel isolation.** A resistive split gives 6.02 dB port-to-port
and that is a theorem (§5.3), not a part limitation. Attenuation placed AFTER
the split counts TWICE, because a wave reflected off one RX port traverses
that arm's pad twice while the wanted signal traverses it once:

```
isolation(RX1↔RX2) = 6.02 + 2·A2
    A2 = 0   →  6.02 dB
    A2 = 12  →  29.8 dB     ← chosen
```

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

At the fact-locked +7 dBm (5.01 mW) PlutoPlus TX:

| element | power in | dissipation | rating [DS] | margin |
|---|---|---|---|---|
| PAD_A1 (YAT-10A+) | 5.0 mW | 4.5 mW | 1.7 W @25 °C | **25.8 dB** |
| splitter, hottest resistor | 0.45 mW | 0.11 mW | 62.5 mW @70 °C | **27.4 dB** |
| PAD_A2 (YAT-10A+) | 0.11 mW | 0.10 mW | 1.7 W | 42 dB |
| SPDT | 0.02 mW | — | P_RF 26 dBm CW [DS WN6 Table 3] | 33 dB |

**Board TX absolute ceiling** — the binding element is the SPDT's 26 dBm CW
operating limit (BGS12WN6, Table 3, PDF p5), which the loopback path reaches
only at TX = 26 + 21.9 + 6.0 ≈ far above; the real first limit is **PAD_A1 at
+32.3 dBm** (1.7 W). Declared board ceiling: **TX ≤ +27 dBm (0.5 W)**, a 5 dB
guard band below PAD_A1's rating.

> TX drive level is the one BRIEF fact-lock row still OPEN. At +7 dBm nothing
> is close. The ceiling above is what protects the board if the user later
> puts an external PA on TX_PLUTO. Note the discrete fallback pad is 13 dB
> LESS forgiving — its input shunt resistor reaches 62.5 mW at ~+18.7 dBm.

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

At the fact-locked +7 dBm TX, with the chosen 21.86 dB pad:

| f | total loss | RX level |
|---|---|---|
| 70 MHz | 28.40 dB | **−21.4 dBm** |
| 3.0 GHz | 29.97 dB | −23.0 dBm |
| 6 GHz | 31.44 dB | **−24.4 dBm** |
| worst case (min pad, min loss) | 27.2 dB | **−20.2 dBm** |

### 6.1 Damage margin

AD9363 RX absolute maximum input = **+2.5 dBm**.

> **CITATION STRENGTH, STATED RATHER THAN DRESSED UP: this figure is a
> SECONDARY source.** Two independent attempts (the sourcing spike and its
> adversarial pass) both failed to open a primary AD9363 absolute-maximum
> page — analog.com, Mouser, DigiKey, Verical and Arrow all returned 403 or a
> JS shell, DigiKey's HTML mirror now returns 410 Gone, and both LCSC
> datasheet URLs resolve to a one-page placeholder. The number comes from ADI
> EngineerZone answers. **It must be confirmed against AD9363 Rev. D before
> it is relied on.** Open item O5.

**Margin at the worst case: +2.5 − (−20.2) = 22.7 dB.** A 6 dB error in the
cited figure still leaves ~17 dB. The conclusion is insensitive to the
citation weakness, which is why it does not block.

**Single-fault check.** If BOTH arm pads were absent (an assembly fault),
RX = 7 − 6.5 − 10.0 = **−9.5 dBm** — still 12 dB below the abs max. If ALL
pads were absent, RX = **+0.5 dBm** — below the abs max but ABOVE the RX
front-end's ~0 dBm P1dB. So no credible single or double assembly fault
damages the Pluto, but a triple fault would produce a compressed, wrong
measurement rather than a dead radio.

### 6.2 Linearity and SNR — the level is right for a POSITIVE reason

- **Linearity.** The AD936x RX in-band 1 dB compression point is ≈0 dBm at
  minimum gain. At −21 to −24 dBm the AGC selects a mid gain index and
  nothing compresses — the cal path does not generate the distortion it
  exists to measure.
- **SNR.** Thermal floor at NF 5 dB: −109 dBm in 1 MHz, −96 dBm in 20 MHz.
  At −23 dBm that is **86 dB / 73 dB of SNR**, both ABOVE what the AD936x's
  12-bit converter chain delivers (~65–70 dB in-band).

**The measurement is CONVERTER-limited, not noise-limited** — repeatability
is set by the ADC, not by how warm the room is. Going hotter (−15 dBm) buys
no usable SNR because the converter already dominates; going below about
−40 dBm would start to cost. **−23 dBm is the correct window and the design
lands in the middle of it.**

---

## 7. Isolation budget — including the one the board does NOT solve

| path | 70 MHz | 6 GHz | derivation |
|---|---|---|---|
| RX1 ↔ RX2 (loopback mode) | **29.8 dB** | 29.7 dB | 6.02 + 2·A2 §4.2(a) |
| antenna → Pluto, loopback mode | 43 dB | 20 dB | switch RFin→RF1 isolation, min [DS WN6 Table 5] |
| TX port return loss, loopback mode | **23.6 dB typ** | **27.2 dB typ / 11.7 dB guaranteed** | PAD_A1's own VSWR [DS YAT-10A+ REV B p.2: 1.09 typ / 1.25 max DC–5 GHz, 1.10 typ / **1.70 max** 5–15 GHz; measured p.4: 1.14 @10 MHz, 1.03 @5 GHz, 1.09 @8 GHz] |
| **loopback → Pluto, ANTENNA mode, TX ON** | **−64 dBm** | **−43 dBm** | see below |

### 7.1 The limitation the board does not fix, and why that is correct

In ANTENNA mode with TX driven at +7 dBm, the loopback arm sits at
7 − 30.3 = **−23.3 dBm** on the switch's deselected RF2 throw. Switch
isolation is 43 dB min at 70 MHz and 20 dB min at 6 GHz [DS], so
**−64 dBm / −43 dBm** reaches RX_PLUTO — 32 to 53 dB above a Pluto RX noise
floor of ≈−96 dBm in 20 MHz.

**Transmitting while receiving on antennas will contaminate the receive
path.** No single stocked SPDT fixes this.

The brief's two states are "antenna→Pluto" and "TX→both RX". Simultaneous
transmit-and-antenna-receive is not among them, so the SIMPLEST reading that
satisfies the stated requirement is taken (SKILL.md SPEC-CHECK rule) and the
limitation is documented rather than engineered away. **If the user later
needs it**, the fix is cheap and named: a THIRD BGS12WN6 gating TX, one throw
on a 50 Ω 0402 terminator, adds 20–43 dB for ~$0.25 and one control bit.
ADR-0004 records the rejection.

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
blocks are needed on the three SMP ports too and the calibration path
inherits ~0.05 dB and a 16.5 dB local return loss at 6 GHz.

---

## 9. Control-path component values

| ref | value | derivation |
|---|---|---|
| `R_CTRL1/2` series at each switch CTRL | **1 kΩ** | I_Ctrl max 10 nA [DS] ⇒ drop 10 µV against a V_Ctrl,H floor of 1.0 V. Upper bound R < 0.01·(3.3−1.0)/10 nA = 2.3 MΩ, so 1 kΩ is three orders inside. Chosen for RF damping, not for level |
| `C_CTRL1/2` shunt at each switch CTRL | **1 nF 0402 X7R** | Infineon's own measurement board carried 1 nF CTRL–GND and 1 nF VDD–GND (Table 6 fn 2). With the 1 kΩ this makes the shared control net RF-dead: at 1.5 GHz — λ/4 of a 25 mm control stub on this stackup, i.e. mid-band — the 1 nF is ≈0.1 Ω plus j2.4 Ω of ESL, an effective short. **Without it the control trace is a resonator, not a wire** |
| | | RC = 1 µs, so the state transition takes ≈2.2 µs against the switch's own 220 ns [DS WN6 Table 10]. The brief states no switching-speed requirement; a bench cal switch does not need microseconds |
| `R_CTRL_PD1/2` pulldown at each switch | **10 kΩ** | Must hold CTRL below V_Ctrl,L = 0.45 V against I_Ctrl max 10 nA ⇒ R_max = 45 MΩ; 10 kΩ is chosen for noise immunity. Load check: two in parallel = 5 kΩ ⇒ 0.66 mA from the MCU at 3.3 V, inside even the 2 mA drive setting (VOH ≥ 2.62 V) [DS] |
| `R_HDR_S` header series | **2.2 kΩ** | With `R_HDR_G` forms a ÷2.5 divider (§9.1). Also bounds a reverse fault: an MCU pin wrongly driving 3.3 V into a Zynq pin clamped at ~2.3 V sources (3.3−2.3)/2.2k = **0.45 mA**, inside any IO clamp |
| `R_HDR_G` header shunt to GND | **3.3 kΩ** | Divider ratio (2.2+3.3)/3.3 = **2.5**. Also the pull-down that makes an UNCONNECTED header read 0 V = antenna mode. Loading on a 1.8 V driver: 1.8/5.5 kΩ = 0.33 mA |
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
| N1 | SMA→SMP adapter and SMP mated-pair insertion loss (rows 1,2,13,14) | **[EST] 0.05/0.15–0.20 dB each.** Neither vendor publishes an insertion-loss figure. What IS cited: `SMP-MSLD-PCE-5T` VSWR **1.11 max over DC–6 GHz** (RL 26 dB) and DC–26.5 GHz band, so the SMP interface is well inside band with margin. §3.6 shows the 22 dB build survives a 2× error on this whole group |
| N2 | AD9363 RX absolute-maximum input, +2.5 dBm | **SECONDARY SOURCE.** §6.1. Does not block: 22.7 dB of margin |
| N3 | 50 Ω / 90 Ω trace widths | closed-form, not a field solve. **Re-confirm against JLCPCB's calculator for the ordered stackup** before release |
| N4 | Routed lengths (§2) | design targets, not measurements. Re-run §3.3/§3.4 after placement |
| N5 | BGS12WN6 board-level IL/RL | **does not exist.** Infineon publishes prober-station numbers only (Table 4 fn 1). Any board-level figure is an estimate |
| N6 | RF axis height above the Pluto PCB | **not established**, must be measured on a physical unit. Gates mechanics only, no RF number here depends on it |
