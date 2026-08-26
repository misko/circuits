---
id: 0016
date: 2026-07-27
status: accepted
tags: [topology, spec-tension]
---
# 0016 — 40 dB, specified as a MINIMUM across the band, sized against TX MAXIMUM

## Context

The user raised the cal-path attenuation from 30 dB to **40 dB** and changed
what kind of number it is. Recorded as **A9** in `BRIEF.md`. **The number is
not the decision — the reasoning is, and it is recorded here because the
reasoning is what makes the number re-derivable.**

**1. The fixed pad is not there to set the operating level.** The AD936x TX
attenuator gives ~90 dB of software control in 0.25 dB steps. Anyone who wants
a particular RX level asks for it in software. **The pad exists to survive a
MISCONFIGURATION** — full TX power commanded while the cal path is engaged —
so it is sized against TX **maximum**, never TX intended. A pad chosen to hit a
nice operating level is a pad chosen against the wrong quantity.

**2. Bare survival is 4.5 dB.** TX max ≈ +7 dBm as the brief carried it (now
**+8 dBm, cited** — see below), RX absolute max **+2.5 dBm**. 30 dB bought
25.5 dB of margin; **40 dB buys 35.5 dB.**

**3. The extra 10 dB is free.** Thermal floor at NF 5 dB is −109 dBm in 1 MHz.
RX at −33 dBm still has **~76 dB of SNR** — far beyond what phase calibration
needs, and beyond what the AD936x's 12-bit converter chain delivers anyway
(~65–70 dB in-band).

**4. The failure modes are ASYMMETRIC.** Too much pad costs SNR, and SNR is
recoverable by averaging longer (10·log₁₀N, free, offline). Too little pad
destroys the receiver, permanently, and takes the user's SDR with it. **When
one side is recoverable and the other is not, buy margin.**

**5. Specify the MINIMUM across 70 MHz – 6 GHz, not a midpoint.** The chain
loses least at 70 MHz, so that is where the receiver sees the most power and
where the ≥40 dB has to hold. This is not a stylistic change: it makes the
requirement *satisfiable* and *checkable*, which the scalar was not (ADR-0013),
and it makes the answer robust in the safe direction — every loss term this
design cannot control can only ADD.

## Options

### How much

- **Keep 30 dB.** 25.5 dB of survival margin against a +7 dBm TX. Adequate
  until you ask what happens at the board's own declared abuse ceiling — see
  Consequences, where 30 dB leaves **2.7 dB**.
- **40 dB.** CHOSEN (A9).
- **More than 40 dB.** Rejected on SNR: at 6 GHz the worst-case unit is already
  at 63 dB SNR in 1 MHz, and another 10 dB starts to cost real averaging time
  for no survival benefit that matters.

### What kind of number

