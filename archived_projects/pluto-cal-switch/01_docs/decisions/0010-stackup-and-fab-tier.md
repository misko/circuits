---
id: 0010
date: 2026-07-27
status: accepted
tags: [tier, mechanical]
---
# 0010 — 4-layer JLC04161H-7628, impedance-controlled, at ADVANCED tier

## Context

D-TIER says the fab tier is a COST CEILING declared at commission, defaulting
to the CHEAPEST plausible tier, and that raising it requires this ADR plus an
ORDER_README line.

Two separate questions have to be answered together, because the sourcing spike
answered them separately and reached contradictory conclusions: the **layer
stackup** (which the RF requires) and the **via/track class** (which two parts
require).

The spike's SMA function argued for **2-layer 1.6 mm FR4**, on the grounds that
a through-hole SMA launch's pad-to-plane capacitance scales as 1/h, so a thin
dielectric makes the launch worse. Its splitter, attenuator and MCU functions
all independently argued for **4-layer**.

## Options

### Layer count

- **2-layer, 1.6 mm FR4.** **REFUTED — and not on RF loss. The 50 Ω line does
  not fit the parts.** A 50 Ω microstrip on 1.6 mm FR4 is **2.9–3.1 mm wide**.
  Against that:
  - the splitter's entire 3 × 0402 delta is ~2 mm across — three 3 mm lines
    cannot land on a 2 mm triangle;
  - the MC1630 attenuator lands are **0.30 mm**;
  - the BGS12WN6 lands are **0.25 mm**;
  - at the SMA, a 3.112 mm trace has a half-width of 1.556 mm against a ground
    pad edge at 1.415–1.540 mm — **NEGATIVE clearance.** The trace would
    overlap the ground pads and is wider than the centre pad it lands on.

  A GCPW variant (W ≈ 1.2 mm, 0.25 mm gap) fits the SMA but is still 4× the
  attenuator's land width. **And the 1/h argument that motivated 2-layer is
  itself refuted** (ADR-0007): once the through-hole barrel is included, thinner
  is BETTER or thickness-independent, in both of two independent models.
- **4-layer `JLC04161H-7628`, 1.6 mm.** CHOSEN. L1→L2 prepreg 0.2104 mm,
  Dk 4.4, JLC's DEFAULT 4-layer stackup — no material premium, and on their
  controlled-impedance list.

### Via / track class

- **`jlc_2layer_default` / `jlc_4layer_standard`** (0.127 mm track/space,
  0.45 mm via / 0.30 mm drill). INSUFFICIENT, for **two independent reasons**:
  1. **RP2040, QFN-56 at 0.40 mm pitch**, computes `jlc_4layer_advanced`
     UNCONDITIONALLY under `escape_check` — 56 pins is far outside the ≤12-pin
     "outward-only-local" rescue class that lets a small dual-row QFN take the
     cheap tier.
  2. **BGS12WN6's pin-2 ground via.** Pin 2 (GND) is the SOLE ground on a part
     with no exposed pad and no inner ring. A 0.45 mm standard-tier via centred
     on its 0.25 mm land leaves **0.050 mm** to the pin-1 and pin-3 lands,
     under the 0.127 mm floor. Offsetting it outward onto a stub does fit
     (~0.130 mm clearance) but adds ~0.2–0.3 nH = **7–11 Ω of common
     ground-return impedance at 6 GHz** — attacking the spec that is ALREADY
     tightest on this board (21 dB minimum isolation at 5150–5925 MHz).
- **`jlc_4layer_advanced`** (0.09 mm track/space, 0.25 mm via / 0.15 mm drill).
  CHOSEN. Proven orderable in this repo (usb-power-3s v1.0–1.3).

## Decision

**`fab_tier: jlc_4layer_advanced`**, on the stackup:

| layer | | function |
|---|---|---|
| L1 | 35 µm | **RF microstrip (0.36 mm = 50 Ω)**, USB pair, control fan-out |
| | 0.2104 mm prepreg 7628, Dk 4.4 | |
| L2 | 35 µm | **SOLID GND — no split anywhere under an RF trace or the USB pair** |
| | 1.065 mm core | |
| L3 | 35 µm | 3V3 / 5V pours + digital routing |
| | 0.2104 mm prepreg | |
| L4 | 35 µm | GND |

**Controlled impedance is REQUESTED.**

Derived constants pinned to this stackup and used throughout DETAIL_DESIGN:
50 Ω single-ended **w = 0.36 mm**; 90 Ω differential **0.33 mm / 0.25 mm gap**;
ε_eff **3.383**; **tpd = 6.135 ps/mm**; λg(6 GHz) **27.17 mm**; microstrip loss
**0.036 dB/mm @6 GHz**, 0.0019 dB/mm @70 MHz.

