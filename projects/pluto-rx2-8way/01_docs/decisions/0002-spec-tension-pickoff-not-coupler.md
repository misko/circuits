---
id: 0002
date: 2026-07-28
status: accepted
tags: [spec-tension, topology, rf]
---
# 0002 — The RX1 tap is a SPLIT-ARM RESISTIVE PICKOFF; the directional coupler is refuted twice

## Context

BRIEF Q3/A3: asked how to tap the RX1 antenna for pole 8, the user answered
**"directional coupler (−10 dB)"**. D-SPEC flagged that as spec tension **T2**
and recorded D3 as PROPOSED, because reversing a user's own answer needs the
user's own confirmation. **That confirmation has now been given, with a
variant: the arm is SPLIT into two 220 Ω resistors.** This ADR records the
refutation, the adopted circuit, the arithmetic behind every published number,
and one consequence nobody had computed — which is why it also carries a NEW
spec tension, **T3**.

## Options

### (a) A 70 MHz – 6 GHz directional coupler — REFUTED, on two independent grounds

1. **It does not exist, and the reason is structural.** 6000/70 = **85.7 : 1**.
   A coupled-line coupler's coupling factor is set by an electrical LENGTH
   (a quarter wave at the design centre); below its band it rolls off at
   **6 dB/octave**. 85.7 : 1 is 6.4 octaves, so a coupler flat at 6 GHz is
   ≈38 dB weaker at 70 MHz. Multi-section and transformer-coupled
   (ferrite) parts extend the ratio at the cost of the top end; nothing
   stocked spans both ends of THIS band with a specified coupling factor.
2. **Directionality is not the property being bought — and this is the
   deeper objection.** A directional coupler's function is to SEPARATE a
   forward wave from a reverse wave. **A receive antenna has one wave
   direction.** There is nothing to separate. The user's actual goal, stated
   in the same breath, was *do not cost RX1 its sensitivity* — and that is a
   question about INSERTION LOSS, which a two-resistor network answers
   better than a coupler and across the whole band.

   The failure mode this refutation names is general and recurs later in
   this design (ADR-0004): **an 85.7 : 1 band kills every solution whose
   mechanism is an electrical length.** A shunt ESD stub dies the same way.

### (b) A resistive SPLITTER (the matched 6 dB Y, 3 × 16.67 Ω) — REJECTED

Matched on all three ports and perfectly flat, but it costs RX1 **6.02 dB**
of sensitivity, permanently, on the board's only continuously-connected
receive path. Sensitivity lost at the antenna is not recoverable downstream.

### (c) A resistive PICKOFF, single 470 Ω arm — REJECTED as the primary (kept as the alternate)

`02_parts/0402WGF4700TCE/` remains as a dossier and is now labelled the
REJECTED ALTERNATE. Its numbers are correct; it loses on FLATNESS SPREAD —
see the table under Decision.

### (d) A resistive PICKOFF, SPLIT arm: 2 × 220 Ω in series — **CHOSEN** (user-confirmed)

## Decision

**One node, three ports.** The RX1 antenna jack, the RX1-out jack and the
series arm all meet at a single node (net `RX1_MAIN`). The arm is
`R_T1` (220 Ω) → `RX1_TAP_MID` → `R_T2` (220 Ω) → `RX1_TAP` → U1 pin 19
(RF8). Both resistors are **0402WGF2200TCE, LCSC C25091, JLC Basic**.

### The three formulas, re-derived from the circuit rather than checked

