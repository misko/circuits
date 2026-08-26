---
id: 0003
date: 2026-07-28
status: accepted
tags: [tier, mechanical, rf]
---
# 0003 — 4-layer JLC04161H-7628, impedance-controlled, at jlc_4layer_advanced

## Context

D-TIER: the fab tier is a COST CEILING declared at commission, defaulting to
the cheapest plausible tier, and raising it costs this ADR plus the tier's
exact `order_readme` line. `03_src/rules/nets.yaml` still carried the template
default `fab_tier: jlc_2layer_default`, and **P-TIER FAILED** on it, measured
before any edit:

```
FAIL P-TIER: parts exceed fab_tier 'jlc_2layer_default':
             ['PE42482A-X needs jlc_4layer_advanced']
```

Two questions have to be answered together because they have different
causes: the **layer stackup** (forced by the RF and by where the digital
escapes) and the **via/track class** (forced by one package).

## Options

### Layer count

- **2-layer, 1.6 mm FR4.** **REFUTED — the 50 Ω line does not fit either end
  of the path.** With `h = 1.53 mm` (1.6 mm less two 35 µm coppers) and
  Dk 4.4, a 50 Ω microstrip is **≈2.91 mm wide** (Hammerstad-Jensen with the
  thickness correction — the same closed form used for the chosen stackup in
  DETAIL_DESIGN §1). Against that:
  - **The SMA launch: NEGATIVE clearance.** `KH-SMA-KE-Z`'s four ground posts
    sit on a 5.08 mm square, so the centre pin is `2.54·√2 = 3.592 mm` from
    each post. With Ø1.4 mm holes and Ø2.4 mm annular pads, the clear span
    from the centre pad edge to a post pad edge is
    `3.592 − 1.20 − 1.20 = 1.19 mm`. A 2.91 mm trace has a half-width of
    **1.46 mm**. It overlaps the ground pads by 0.27 mm on each side, and it
    is wider than the centre pad it lands on.
  - **The switch land: 11.6× too wide.** PE42482A-X lands are
    **0.25 × 0.40 mm** (Figure 23, PDF p21).
  - **There is nowhere for the digital section to escape.** pSemi's own
    reference board (Figure 21, PDF p19) escapes the whole control section on
    the BOTTOM copper, underneath the RF fan. On a 2-layer board the bottom
    copper IS the RF reference plane, so every control escape becomes a slot
    in the return path of a nine-arm radial star. This is the decisive
    argument, and it is specific to THIS board: a 2-layer SP8T fan-out cannot
    have both a solid reference and a routed control bus.
- **2-layer, thinner (0.8 mm / 0.4 mm).** REFUTED. 0.8 mm gives a 1.41 mm
  line — still 5.6× the QFN land and still overlapping the SMA ground pads
  (half-width 0.70 mm against 1.19 mm of clear span, with no room for a
  fence). 0.4 mm gives ≈0.72 mm, which fits the launch but not the land, and
  **ten cabled SMA torque paths on a 0.4 mm laminate is a mechanical
  non-starter**. Neither solves the escape problem.
- **4-layer `JLC04161H-7628`, 1.6 mm.** **CHOSEN.** L1→L2 prepreg
  **0.2104 mm**, Dk 4.4 — JLC's DEFAULT 4-layer stackup, no material premium
  and on their controlled-impedance list. 50 Ω single-ended is **0.36 mm**
  (DETAIL_DESIGN §1).
- **6-layer.** REJECTED: nothing needs it. There is one dense package, one
  bus, and 270° of the board is a nine-net radial fan with no crossings by
  construction (ADR-0007). Paying for two more layers to route nothing is the
  over-engineering this canon's E-TOPO/D-TIER pair exists to catch.

### Via / track class

- **`jlc_2layer_default` / `jlc_4layer_standard` / `jlc_6layer_standard`**
  (0.127 mm track/space, 0.45 mm via / 0.30 mm drill, 0.50 mm hole-to-hole).
  **INFEASIBLE, and the arithmetic is one line:** PE42482A-X is a QFN-24 at
  **0.50 mm pitch**, and an escape via between adjacent pins leaves
  `0.50 − 0.30 = 0.20 mm` of hole-to-hole gap against a **0.50 mm** floor
  (`fab_tiers.yaml`). No via fits. The part is 24 pins + an exposed pad, far
  outside the ≤12-pin "outward-only-local" rescue class that lets a small
  dual-row QFN take a cheap tier, and its worst side carries **5** escapes
  (GND, VDD, V1–V4).