> **AMENDED 2026-07-30 — ε_r IS 4.4 THROUGHOUT, AND THE HEADLINE "0.35 mm =
> 50 Ω" WAS WRONG AT EITHER PERMITTIVITY.** This ADR's own stackup table above
> says Dk 4.4 (JLC published); DETAIL_DESIGN §1 said "ε_r taken as 4.3". The
> two give different answers and the dispute never mattered, because at *both*
> values 0.35 mm is above 50 Ω — moving to 4.3 makes it worse, not better.
> `03_src/rules/nets.yaml` had recorded "0.35 → 51.0 Ω" in its own table since
> stage 4, contradicting this line in the same repository.
>
> **The width is now 0.36 mm, and it is derived THREE ways, not two.** The two
> derivations that produced 0.35 mm were both Hammerstad-Jensen closed form —
> one method run twice, which is the shared-method trap canon M1 names. An
> independent **2D finite-difference field solve** (box-integration Laplace,
> discrete-Gauss charge extraction, validated against Hammerstad-Jensen to
> −0.35 % at t = 0) puts the answer for a *bare* trace at **0.3736 mm**, not
> 0.3610 mm — the two maths disagree by 3.4 % on the same cross-section, which
> is a wider spread than the correction itself.
>
> **What settled it is a term neither closed form carries: the solder mask.**
> At w = 0.35 mm the conformal mask is worth **−1.55 Ω** and the trapezoidal
> etch **+0.46 Ω**; the as-fabbed cross-section (this board does not open mask
> over its RF runs) needs **0.3590 mm** for 50 Ω. The bare-trace closed form
> and the as-fabbed field solve then bracket **0.36 mm** within 2 µm, which is
> why that is the authored value. Full derivation, per-term measurements and
> the return-loss table: `03_src/rules/nets.yaml`, "WIDTH DERIVATION" block.
>
> **This is a documentation-consistency fix, not an RF rescue.** The worst
> model puts the OLD 0.35 mm line at RL 35.0 dB (best: 43.4 dB); the SMA
> launch on this board is RL 6.0 dB by this ADR's own corrected figure. The
> old width was never the limiting mismatch and this change does not claim to
> have fixed a broken board.

**ORDER_README line (required by D-TIER):**
> **ADVANCED option REQUIRED** — 4-layer, 0.25 mm via / 0.15 mm drill,
> impedance-controlled, stackup `JLC04161H-7628`.

## Consequences

- **The tier is justified TWICE over.** If the RP2040 were ever swapped for a
  coarser-pitch part, the BGS12WN6 ground via still requires advanced — so the
  tier decision does not ride on the MCU choice alone, and removing the MCU
  does not license dropping back to standard.
- **The thin top prepreg costs 2.7× the microstrip loss per millimetre** versus
  a wide line on 1.6 mm — 0.036 dB/mm at 6 GHz instead of ~0.013. Over the
  53 mm loopback run that is **1.91 dB instead of 0.69 dB**, and it is why the
  chain tilt is 3.09 dB rather than the sourcing spike's 1.64 dB. **That single
  correction moved the attenuator value** (DETAIL_DESIGN §1.1). The cost is
  accepted because the alternative does not physically fit the parts.
- **THE WIDTHS ARE NOW A FIELD SOLVE AS WELL AS A CLOSED FORM** (amended
  2026-07-30). Hammerstad-Jensen with a thickness correction, cross-checked by
  an independent 2D finite-difference field solve on the as-fabbed
  cross-section. That cross-check is what found the 3.4 % method spread and
  the missing solder-mask term. **They must STILL be re-confirmed against
  JLCPCB's own impedance calculator for the exact stackup ordered, before
  release** — three of our own solves are still ours, and the fab builds to
  its model, not to ours. A CHECKLIST item, not a note.
- **The layer assignment is the single most important routing rule on the
  board.** L2 solid under everything RF and under the USB pair. This is where
  the RF requirement and the USB requirement coincide rather than compete
  (`hardware-design-with-rp2040` §2.4.1 p.11: *"A solid, uninterrupted area of
  ground copper, stretching the entire length of the track"*). It also means
  **there is no power plane**: 3.3 V reaches six scattered IOVDD pins on L3 and
  L1, which must be planned at placement, not discovered at routing.
- **THT parts (2× SMA, micro-USB legs) disqualify the board from JLC Economic
  PCBA** and add ~$6.93/order. The tier decision therefore also fixes the
  assembly service to Standard, which is separately required by the non-default
  stackup: JLC's Economic PCBA is documented as *"Standard stack-up only,
  special stack-up is not supported"*.
- **A 4-layer THT SMA launch needs a bottom-plane antipad ≥ Ø3.5 mm** (ADR-0007)
  — on this thin top prepreg the inner-plane relief is not optional. The
  spike's "do not promote to 4 layers without relieving L2" warning survives;
  its arithmetic (RL 4.5 dB / VSWR 3.93) does not — |Γ| was never normalised by
  √(1+x²), and the correct figure within its own model is RL 6.0 dB.
- **Via fence at ≤2.0 mm pitch** (λg/12 at 6 GHz) beside every RF trace and
  around every launch, emitted as a generated rule.
- USB full-speed does **not** require a controlled 90 Ω pair on a board this
  size — the critical length at a 4 ns edge is ~170 mm and our run is under
  30 mm — but the stackup delivers it at essentially the same trace width
  (0.33 mm vs 0.35 mm, same layer, same reference), so it is routed as a proper
  pair anyway. Free.
