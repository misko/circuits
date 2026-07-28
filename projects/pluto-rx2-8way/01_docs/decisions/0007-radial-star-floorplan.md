---
id: 0007
date: 2026-07-28
status: accepted
tags: [layout, rf, mechanical]
---
# 0007 — The radial star IS the floorplan; the EVK's octagon is not

## Context

D-LAYOUT (canon P8) says the floorplan is ADAPTED FROM the manufacturer's
reference layout, never authored against it, and canon M6 says the
manufacturer's own routed picture wins over my derivation.

pSemi publishes **no prose layout section** for PE42482A-X. What it publishes
is **Figure 21, "Evaluation Board Layout for PE42482", PDF p19 — a ROUTED
REFERENCE BOARD**, read visually at 300 dpi during the D-SPEC spike and
recorded in `02_parts/PE42482A-X/part.yaml`:

- an **OCTAGONAL** outline;
- **U1 at the exact geometric CENTRE**;
- **nine EQUAL-LENGTH 50 Ω traces radiating RADIALLY** to nine edge-launch
  SMA jacks (J0 = RFC at 12 o'clock, J1…J8 around the remaining facets);
- **a continuous ground-via fence flanking every arm**;
- the entire digital section (bypass cluster, strap jumpers, control header)
  grouped on the **pins-7…12 edge, OUTSIDE the RF fan**, with the control
  nets escaping on the **BOTTOM copper** so they never cross an RF trace.

That radial star is not merely pSemi's preference — **it is what the AoA
requirement wants anyway: equal trace length is equal phase BY
CONSTRUCTION**, and ADR-0006(b) shows the equality is also what bounds
thermal differential drift on the published deltas.

## Options

- **Copy the octagon.** REJECTED, and the reason is the interesting part —
  see Decision (1).
- **A rectangular fan-out** (switch on one edge, jacks along the opposite
  edge). REJECTED: it produces a ~20 mm spread in arm length, which
  ADR-0006(b) prices at **~1° of thermal phase drift at 6 GHz over 40 °C**,
  against 0.05° for the star — plus 20 mm × 0.036 dB/mm of extra loss on the
  worst arm, plus arm-to-arm crossings that the star has none of.
- **The radial star inside a RECTANGULAR outline.** **CHOSEN.**

## Decision

### 1. Keep the star; drop the octagon — because the connector is different

**The EVK's octagon is a consequence of EDGE-LAUNCH connectors.** An edge
launch must sit ON an edge, so nine of them force a nine-sided outline.

**`KH-SMA-KE-Z` is a VERTICAL THT FLANGE JACK** — four 0.9 mm posts and a
centre pin through the board, barrel normal to the laminate
(`02_parts/KH-SMA-KE-Z/part.yaml`). **It mounts on the board FACE and does
not need to be near an edge at all.** The polygon was never the requirement;
it was the connector style's shadow.

Dropping it buys three things:

1. **The outline stays a RECTANGLE, so the board stays expressible in the
   SHARED generic backend.** `generate_board_generic.py` supports a rectangle
   with optional corner radius and edge notches — **there is no polygon
   outline**. An octagon would force a bespoke `03_src/generate_board.py`,
   which ADR-0002 of the repo (tscircuit-native pipeline) makes an EXCEPTION
   requiring its own ADR. A board should not buy a bespoke generator to
   inherit a connector choice it did not make.
2. **The corners and the whole bottom strip become free real estate** for the
   digital section — which is exactly where Figure 21 puts it anyway.
3. **Ten edge-launch transitions are removed** from the RF budget.

This is the canon's STUDY-THEN-RE-DERIVE rule doing its job: extract the
DECISION (centred switch, equal-length fenced radial arms, digital on the
far side escaping down a layer) and leave the ACCIDENT (the polygon).

### 2. The angular assignment falls out of the pinout with ZERO crossings

PE42482A-X puts its RF ports on three sides and its entire digital group on
the fourth (Figure 22, PDF p20). Rotate `U_SW` so **pins 7–12 face 270°
(down)** and every port's natural exit direction is its own slot:

| package side | pins | ports | slots (θ, math convention, y-up) |
|---|---|---|---|
| top | 19–24 | RF8, RFC, RF1 | 75°, 105°, 135° |
| left | 1–6 | RF2, RF3, RF4 | 165°, 195°, 225° |
| right | 13–18 | RF5, RF6, RF7 | 315°, 345°, 15° |
| **bottom** | **7–12** | **GND, VDD, V1–V4** | **the 225°→315° sector is the ESCAPE CORRIDOR — no RF in it** |

Ten slots at **30° spacing over 270°**, leaving a **90° escape sector centred
on 270°**. The tenth slot, **45°**, sits between RF7 and RF8 and carries
`J_RX1` — the RX1 output — putting it 10.35 mm from `J_ANT8`, so the RX1
main line is short (0.37 dB at 6 GHz) and the pickoff, the RX1 jack and the
RX2 jack all cluster on the Pluto-facing side.

**No arm crosses another arm. No arm crosses a control net.** That is a
property of the pin-out, not of routing skill, and it is why this archetype
is worth harvesting.

### 3. The geometry (placement-stage INPUT, to be legalized and gated)

Outline `x0=21.0, y0=21.0, x1=71.0, y1=89.0` — **50.0 × 68.0 mm**, 4-layer
(ADR-0003). Star centre **C = (46.0, 46.0)**, ring radius **R = 20.0 mm**.
Jack rotation = its own θ (the 4-fold post square makes θ mod 90 equivalent).

| ref | port | θ | x, y (mm) |
|---|---|---|---|
| `J_RX2` | RFC (pin 22) | 105° | 40.824, 26.681 |
| `J_ANT1` | RF1 (pin 24) | 135° | 31.858, 31.858 |
| `J_ANT2` | RF2 (pin 2) | 165° | 26.681, 40.824 |
| `J_ANT3` | RF3 (pin 4) | 195° | 26.681, 51.176 |
| `J_ANT4` | RF4 (pin 6) | 225° | 31.858, 60.142 |
| `J_ANT5` | RF5 (pin 13) | 315° | 60.142, 60.142 |
| `J_ANT6` | RF6 (pin 15) | 345° | 65.319, 51.176 |
| `J_ANT7` | RF7 (pin 17) | 15° | 65.319, 40.824 |
| `J_ANT8` | RF8 (pin 19) — the RX1 antenna | 75° | 51.176, 26.681 |
| `J_RX1` | RX1 out (off-switch) | 45° | 60.142, 31.858 |

**Why R = 20.0 mm and not less.** Adjacent slots are `2·R·sin15° = 10.35 mm`
apart. Two 6.5 mm flanges at 30° relative rotation have a support-bound gap of
`10.35 − 7.96 = 2.39 mm` at R = 20, against **1.36 mm at R = 18** and
**0.09 mm at R = 18 with axis-aligned flanges** — i.e. touching. **That gap is
not spare board area, it is the ground-via fence that sets port-to-port
isolation between ten coaxial barrels on one laminate** — the quantity
`02_parts/README.md` records as OWED and which bounds the AoA leakage budget
independently of the switch (ADR-0006). Paying 2 mm of radius for it is the
cheapest thing on the board.

**Derived arm length:** `U_SW` RF pad at r ≈ 2.15 mm → jack centre pin at
r = 20.0 → **17.85 mm** per arm. At ADR-0003's constants that is
**0.64 dB at 6 GHz** (0.039 dB at 70 MHz) and **108.7 ps**, identical on all
nine arms by construction.

**Free escape width:** at the RF4/RF5 latitude the clear span between their
flanges is **20.3 mm** — the corridor the control bus, 3V3 and QSPI descend
through to the digital strip (`y ≳ 65`, 24 mm × 50 mm), which holds the MCU,
the QSPI flash, the LDO, the USB-C jack and the eight control-line passives.

**Adjacency (D-ADJ), each against its part.yaml budget:**

| group | placed | budget |
|---|---|---|
| `C_VDD` bypass | at `U_SW` pin 8 | `SW_VDD ≤ 3 mm` |
| `R_PD1…R_PD4` pull-downs | at `U_SW` pins 9–12, inside the escape corridor | `SW_V4 ≤ 4 mm` |
| `U_SW` pin 1 (LS) ground via | ≤0.5 mm from the pad centre | geometric — ADR-0005 |
| `R_T1`, `R_T2` | on the 75° radius at r = 17.0 / 15.0, **identical rotation** | `RX1_TAP_MID ≤ 1.37 mm` (λg/20), ADR-0006 |
| `R_S1…R_S4` | at the MCU pads | ADR-0005 |

**Mounting holes:** 4 × M3 at (24.5, 24.5), (67.5, 24.5), (24.5, 84.5),
(67.5, 84.5) — all ≥10.4 mm from the nearest flange centre. Ten cabled SMA
ports are ten torque paths into one laminate; they are structural, not
decorative.

## Consequences

- **`03_src/floorplan.yaml` is written from this table**, replacing the
  skill's `cook_loadcell` schema example verbatim. It is a placement-stage
  INPUT: the legalizer may move seeds, and `placement_gates.py` (P-OUT
  pads-inside-outline, P-CAP corridor demand) and P-COLLIDE gate the result.
  **Nothing here is copper yet, and none of it is a measurement.**
- **`escape_corridors: [{ref: U_SW, side: S, depth_mm: 4.0}]`** is declared,
  matching the escape budget of 5 on the pins-7…12 side recorded in the
  part.yaml.
- **The board is 50 × 68 mm = 34 cm².** Bigger than a fan-out board needs and
  smaller than the EVK; the size is set by ten 6.5 mm flanges on a
  fence-separated ring, and shrinking it spends the isolation budget.
- **This archetype is NEW.** `kicad-pcb/references/floorplan-archetypes.md`
  has no "radial RF star / N-way switch fan" class. **Harvest it at release**
  with the angular-assignment-from-pinout rule and the vertical-vs-edge-launch
  finding, which is the part a future board would otherwise re-pay.
- **If the connector is ever swapped for an edge launch, this ADR is void** —
  the outline question re-opens and with it the bespoke-generator question.
