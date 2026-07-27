---
id: 0004
date: 2026-07-27
status: superseded-by-0016
tags: [topology]
---
# 0004 — 22 dB of pad, SPLIT 10 dB pre-split + 12 dB per arm, as YAT chips

## Context

BRIEF A2 fact-locks **30 dB TOTAL, TX → each RX**, and BRIEF D2 requires the
pad to be derived from MEASURED splitter and switch losses rather than
assumed. Two questions follow that the brief does not answer: **what value**,
and **where**.

The chain carries 6.54 dB of non-pad loss at 70 MHz and 9.63 dB at 6 GHz
(DETAIL_DESIGN §3) — **3.09 dB of irreducible tilt** — so no single pad makes
30 dB true at both ends.

## Options

### Value

- **Reference the 30 dB to 70 MHz or to the band's geometric mean (648 MHz).**
  Pad 23.5 / 23.1 dB → totals 29.4 dB @70 MHz, 32.5 dB @6 GHz.
- **Reference it to 6 GHz.** Pad 20.4 dB → 26.5 / 29.6 dB. Guarantees ≥30 dB
  nowhere and undershoots most of the band.
- **MINIMAX — the value minimizing the worst-case deviation from 30 dB.**
  `P = 30 − (6.54 + 9.63)/2 = 21.92 dB`. CHOSEN, as **D5**, because the user
  has not named a reference frequency and minimax privileges none.

### Placement

- **One pad ahead of the split.** The obvious build, and the sourcing spike's
  recommendation, on three arguments: brief D4 wants the two runs identical by
  construction and a shared pad cannot introduce branch imbalance; the TX
  port's return loss becomes the pad's; half the parts.
- **Split: some ahead, the rest in each arm.** CHOSEN.

### Technology

- **Mini-Circuits YAT chips** (MCLP 2×2, case MC1630, DC–18 GHz, absorptive).
- **Discrete 0402 pi pads.**

## Decision

**`A1 = YAT-10A+` before the split; `A2 = YAT-10A+ + YAT-2A+` in EACH arm.
Total 21.90 dB at 70 MHz falling to 21.74 dB at 6 GHz** (MEASURED typical
performance — the pad itself contributes only 0.16 dB of the chain's 3.09 dB
tilt). 30 dB is met at **≈3.0 GHz**, with a band span of
**30.0 −1.6 / +1.4 dB** and a guaranteed unit-to-unit envelope of
**27.2 – 32.9 dB**.

### Why the arm pads, against the pre-split argument — four reasons

1. **Isolation.** `isolation(RX1↔RX2) = 6.02 + 2·A2` — attenuation after the
   split counts twice, because a reflection off one RX port traverses that
   arm's pad twice while the wanted signal traverses it once. 6.02 dB with no
   arm pad; **29.8 dB with 12 dB arms.** At a realistic 10 dB RX return loss,
   that is the difference between −16.0 dBc of contamination (**±1.4 dB and
   ±9.0° of ripple versus frequency**) and −39.8 dBc (±0.09 dB, ±0.6°).
2. **An unplugged RX cable corrupts the OTHER channel, silently.** With one
   arm open, the delta gives Zin = 83.3 Ω and the surviving RX receives
   **+3.52 dB** more, with no error indication anywhere on the board. Arm pads
   mask the open by 2·A2 = 24 dB and the error falls to ~0.2 dB. On a bench
   adapter whose only product is amplitude accuracy, a loose SMA must not
   produce a confidently wrong answer.
3. **In ANTENNA mode the splitter presents an OPEN to TX.** Both switches are
   reflective, so with no arm pad both splitter arms face shorts, the delta's
   node equations give Iin = 0, **Zin = ∞ and Γ = +1** — a Pluto PA driven in
   antenna mode sees full reflection. With 12 dB arms the arm reflection
   reaching the splitter is |Γ| = 0.063. **The arm pads are what make it safe
   to transmit in antenna mode at all.**
4. **The leakage is NON-STATIONARY.** The AD936x RX input match moves with the
   internal LNA/attenuator gain index, so the reflection at RX1/RX2 changes as
   the AGC moves. A term that moves with gain cannot be calibrated out. This
   kills the "we'll calibrate the 6 dB isolation away" escape.

Only (1) was costed by the pre-split argument. (2), (3) and (4) were not
costed at all, and each is sufficient on its own.

**The pre-split argument's real content is (b): the TX port's return loss.**
That survives — A1 is still ahead of the split, so TX-port match is set by
PAD_A1 (VSWR 1.03–1.14 measured, 23.6–36 dB) with splitter and switch mismatch buried under
2×10 = 20 dB of round trip. Splitting keeps most of that benefit.

