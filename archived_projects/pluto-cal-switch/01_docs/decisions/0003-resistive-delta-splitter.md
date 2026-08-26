---
id: 0003
date: 2026-07-27
status: accepted
tags: [topology]
---
# 0003 — Resistive DELTA 2-way splitter, not Wilkinson and not a star

## Context

State B feeds one TX into both Pluto RX ports. The band is 70 MHz – 6 GHz —
a **bandwidth ratio of 85.7:1** — and brief D4 requires the two runs to be
symmetric by construction.

BRIEF D1 already argued a Wilkinson is impossible ("λ/4 at 70 MHz is ~400 mm
on FR4") and asked for that to be CONFIRMED or REFUTED against a wideband
MMIC/LTCC alternative. This ADR does that.

## Options

- **Printed Wilkinson.** **REFUTED, twice, independently.**
  (a) *Size*: recomputing properly, a 70.7 Ω microstrip on 1.6 mm FR4
  (εr 4.4) is W ≈ 1.6 mm, W/h ≈ 1.0, so ε_eff = 2.70 + 1.70·13^−0.5 = 3.17,
  λg = 2.405 m and **λg/4 = 601 mm**, not ~400 mm. D1's conclusion was right
  and its number was 50 % optimistic.
  (b) *Bandwidth*: a single-section Wilkinson manages ~1.4:1; published
  multi-section designs top out around 10–20:1 against a requirement of
  85.7:1. Each section is λ/4 at f_gm = √(70×6000) = 648 MHz = 65 mm, so six
  or seven meandered sections plus six or seven isolation resistors would
  consume 400+ mm and STILL fall short. **The second refutation is fatal on
  its own and does not depend on the board being small.**
- **A commercial wideband splitter part.** **NOT SOURCEABLE.** Every 2-way
  splitter LCSC stocks was swept: Mini-Circuits EP2W+ (C3154895) 700 MHz–6 GHz
  is the closest in existence and still misses a full decade at the bottom, at
  $20.86 and 93 in stock; EP2C+ 1800–12500; EP2K+ 5–20 GHz (per its own
  datasheet Rev B p.1 — an LCSC search snippet claiming "5 MHz~10 GHz" was
  refuted against the primary); EP2K1+ 2–26.5 GHz; SP-2G+ 1.42–1.66 GHz;
  SP-2G1+ / BP2G1+ 1.2–2 GHz; the entire 18-model LTCC family (SBA/SBB/SCG/
  SCN) is narrow slices between 600 MHz and 6.5 GHz; ADP-2-20+ core-and-wire
  is 20–2000 MHz and connectorized. **None covers 70 MHz – 6 GHz.**
  The root cause is physics, not sourcing: ferrite/transformer types die above
  ~2–3 GHz, lumped LTCC/GaAs-IPD needs impractical L and C below ~700 MHz, and
  distributed types are λ/4-bound.
- **Resistive STAR / wye, 3× 16.9 Ω.** REJECTED on two counts, both measured.
  Electrically identical in the ideal case, but with the same mounting
  inductance Lp = 0.5 nH at 6 GHz the star's through path crosses TWO chip
  bodies: Zin = R + (R+50)/2 = 50.0 + j28.3 ⇒ **RL 11.3 dB, VSWR 1.74**,
  against the delta's 49.95 + j9.42 ⇒ **RL 20.6 dB, VSWR 1.21** —
  **9.3 dB worse with identical parts.** And 16.9 Ω 0402 (C82287) is a JLC
  **Extended** part with **17 pieces in stock**, where 49.9 Ω is JLC **Basic**
  with 1.78 M. The star costs more to assemble for a worse result.
- **Resistive DELTA, 3× 49.9 Ω 0402 (C25120).** CHOSEN.

## Decision

**Three 49.9 Ω ±1 % 0402 (UNI-ROYAL 0402WGF499JTCE, LCSC C25120, JLC Basic)
in a DELTA — one resistor between each pair of the three ports.**

Realised: split loss **6.017 dB**, port return loss **66.0 dB** at DC, port-to-
port isolation **6.017 dB**, **zero intrinsic phase shift and zero dispersion**
(there is no reactive element in the network). Full derivation in
DETAIL_DESIGN §5.

Choosing resistive is not settling. The only commercial parts that span this
bandwidth are BOTH resistive — Mini-Circuits ZFRSC-183-S+ (DC–18 GHz) and
HyperLabs HL7071 (DC–30 GHz). It is what the industry does at 85.7:1.

Second source at the same value and package: YAGEO RC0402FR-0749R9L, LCSC
C87044 (Extended, 1.22 M in stock). **NOTE:** an earlier fallback of 51 Ω
C25125 was recorded during sourcing as "also JLC Basic, 31 975 in stock" —
that is FALSE on both halves (it is Extended and stock 0 / out of stock at
LCSC). It is deleted here rather than carried, because a fallback that cannot
be bought is an inherited defect, not a fallback.

## Consequences

- **Costs 6.02 dB of the loop budget**, which the attenuator absorbs
  (ADR-0004). A reactive splitter would have cost ~1.8 dB, but no such part
  covers the band, so this is a consequence of the requirement, not of the
  choice.
- **Port-to-port isolation is capped at 6.02 dB and cannot be improved inside
  the splitter.** This is a theorem with three independent proofs
  (DETAIL_DESIGN §5.3): the 50/50/50 delta is the ONLY all-ports-matched
  resistive 3-port, so loss cannot be traded for isolation. **It is the direct
  cause of ADR-0004's decision to move attenuation into the arms**, and it
  must not be re-litigated as a part-quality problem.
- **The delta has no ground node.** Two layout consequences: keep the
  reference plane CONTINUOUS underneath (the small Cg at each vertex partially
  cancels the series Lp, forming a pi-section that mimics 50 Ω line — the
  opposite advice applies to a star), and the network is DC-continuous between
  all three ports, which ADR-0005 handles.
- **All 6 GHz performance rests on a mounting model, not on part data.**
  C25120 is a commodity thick film with no S-parameters, no |Z|/R curve and no
  application section. If measured 6 GHz return loss comes in below ~15 dB,
  the documented remedy is Vishay CH0402/FC0402 HF thin-film 49.9 Ω
  (characterized to 50 GHz, doc 53014 p.1) — which is NOT LCSC-stocked, so
  specifying it up front would itself be a sourcing failure.
- **Assembly variation becomes calibration error.** The network has zero
  intrinsic phase shift, so 100 % of observed phase imbalance comes from
  layout and from Lp mismatch between the two arm resistors (0.1 nH ≈ 3.8 Ω
  ≈ 2° at 6 GHz). Mitigations, all free: same reel for all three resistors,
  identical (NOT mirrored) placement rotation, minimum-area pads, no thermal
  reliefs, no teardrops, no solder-mask-defined pads.
- **Amplitude imbalance of 0.087 dB** worst case from two independent ±1 %
  parts (2 % differential × 4.339 dB/unit sensitivity). Static and
  calibratable — and it must therefore be MEASURED AND PUBLISHED, which
  extends brief D4 from delay-only to delay AND amplitude (ADR-0011).
- The board's TX input ceiling from the splitter alone is +24 dBm (62.5 mW in
  the hottest resistor at P_in/4); the attenuator, not the splitter, is the
  binding thermal element.