- **A scalar at a nominated reference frequency** (ADR-0013's minimax, D5).
  REJECTED, by reframing rather than by answering — see below.
- **A typical-curve minimum**: the ≥40 dB holds on the measured typical curve,
  with the unit-to-unit envelope published beside it. This is what ADR-0013
  did for 30 dB. It would let the build be one YAT-2A+ cheaper.
- **A GUARANTEED minimum**: ≥40 dB holds for the WORST-CASE unit at the WORST
  frequency, using the datasheet min column. CHOSEN. A survival spec that is
  only typically true is not a survival spec, and reason (4) above — the user's
  own — says which way to err. The cost of the stronger reading is **one $3.40
  chip**.

### Where the extra 18 dB goes

- **All in the arms.** REJECTED: two parts per 1 dB instead of one, and it
  pushes RX1↔RX2 isolation far past where it does any good.
- **All pre-split.** CHOSEN. *One part protects both arms*, and it protects
  them against the failure the pad exists for — a pre-split pad is upstream of
  every downstream fault, including a splitter fault.
- **Arm pads unchanged at 12 dB.** CHOSEN. Their value was never set by the
  total: ADR-0004's four reasons fix `A2` from isolation
  (`6.02 + 2·A2 = 29.9 dB`), from masking an unplugged RX cable (24 dB of
  round trip, +3.52 dB error → ~0.2 dB), and from what the splitter sees in
  antenna mode (|Γ| = 0.063 instead of +1). Raising the total must not disturb
  a number that three independent arguments already pinned.

## Decision

**TX_PLUTO → each RX_PLUTO attenuates ≥ 40 dB, MINIMUM across 70 MHz – 6 GHz,
worst-case unit, with the user's cables credited at ZERO.**

Realized as:

| element | build | typ @70 MHz | typ @6 GHz |
|---|---|---|---|
| **PAD_A1**, pre-split | `2 × YAT-10A+ + 3 × YAT-2A+` | 25.78 dB | 25.37 dB |
| **PAD_A2**, in EACH arm (unchanged) | `YAT-10A+ + YAT-2A+` | 11.92 dB | 11.78 dB |
| **pad in the TX→RX path** | 3 × YAT-10A+ + 4 × YAT-2A+ | **37.70 dB** | **37.14 dB** |

PAD_A1 goes 10 dB → 25.78 dB; PAD_A2 is untouched.

### The minimum, and exactly what it rests on

| | 70 MHz – 5 GHz | 5 – 6 GHz |
|---|---|---|
| pad, datasheet **min** column | 3(9.6) + 4(1.5) = **34.8** | 3(9.5) + 4(1.4) = **34.1** |
| resistive delta split, worst case on ±1 % parts | **5.97** | **5.97** |
| **guaranteed minimum TX → each RX** | **40.77 dB** | **40.07 dB** |

**≥ 40.07 dB, worst frequency 6 GHz.** Every other element in the chain — both
cables, all four coax interfaces, 65 mm of microstrip, the SPDT, the splitter's
mounting parasitics — is strictly positive and is credited at **zero** in that
figure. The guarantee rides on two things only: **a datasheet minimum column**
and **a theorem** (the 6.02 dB of a matched resistive 3-port, proved three ways
in DETAIL_DESIGN §5.3). Credit only the terms the geometry forces (≥25 mm of
trace = 0.9 dB at 6 GHz, SPDT IL ≥0.2 dB) and it is **≥41.2 dB**.

**The typical curve is 44.6 dB at 70 MHz rising to 50.2 dB at 6 GHz**, and the
guaranteed envelope across band *and* unit-to-unit is **40.1 – 53.7 dB**. The
release publishes the curve; ADR-0013's rule that a number known to be a curve
must ship as a curve is unchanged and now applies to a floor instead of a
target.

### D5 is RESOLVED — by reframing, not by answering

ADR-0013 asked the user to nominate the frequency at which "30 dB" should be
exact, because a 3.09 dB tilt made the scalar unsatisfiable, and chose minimax
in their absence. **A9 makes the question disappear.** A minimum needs no
reference frequency: it is met where the chain loses least, and it is met by
construction everywhere else.

Two things follow, and both are worth stating because they are the reason the
reframing is not a dodge:

- **The tilt stops mattering for SAFETY.** Only the low end of the band binds,
  and every dB of tilt is a dB of extra margin at the top. The tilt got *worse*
  under A8 — two SMA cables took it from 3.09 dB to **6.13 dB** (ADR-0015) —
  and the specification absorbed that without changing.
- **The tilt never mattered for ACCURACY.** This is a calibration fixture: its
  response is **measured and published**, not assumed. A user offsets against
  the published curve. A flat pad would be convenient; it was never a
  requirement, and ADR-0013's minimax was solving a presentation problem, not
  an engineering one.

### Confirmed: BOTH pads sit UPSTREAM of BOTH switches

Asked explicitly, because if it were the other way round the topology would
matter more than the dB value.

```
TX_PLUTO ──► PAD_A1 (25.8 dB) ──► resistive delta split (6.02 dB) ──┬──► PAD_A2a (11.9) ──► SW1.RF2 ─┐
                                                                     │                       SW1.RFin ├──► RX_PLUTO1
                                                     RX_ANT1 ────────────────────────────►   SW1.RF1 ─┘
                                                                     └──► PAD_A2b (11.9) ──► SW2.RF2 ─┐
                                                                                             SW2.RFin ├──► RX_PLUTO2
                                                     RX_ANT2 ────────────────────────────►   SW2.RF1 ─┘
```

`TX_PLUTO` touches exactly one thing: PAD_A1's input. **The complete pad chain
— A1, the split, and A2 — lies between the TX port and either switch.** So:

- **No switch STATE can present raw TX to an RX port.** The antenna throw
  (RF1) carries no TX at all; the loopback throw (RF2) carries TX through the
  full 37.7 dB.
- **No switch FAILURE can either.** A stuck throw leaves the full chain in
  circuit. A destroyed die that shorts RFin–RF1–RF2 together *still* has the
  full chain in circuit, because the pads are not downstream of it. The worst
  a switch fault can do is deliver the attenuated signal to the wrong place.
- **The minimum attenuation from TX to RX over EVERY switch state and every
  switch fault is the same ≥40.07 dB.** The switch's own isolation (43 dB at
  70 MHz, 20 dB at 6 GHz) sits *on top of* that in antenna mode and is not
  counted.