**What it costs:** two independent pad chains can differ. Worst case on the
datasheet windows is |A2a − A2b| ≤ **1.6 dB** (DC–5 GHz) / **1.9 dB**
(5–15 GHz); typical is far smaller and no unit-to-unit σ is published. That
imbalance is STATIC and MEASURABLE, which is exactly what brief D4 already
obliges the release to publish (ADR-0011). **A known imbalance is benign;
unknown, gain-dependent cross-coupling is not.**

### Why chips, on FLATNESS

| | tilt 70 MHz→6 GHz | 6 GHz spread | cost |
|---|---|---|---|
| YAT cascade | **0.16 dB** (MEASURED typical-performance tables, YAT-10A+ REV B p.4 + YAT-2A+ REV B p.4, both vendored in `02_parts/`) | 20.7–23.1 dB, a datasheet-GUARANTEED window | ~$17/board |
| 2× 11.5 dB 0402 pi | 0.56 dB modelled | 21.3–22.7 dB, an UNKNOWN set by ground-via inductance the fab does not guarantee | ~$0.06 |
| single 23 dB 0402 pi | **2.14 dB** | 18.1–22.0 dB | ~$0.03 |

Note honestly: **the chip's guaranteed window (±1.15 dB) is WIDER than the
discrete's modelled spread (±0.7 dB).** The chip does not win on spread. It
wins on **flatness** — 0.16 dB against 0.56 dB — which is the property a swept
calibration reference actually sells.

The single 23 dB pi collapses for a reason worth recording: it needs a 348 Ω
series element, and an 0402's own end-to-end parasitic capacitance (~0.05 pF)
is ~530 Ω at 6 GHz. **The resistor is half-shorted by its own package.** That
is why the arm pads are built as 10 + 2 rather than as one 12.

## Consequences

- **~$17 of silicon per board** (5 MCLP chips at ~$3.4). On a board whose
  other RF parts total ~$1, this is the dominant BOM line. It is the correct
  trade for a CALIBRATION reference, whose product is a known number.
- **Stock ceiling.** YAT-10A+ C5839318 = 150 pieces (3/board ⇒ 50 boards);
  YAT-2A+ C5205333 = 103 (2/board ⇒ 51 boards). Both JLC **Extended**.
  Deliberately NOT `YAT-20A+` (C5181338), whose 37 pieces would cap the build
  at 37 boards and is the sourcing spike's largest single risk.
- **D5 is a one-BOM-line lever.** If the user names a reference frequency, only
  the arm chain's SECOND part changes — same footprint, two placements:
  70 MHz/648 MHz ⇒ YAT-3A+; 3.0 GHz ⇒ YAT-2A+ (chosen); 6 GHz ⇒ omit it.
