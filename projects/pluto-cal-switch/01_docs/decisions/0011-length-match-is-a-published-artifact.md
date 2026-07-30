---
id: 0011
date: 2026-07-27
status: accepted
tags: [topology, verification]
---
# 0011 — The length match is a PUBLISHED MEASUREMENT, not a routing target

## Context

The commission says the two loopback runs must have "same path length on each
run". Asked how tight, the user answered **A6: "not tight — as long as
distance is precisely known, it will be software offset"**, then immediately
added **A7: "but lets try to make them the exact same if possible"**.

Read separately, A6 relaxes a requirement and A7 restores it. Read together
they are not a tolerance at all — **they are a DOCUMENTATION requirement.**
BRIEF D4 already records that conclusion. This ADR fixes what must actually be
produced, because "publish the delta" is not executable until somebody says
which quantity, measured how, in what units, and against what constant.

Three things surfaced during design that D4 as written does not cover.

## Options

- **Treat it as a routing tolerance** ("match to within X mm"). REJECTED: it
  answers the wrong question. A software offset is only as good as the number
  it is given, and a tolerance band is not a number.
- **Publish the DELAY delta only** (D4 as originally written). REJECTED as
  incomplete — see Decision.
- **Publish delay AND amplitude, per arm and as a delta, with the conversion
  constant pinned to the ordered stackup.** CHOSEN.

## Decision

**The release ships, as a verification artifact:**

| quantity | per arm | delta | why |
|---|---|---|---|
| routed electrical length, mm | yes | yes | the raw geometric fact |
| propagation delay, ps | yes | yes | at **6.135 ps/mm**, the constant DERIVED for the ordered stackup (ε_eff 3.383 — DETAIL_DESIGN §1) |
| insertion loss vs frequency | yes | yes | 70 MHz – 6 GHz |

**and the layout achieves symmetry BY CONSTRUCTION**, not by tuning: the two
arms are mirror images about the splitter axis, identical bend for bend, same
layer, no vias, with the arm attenuators at **identical rotation, not mirrored
rotation**.

> **THE CONGRUENCE TRANSFORM IS PER-NET, NOT ONE MAP FOR THE WHOLE ARM
> (added 2026-07-30 — the next person will assume one map, because both prior
> readers of this ADR did).** "Mirror images about the splitter axis" is true
> of the splitter end and FALSE of the switch end:
>
> - **The splitter resistors are REFLECTED** about y = 55.000. `LOOP_ARM1`'s
>   `R_DELTA1.2` is at y 53.670; the reflection sends it to 56.330, which is
>   `R_DELTA2.2` exactly. A **+14.5 mm translation sends it to y 68.170, where
>   there is no pad at all.**
> - **The switches are TRANSLATED** by +14.5 mm. `U_SW1` sits at y 47.950 and
>   `U_SW2` at 62.450 (a reflection would give 62.050). Their pin-1 lands
>   coincide under both maps, but the **second pad row does not**: a reflected
>   arm-2 entry lands **0.010 mm from `U_SW2.6`** against a 0.150 mm clearance
>   floor. Measured, and refused by the planner.
>
> **`audit_board.py` A-SYM cannot see this and reports PASS at 0.0 µm**, which
> is not a bug in A-SYM — it grades the arm parts whose pads sit at
> y 47.750 / 62.250, and for those pads the two maps are *the same map*,
> because 62.250 = 2 × 55.000 − 47.750. The population A-SYM grades is exactly
> the population where the distinction is invisible. Both maps are isometries,
> so the member totals are equal to the nanometre either way — the spread is
> 0.000000 mm under either choice, and only the *landability* distinguishes
> them. `03_src/rf_copper.py` declares the map per net (`xf="R"` vs `xf="T"`)
> and verifies landing, clearance, width, grid and congruence against the live
> board, refusing whole rather than shaving.

### The three extensions to D4

1. **AMPLITUDE, not just delay.** ADR-0004 moved 12 dB of attenuation into
   each arm, so the two arms now contain independent parts. Worst-case
   arm-to-arm amplitude imbalance is **1.6 dB (DC–5 GHz) / 1.9 dB (5–15 GHz)**
   on the YAT datasheet windows, plus **0.087 dB** from the splitter's own
   ±1 % resistors. All of it is STATIC and calibratable — *but only if it is
   measured and published.* An unpublished 1.6 dB is exactly the error this
   board exists to remove.