With `Z0 = 50 Ω`, arm resistance `Rs`, and `Rp = Rs + Z0` (the arm plus the
tap port's own termination):

| quantity | expression | at Rs = 440 Ω |
|---|---|---|
| main-line insertion loss, antenna → RX1 out | `20·log10(1 + Z0/(2·Rp))` | **0.4324 dB** |
| tap level, **relative to the RX1 output port** | `20·log10(Z0/Rp)` | **−19.825 dB** |
| tap level, **relative to a PLAIN antenna port** (= tap + IL) | | **−20.257 dB** |
| return loss at the antenna port | `Zin = Z0 ∥ Rp = 45.37 Ω` | **26.28 dB** (VSWR 1.104) |

**Both tap definitions are published because they answer different
questions**, and quoting one where the other is meant is a 0.43 dB error:
−19.83 dB is what RX1 and RX2 see relative to EACH OTHER; −20.26 dB is what
element 8 delivers to the switch relative to elements 1–7. The SIR
arithmetic below uses the second.

### The "flat DC–6 GHz" claim in the BRIEF is WITHDRAWN, and here is the tilt

An 0402 chip resistor has a shunt parasitic across its body. **Vishay
technical note 60107, Table 1, page 1** gives an 0402 wrap-around chip
`C = 0.0392 pF`, `L = 0.1209 nH`. **That figure is CITED for the 0402
wrap-around CLASS and ESTIMATED for this thick-film part**, which publishes
no HF data of any kind: call it **0.04 ± 0.02 pF**, and note that the tilt
below scales essentially linearly with it.

Modelling the arm as `Z_arm = R/(1 + jωRC)` and re-evaluating the tap:

| f | single 470 Ω (C = 0.0392 pF) | **split 2 × 220 Ω (C_eff = 0.0196 pF)** |
|---|---|---|
| DC | −20.341 dB | **−19.825 dB** |
| 1 GHz | −20.285 (+0.056) | **−19.812 (+0.013)** |
| 2 GHz | −20.116 (+0.225) | **−19.775 (+0.050)** |
| 3 GHz | −19.851 (+0.490) | **−19.713 (+0.112)** |
| 4 GHz | −19.505 (+0.836) | **−19.628 (+0.197)** |
| **6 GHz** | **−18.650 (+1.691)** | **−19.394 (+0.431)** |

Two resistors in series put their parasitics in SERIES, halving the
effective shunt C. **The 6 GHz tilt falls from 1.69 dB to 0.43 dB — 3.9×.**

**But the nominal tilt is not the number that justifies the second
resistor.** A known tilt calibrates out; what cannot be calibrated before it
is measured is the SPREAD, and the spread is what the ± 0.02 pF bar buys:

| arm | 6 GHz tilt at C_nom | at the bar's ends | **width of the unknown** |
|---|---|---|---|
| single 470 Ω | +1.691 dB | +0.509 … +3.240 dB | **2.73 dB** |
| **split 2 × 220 Ω** | **+0.431 dB** | **+0.117 … +0.950 dB** | **0.83 dB** |

**The second 0402 buys a 3.3× reduction in what remains UNKNOWN**, and that
is the property this board sells (ADR-0006: the path table is a measured,
published artifact — a narrow prior is worth more than a good typical).

**The main line is essentially unaffected**, which is the half that costs RX1
sensitivity: 0.4324 dB at DC → **0.4373 dB at 6 GHz** (+0.005 dB), return
loss 26.28 → 25.84 dB.

### T3 — a NEW spec tension found here: the reference dwell is LEAKAGE-limited

Nobody had computed what the deep tap does to the reference dwell's
signal-to-interference ratio, because T2 optimised only RX1's sensitivity.
The cost function has a second term.

On the reference dwell, RF8 is selected and carries the TAPPED copy of
element 8 (−20.26 dB), while the seven live antennas leak into RFC at full
strength through the switch's finite isolation. Power-summing the seven
leakers from the **guaranteed-minimum** isolation column (Table 3, PDF p5)
and using the RF8 insertion-loss **max** column (PDF p4):

| band | Σ leakage | wanted (tap + IL) | **reference-dwell SIR** | worst-case Δφ |
|---|---|---|---|---|
| 10–100 MHz | −55.8 dB | −21.16 dB | **+34.7 dB** | 1.1° |
| 100 MHz–1 GHz | −41.5 dB | −21.26 dB | **+20.2 dB** | 5.6° |
| 1–2 GHz | −35.9 dB | −21.46 dB | **+14.4 dB** | 11.0° |
| 2–4 GHz | −29.6 dB | −21.76 dB | **+7.8 dB** | 23.9° |
| 4–6 GHz | −23.4 dB | −22.16 dB | **+1.2 dB** | 60.1° |

(Δφ = `arcsin(10^(−SIR/20))`, the worst-case phase pull from one coherent
interferer.) For contrast, a NORMAL antenna dwell is **+21.7 dB SIR / 4.75°
at 4–6 GHz** — the number the sourcing spike published. **Only the reference
dwell is compromised, and it is compromised by 20 dB.**

**The tap value is NOT the fix, and that is the finding.** The ceiling is set
by the seven live ports' aggregate isolation, not by the arm:

| arm | tap (vs plain port) | RX1 IL | RL | SIR @4–6 GHz (min iso) |
|---|---|---|---|---|
| 2 × 220 Ω (chosen) | −20.26 dB | 0.432 dB | 26.3 dB | **+1.2 dB** |
| 220 Ω (`R_T2` → 0 Ω) | −15.42 dB | 0.769 dB | 21.4 dB | **+6.1 dB** |
| matched 6 dB split | −6.02 dB | 6.02 dB | ∞ | **+15.5 dB** |
| ideal lossless 3 dB | −3.01 dB | 3.01 dB | ∞ | **+18.5 dB** |

**No tap value reaches 20 dB at the top of the band.** Giving up 5.6 dB of
RX1 sensitivity (the matched split) buys 14.3 dB of reference SIR and still
lands under 16 dB. So the confirmed 2 × 220 Ω is KEPT: it costs 0.43 dB of a
permanent, unrecoverable quantity to give up ~5 dB of a recoverable one.

**What actually fixes it is that the leakage is COMPUTABLE.** On the
reference dwell the interference is `Σ a_k · s_k` where the `a_k` are the
seven port-to-RFC isolation coefficients — **constant** (the switch is
absorptive, so every deselected element sits at ~50 Ω in all eight states)
and **published** (ADR-0006) — and the `s_k` are the very signals the
receiver measures on the other seven dwells of the SAME 2.08 ms frame. This
is P8/A1's "unequal but constant" applied to leakage instead of to path
length, and it costs the board nothing: the obligations are (i) hold the
coefficients constant, which the absorptive switch and the fixed radial
geometry already do; (ii) measure them, which ADR-0005's all-ports-terminated
dark state and the per-dwell data already permit.

**The lever that stays on the board at zero cost:** `R_T2` is a 0402 in a
series arm, so **populating it as 0 Ω instead of 220 Ω is a BOM change with
no board change** and buys +4.84 dB of reference SIR for 0.337 dB of RX1
loss. The decision can therefore be deferred to order day, or to after the
first measurement, at zero cost. **The default build is 2 × 220 Ω, as
confirmed.**

## Consequences

- **BRIEF T2 moves from "ADR owed" to APPLIED; D3 moves from PROPOSED to
  CONFIRMED; a new row T3 is added** and flagged to the user. The
  "flat DC–6 GHz" wording in the original T2 is WITHDRAWN — a claim retracted
  in the record, not quietly edited away.
- **The reference channel is 20.26 dB down, and D1 already pays for it.** The
  reference dwell is 4096 samples = **36.1 dB of coherent processing gain**,
  so thermal noise is not the limit — interference is. For a reference phase
  error ≤ 2° the reference needs post-integration SNR ≥ `1/(2·(2π/180)²)` =
  **26.1 dB**, which the processing gain delivers comfortably wherever T3's
  SIR allows.
- **Three parts, one net topology, and the value is the whole design.** The
  netlist, DRC, ERC and parity are IDENTICAL for any resistor value, so
  nothing on the board can detect a wrong one. Both resistors therefore carry
  a `part_value` invariant (`03_src/rules/electrical_invariants.yaml`) and a
  `part.yaml` `asserts:` entry, and `RX1_TAP_MID` carries a length budget —
  it is the interior of a LUMPED element, not a transmission line, and must
  stay under **λg/20 = 1.37 mm** at 6 GHz for that to remain true.
- **A DC-conductive path now exists from an antenna jack to an RF pin**, and
  PE42482A-X's `V_RFDC` maximum is **0 V** (Table 8 fn 1, PDF p20). The 440 Ω
  arm limits a fault to `V/490` — 10 mA at an accidental 5 V, against 100 mA
  straight into a direct port. That is a mitigation, not a licence: the port
  contract in ADR-0004 governs.
- **Sourcing, measured 2026-07-28 (M-QUOTE):** C25091 is `base` (JLC Basic)
  with **995,162** in the JLCPCB assembly library. Its LCSC RETAIL product
  page reads **stock 0** the same day — two different pools, and the assembly
  pool is the one a PCBA order allocates from. Recorded because the retail
  figure is the one a casual check returns, and it is the wrong instrument
  for this question (canon M-QUOTE: measure the state of the PART, not of a
  catalog record).
- **What must be re-verified if the arm changes:** the published tap table,
  the tilt table, the T3 SIR table, and both `part_value` invariants.