- **`jlc_4layer_advanced`** (0.09 mm track/space, 0.25 mm via / 0.15 mm
  drill, 0.25 mm hole-to-hole). **CHOSEN.** `0.50 − 0.15 = 0.35 mm ≥ 0.25` —
  it fits, with 0.10 mm to spare. Proven orderable in this repo
  (usb-power-3s v1.0–1.3).
- **`jlc_6layer_smallvia`** also computes feasible (0.30/0.15 vias,
  0.20 hole-to-hole) and is REJECTED as strictly more expensive for the same
  escape.

**Independent confirmation (canon M1).** The five verdicts above were derived
here from `fab_tiers.yaml`'s numbers; `escape_check.py --style qfn --pitch
0.5` was then run and returns exactly the same five —
`2layer INFEASIBLE / 4layer_standard INFEASIBLE / 4layer_advanced ok /
6layer_standard INFEASIBLE / 6layer_smallvia ok`. Two derivations, one answer.

## Decision

**`fab_tier: jlc_4layer_advanced`**, on `JLC04161H-7628`:

| layer | | function |
|---|---|---|
| L1 | 35 µm | **RF microstrip (0.36 mm = 50 Ω)** — the nine radial arms, the pickoff cell, the USB pair |
| | 0.2104 mm prepreg 7628, Dk 4.4 | |
| L2 | 35 µm | **SOLID GND — no split, no slot, anywhere under an RF arm or the USB pair** |
| | 1.065 mm core | |
| L3 | 35 µm | 3V3 pour + the control bus + QSPI — the digital escape layer, pSemi Figure 21's bottom-copper role |
| | 0.2104 mm prepreg | |
| L4 | 35 µm | GND |

**Controlled impedance is REQUESTED at order time.**

**Constants pinned to this stackup** and used throughout DETAIL_DESIGN:
50 Ω single-ended **w = 0.36 mm**; ε_eff **3.328**; **t_pd = 6.09 ps/mm**;
λg(6 GHz) **27.41 mm** (so λg/20 = **1.37 mm**, the via-fence pitch and the
lumped-element length bound); microstrip loss **0.036 dB/mm @6 GHz**,
**0.0022 dB/mm @70 MHz**.

**ORDER_README line required by D-TIER**, the `order_readme` string from
`fab_tiers.yaml` with its `<reason>` filled:

> **ADVANCED option REQUIRED: min via 0.25/0.15 mm** (PE42482A-X QFN-24 at
> 0.50 mm pitch — at the standard-tier 0.30 mm drill the adjacent-pin
> hole-to-hole gap is 0.50 − 0.30 = 0.20 mm against a 0.50 mm floor, so no
> escape via fits). 4-layer `JLC04161H-7628`, **IMPEDANCE CONTROL
> REQUESTED**.

Until a release exists this line lives in exactly two machine-readable
places — beside `fab_tier:` in `03_src/rules/nets.yaml`, and as a checkable
line in `01_docs/CHECKLIST.md` — and it is copied VERBATIM into
`ORDER_README.md` at the seal.

## Consequences

- **P-TIER passes.** Re-measured after the raise: `P-TIER PASS`, and
  `P-ESC PASS 3 parts` unchanged.
- **The tier rides on ONE part today**, and that is a fragility worth naming:
  removing PE42482A-X would license dropping back to standard. It will not
  stay that way — an RP2040 (BRIEF A4) is a QFN-56 at 0.40 mm pitch and
  computes the same tier unconditionally. Recorded now so a future
  "can we save the advanced fee?" question has its answer already written.
- **The thin top prepreg costs loss.** 0.036 dB/mm at 6 GHz against ~0.013
  for a wide line on 1.6 mm — 2.8×. Over the 15.9 mm radial arm that is
  **0.57 dB instead of 0.21 dB**, and it is paid on all nine arms. Accepted
  because the alternative does not physically land on the parts.
- **THE WIDTHS ARE CLOSED-FORM, NOT A FIELD SOLVE**, and Dk is quoted at
  1 GHz while the band runs to 6 GHz (FR4's Dk falls with frequency; at
  Dk 4.2 the same 0.36 mm line is 51.6 Ω). **Re-confirm 0.36 mm against
  JLCPCB's own impedance calculator for the exact ordered stackup before
  release** — a CHECKLIST line, not a note.
- **No power plane.** 3V3 reaches the switch and the MCU on L3 pours and L1
  stubs; that must be planned at placement, not discovered at routing.
- **Ten THT SMA jacks disqualify the board from JLC Economic PCBA** and add a
  per-order THT surcharge (~$3.50 setup + ~$0.0173/joint + $3.00 extended
  component); at 10 × 5 = 50 joints that is ~$0.87/board of joint fee alone.
  The non-default-stackup requirement forces Standard assembly anyway
  (Economic is documented as standard-stackup-only), so the two constraints
  agree rather than compete.