This is not luck: ADR-0004 put A2 *in the arm*, i.e. between the splitter and
the switch, on four arguments that had nothing to do with fault protection.
The property was bought and paid for; it had simply never been stated.

**The counterpart, stated so it is not mistaken for coverage: the ANTENNA path
has no pad at all** (`RX_ANT → DC block → SW.RF1 → RFin → RX_PLUTO`, ≈0.3 dB).
A user who connects a transmitter to an antenna port reaches the Pluto's
receiver essentially unattenuated. That is what an antenna port IS, it is
outside the two states the brief specifies, and ADR-0009's input-protection
posture is what covers it. **40 dB protects the CAL path; nothing protects the
antenna path, by construction.**

## Consequences

- **The TX number this is sized against is now CITED, and it is higher than the
  brief carried.** `+7 dBm` was a typical figure with no primary source. The
  AD9363 data sheet Rev. D, printed p.4 of 32, gives **Maximum Output Power
  8 dBm at 800 MHz** (7.5 at 2.4 GHz, 7.0 at 3.5 GHz), *"1 MHz tone into 50 Ω
  load"* — **so "≈+7 dBm" was the WORST of the three characterized bands being
  carried as if it were the ceiling.** The user's own suspicion ("some bands
  run hotter") was correct, by 1 dB. **40 dB absorbs it without a change:**
  worst case RX = 8 − 40.07 = **−32.1 dBm**, margin to the +2.5 dBm rating
  **34.6 dB**. Both figures now live in `spf/plutoplus_hardware/` and are
  consumed through `mates.yaml`, graded, instead of sitting in prose.
- **The RX number is CITED too, and the secondary source was right.** AD9363
  Rev. D, ABSOLUTE MAXIMUM RATINGS, printed p.15 of 32: `RF Inputs (Peak
  Power) — 2.5 dBm`. **Note what the row actually says: PEAK power.** For the
  CW cal tone peak = average and it costs nothing; for a modulated stimulus it
  would not, and that is now on the record. The same table's
  `Tx Monitor Input Power (Peak Power) 9 dBm` is a DIFFERENT port and must not
  be read as the RX limit.
- **THE STRONGEST ARGUMENT FOR 40 dB IS NOT THE ONE THAT MOTIVATED IT.** This
  board declares its own TX abuse ceiling at **+27 dBm** (DETAIL_DESIGN §4.3),
  the level an external PA on TX may reach before PAD_A1 is endangered. Check
  the receiver at that ceiling:

  | pad | guaranteed min TX→RX | RX at TX = +27 dBm | margin to +2.5 dBm |
  |---|---|---|---|
  | 30 dB build (ADR-0004/0013) | 27.2 dB | **−0.2 dBm** | **2.7 dB** |
  | **40 dB build (this ADR)** | **40.07 dB** | **−13.1 dBm** | **15.6 dB** |

  **The old design's declared board ceiling protected the BOARD's parts and
  left the user's RECEIVER 2.7 dB from destruction.** Two ratings were being
  read against different victims and nobody had put them in the same table.
  40 dB is what makes the +27 dBm ceiling honest.