- **Layout obligations, all load-bearing** (YAT-20A+ p.3, "SUGGESTED PCB
  LAYOUT (PL-586)", and p.2 footnote 1): the published flatness and VSWR are
  **grounded-coplanar-waveguide** numbers measured on Mini-Circuits' own test
  board. The drawing's 0.011″/0.008″ geometry is conditioned on 0.168 mm
  RO4350B and **must be re-solved for the JLC FR4 stackup** — copying it is
  wrong. Continuous ground plane directly under the part; dense ground
  stitching; land pattern free of solder mask; and **the exposed pad is the RF
  GROUND RETURN, not a thermal pad** (abs-max note 3: "Case is defined as
  ground lead") — tenting it breaks the return path.
- **A PL-586 deviation waiver is REQUIRED and must cover the four 0.30 mm GND
  lands, not just the exposed pad.** The drawing calls 31× Ø0.2 mm
  epoxy-plugged vias, of which ~4 are in the EP and the rest sit in the GND
  lands and the perimeter. A 0.2 mm drill needs ~0.45–0.5 mm of finished pad
  at JLC — **wider than the 0.30 mm land itself**, so via-in-pad there is
  geometrically impossible at any tier. The waiver carries the measured via
  count and the reason.
- **Land pattern is MEASURED, not inferred**: MC1630 (drawing 98-MC Rev. H,
  03/05/18, sheet 1 of 5) gives pad pitch **0.65 mm**, land **0.30 × 0.80 mm**,
  exposed pad **1.20 × 0.60 mm** (land ≈1.25 × 0.65 with a 0.30 mm 45°
  chamfer as the pin-1 index), suggested-layout tolerance ±0.05 mm. Do NOT
  infer a pitch from the 2 × 2 mm body size. Escape is trivial and
  condition-free: only pads 2 (RF-IN) and 5 (RF-OUT) are signal, centre of
  opposite rows, straight through.
- **Guaranteed TX-port return loss at 6 GHz is 11.7 dB, not 20 dB.** 6 GHz sits
  in the 5–15 GHz band, where YAT-10A+'s max VSWR is **1.70** (REV B p.2) — the
  1.25 max (19.1 dB) belongs to DC–5 GHz. Measured typ there is 1.03–1.09
  (27–36 dB), so practice is excellent, but the GUARANTEED form of the "the pad
  sets the TX port match" benefit is 11.7 dB. (The sourcing spike quoted 14 dB
  for the YAT-20A+, reading the DC–5 GHz max against a 6 GHz question; that
  part is not used here and its 5–15 GHz max is 2.0, i.e. 9.5 dB.)
- **Immune to the CPL-180 defect** that produced this repo's interposer v1.0
  DO-NOT-ORDER: a 180° rotation maps pad 2 ↔ pad 5 and the GND pads onto each
  other, and the pad is a symmetric bidirectional 2-port, so the board still
  functions. Rotation must still be right for index-dot/AOI.
- **Discrete fallback is fully specified** and carries zero stock risk: each
  11.5 dB pi is 3× 86.6 Ω 0402 1 % (E96 rounds 86.25/87.31/86.25 to one
  value); stock verified C158969 (5202), C227253 (4450), C830266 (1038).
  Taking it costs 0.5 dB of flatness and an unbounded 6 GHz value.
- **RE-DERIVE AFTER ROUTING.** The pad value rests on estimated interconnect
  loss. If measured total interconnect at 6 GHz lands below ~1.4 dB, the arm's
  second part changes. DETAIL_DESIGN §3.6 sizes the sensitivity: the 22 dB
  build survives any single estimate being wrong by 2×.

## Superseded — 2026-07-27, by ADR-0016 (user directive A9)

**HALF of this ADR is superseded and half is CARRIED FORWARD UNCHANGED, so
read the split carefully.**

**SUPERSEDED — the VALUE and its selection rule.** The user raised the total to
40 dB and specified it as a MINIMUM across the band rather than a scalar at a
reference frequency. `PAD_A1` goes **10 dB → 25.78 dB**
(`2 × YAT-10A+ + 3 × YAT-2A+`), the path total goes 21.9 → **37.7 dB typical**
with a guaranteed minimum of **≥40.07 dB TX → each RX** including the split.
Minimax, the ≈3.0 GHz reference, the 30.0 −1.6/+1.4 dB span and the
27.2–32.9 dB envelope all go with it (ADR-0013's supersession).

**CARRIED FORWARD — the PLACEMENT argument, in full.** `PAD_A2` stays at 12 dB
in EACH ARM, and the four reasons above are the reason it stays. Its value was
never set by the total: it is pinned independently by inter-channel isolation
(`6.02 + 2·A2` = 29.9 dB), by masking an unplugged RX cable (2·A2 = 24 dB of
round trip turning a silent +3.52 dB error into ~0.2 dB), by what the splitter
presents to TX in antenna mode (|Γ| = 0.063 instead of Γ = +1), and by the
AD936x RX match moving with the AGC index so the leakage is non-stationary and
uncalibratable. **The whole 18 dB increase went PRE-SPLIT** precisely so that
none of those three numbers moved.

Also carried forward unchanged: chips-over-discrete on FLATNESS (0.16 dB vs
0.56 dB, and the honest note that the chip's guaranteed window is WIDER than
the discrete's modelled spread); the MC1630 land pattern read from drawing
98-MC Rev. H; the PL-586 deviation waiver covering the four 0.30 mm GND lands;
the exposed pad being the RF GROUND RETURN and not a thermal pad; and the
CPL-180 immunity note.

**One consequence of the increase that ADR-0016 costs explicitly:** PAD_A1 is
now a FIVE-chip cascade, so ~12 mm of extra interconnect (0.43 dB at 6 GHz) and
four more mounting discontinuities enter the budget, and the binding stock
ceiling moves from YAT-10A+ (150 pcs, 4/board = 37 boards) to YAT-2A+ (103 pcs,
5/board = **20 boards**). A stock query on the mid-value YAT parts — which
would collapse the cascade to two chips — is recorded as OWED rather than
assumed, because **a guaranteed-minimum claim may not rest on an unverified
datasheet min column.**