2. **The conversion constant is a DERIVED number, and it must ship with the
   delta.** 6.135 ps/mm is pinned to `JLC04161H-7628`. A stackup change
   silently invalidates every published picosecond. The artifact states the
   stackup.

   > **CORRECTED 2026-07-30, BY THIS CLAUSE'S OWN ARGUMENT.** This ADR
   > published **6.0 ps/mm** (ε_eff 3.26). Re-derived on the as-fabbed
   > cross-section at Dk 4.4 — the value JLC publishes for the ordered
   > stackup, against DETAIL_DESIGN §1's "taken as 4.3" — the constant is
   > **6.135 ps/mm** (ε_eff 3.383, λ_g 27.17 mm at 6 GHz, 13.25 °/mm). The old
   > figure was **2.2 % low**. The clause above says a stackup change
   > invalidates every published picosecond; a *constant* change does the
   > same, so it is corrected here rather than noted downstream. Derivation:
   > `03_src/rules/nets.yaml`, "WIDTH DERIVATION" block.
   >
   > **THE PUBLISHED DELTA IS IMMUNE, AND THAT IS ARITHMETIC, NOT LUCK.** The
   > arm spread is **0.000000 mm BY CONSTRUCTION** (the two arms are congruent
   > under a per-net isometry — see below), and 0.000000 mm × any constant is
   > **0.0000 ps**. No conversion constant, right or wrong, can move a delta
   > that is exactly zero. What moves is the **per-arm ABSOLUTE**: at the
   > promoted arm length the per-arm delay goes from 96.48 ps at 6.0 ps/mm to
   > **98.65 ps** at 6.135 ps/mm. Only the absolute was ever at risk, and it
   > is the number this correction exists to make true.
3. **Mirrored rotation is forbidden, and it is a CPL fact.** The splitter has
   zero intrinsic phase shift, so 100 % of observed phase imbalance comes from
   layout and from mounting-inductance mismatch: **0.1 nH ≈ 3.8 Ω ≈ 2° at
   6 GHz**. Mirroring the two arms' passives makes solder-fillet and
   pick-orientation asymmetry into calibration error. Same rotation, same reel,
   same lot.

### What is NOT claimed

The edge-launch SMP reference plane sits at the routed board outline
(ADR-0006), so board-outline routing tolerance is inside the measured length.
It affects all three notches through the SAME tool path, so the arm-to-arm
term is the router's within-board repeatability, not JLC's board-to-board
±0.2 mm. **That is an argument, not a measurement** — the published delta is
measured on the actual board and therefore includes it either way.

## Consequences

- **`03_src/rules/nets.yaml` carries a dedicated `RF_LOOP_MATCH` class** for
  `LOOP_ARM1` / `LOOP_ARM2` so the pair is visible to the router and to the
  rules gate as a pair, not as two unrelated nets.
- **A per-unit artifact, not a per-design one.** Amplitude imbalance is
  unit-to-unit (independent parts), so the published number describes THE
  BOARD IN HAND. A design-level figure would be a lie for every other unit.
  The release must state which unit was measured.
- **The measurement needs a VNA.** The board cannot self-report loss vs
  frequency. If no VNA is available the release ships the routed lengths and
  the derived delays, and states plainly that the amplitude delta is
  UNMEASURED — a partial result honestly reported, never a passing claim.
- **Constrains routing**: no vias in either arm, no layer changes, same-layer
  mirror symmetry, and inter-arm separation ≥3× dielectric height plus a via
  fence (two parallel 50 Ω microstrips on a 0.21 mm prepreg couple at roughly
  −25 to −35 dB over a few mm at 6 GHz — **at or ABOVE the 29.8 dB isolation
  the arm pads buy**, so the routing can undo the pads' work).
- Makes the arm-pad decision (ADR-0004) affordable: its only real cost is an
  imbalance that this ADR converts from a hidden error into a published number.