- **SNR, measured rather than asserted.** Thermal floor at NF 5 dB: −109 dBm in
  1 MHz, −96 dBm in 20 MHz. Typical RX level −36.6 dBm at 70 MHz / −42.2 dBm
  at 6 GHz ⇒ **72 dB / 67 dB of SNR in 1 MHz**; worst-case unit at 6 GHz
  (53.7 dB total) ⇒ 63 dB. In a 20 MHz span the top of the band lands at
  50–54 dB, i.e. **below** the converter chain's ~65–70 dB, so the measurement
  goes from converter-limited to noise-limited at the top of the band in wide
  bandwidth. That is exactly the recoverable side of the asymmetry: 16×
  averaging returns 12 dB, offline, free.
- **Cost and stock — the real price of the decision.** Nine YAT chips per board
  instead of five: **4 × YAT-10A+ and 5 × YAT-2A+ ≈ $30.6**, up from ~$17. The
  stock ceiling MOVES: YAT-2A+ (C5205333, 103 pcs) at 5/board caps the build at
  **20 boards**, taking over from YAT-10A+ (C5839318, 150 pcs) at 4/board = 37
  boards. Against a `build_quantity: 5` that is comfortable, but the binding
  line changed and `assembly.yaml` says so.
- **OWED, and cheap: a stock query on the mid-value YAT parts.** A single
  15 dB or 12 dB chip would collapse PAD_A1 from five parts to two, saving ~$7
  and 12 mm of interconnect. Only YAT-10A+, YAT-2A+ and YAT-20A+ (37 pcs — the
  sourcing spike's largest risk, deliberately unused) have verified stock on
  this board, so the five-chip cascade is what the VERIFIED parts allow.
  **YAT-12A+ / YAT-15A+ / YAT-5A+ / YAT-3A+ are not stock-checked, and a
  guaranteed-minimum claim may not be built on an unverified min column.** The
  query is one API call at seal time; the build only gets simpler.
- **A new row in the loss budget, because five chips in series is not free.**
  PAD_A1's internal cascade adds ~12 mm of microstrip (4 × 3 mm between chips)
  = 0.02 dB at 70 MHz, **0.43 dB at 6 GHz**, and four more mounting-parasitic
  discontinuities. It is budgeted (DETAIL_DESIGN §3.1 row 5b) rather than
  waved away, and it pushes in the safe direction for a minimum.
- **Isolation, the open-cable error and the antenna-mode reflection are all
  UNCHANGED**, because A2 is unchanged: RX1↔RX2 = 6.02 + 2(11.92) = **29.9 dB**,
  open-port error ~0.2 dB, |Γ| = 0.063 into the splitter in antenna mode. This
  is the point of putting the increase pre-split: it buys survival margin
  without touching three properties that were separately argued.
- **Power dissipation is a non-event and the board ceiling does not move.** At
  the cited +8 dBm TX, PAD_A1's first chip takes 6.3 mW against a 1.7 W rating
  (24.3 dB). The binding element for the board's abuse ceiling is still that
  same first chip at +32.3 dBm, so **TX ≤ +27 dBm** stands with its 5.3 dB
  guard band.
- **The assembly-fault ladder gets safer at every rung.** All arm pads missing
  ⇒ RX = −24.7 dBm (27 dB of margin). All of PAD_A1 missing (five separate
  parts) ⇒ −10.8 dBm (13.3 dB). *Every* pad missing ⇒ +1.1 dBm — still below
  the +2.5 dBm absolute maximum, though above the front end's ~0 dBm P1dB, so
  even the absurd case is a wrong measurement rather than a dead radio.
- **ADR-0004 and ADR-0013 are superseded by this ADR**, and each keeps its
  reasoning: ADR-0004's placement argument is carried forward verbatim in
  substance (only the VALUE of A1 changes), and ADR-0013's "a number known to
  be a curve ships as a curve" survives as the rule that makes the published
  minimum meaningful.
- **RE-DERIVE AFTER ROUTING is UNCHANGED as an obligation but no longer as a
  RISK.** The old 22 dB build was sized by minimax against estimated
  interconnect loss, so an estimate being wrong moved the pad. A minimum
  credited at zero interconnect cannot be invalidated by interconnect being
  smaller than budgeted — there is nothing below zero. The re-derivation now
  only sharpens the published typical curve.
