# ADR-0009 — Board C is a RIGID interposer + separate flex jumper (Path A)

status: accepted
date: 2026-07-24
depends-on: 0007 (multi-board structure), 0008 (CN1 = 10FDZ-BT ZIF)

## Context

ADR-0008 left a fork open: (a) rigid interposer + one dumb double-ended
10-finger 0.125mm flex jumper (only the jumper is out-of-pipeline), or
(b) a single rigid-flex interposer (whole board out-of-pipeline, T5).

## Decision (user-chosen, 2026-07-24 — "Path A")

Board C = a small **RIGID PCB** fully inside the proven pipeline, carrying:

- **J_MEMBRANE** — JST **10FDZ-BT** top-entry ZIF: receives the original OEM
  membrane tail (proven-compatible by construction, ADR-0008).
- **J_CN1_JUMPER** — a second, identical **10FDZ-BT**: receives the flex
  jumper whose far end plugs the OEM CN1. The flex jumper itself is a
  SEPARATE part (own task; a plain double-ended 10-finger / 2.54mm /
  0.125mm tail per the FDZ datasheet "Recommended dimensions for membrane
  switch lead") — NOT designed on this board; only its interposer-side
  receptacle lands here.
- **J_KEY_MATRIX** — keyed locking 10-pin breakout of the same ten lines to
  the cooksense main board (same JST GH SM10B-GHS-TB / pin map as the main
  board's J_KEY_MATRIX, so one straight-through GHR-10V-S cable serves).
- Labeled test points on all 10 lines, both sides of the pass-through.

Electrically PASSIVE: pins N of J_MEMBRANE, J_CN1_JUMPER, and J_KEY_MATRIX
share one net per line (KP_U1..KP_U6, KP_D1..KP_D4). No active parts, no
GND, no power rails, **no bond to logic ground or chassis** (BRIEF §5
keypad-domain isolation — the board is a floating 10-net domain).

## Why

- Both interposer interfaces become the SAME purchasable connector the OEM
  itself uses (ADR-0008); the only out-of-pipeline item left is the dumb
  flex jumper, which is coupon-gated (G1/G2) and independently revisable
  (contingency C1 touches only the jumper, not this board).
- The rigid board rides the proven rigid pipeline end-to-end (schematic /
  placement / routing gates all apply unmodified).

## Bounds carried forward (unchanged)

- **Coupon gate G1/G2 still BLOCKS fabrication/ORDERING** of Board C. The
  10FDZ-BT land pattern is authored from the JST eFDZ datasheet as CANONICAL
  (user directive 2026-07-24: "go ahead assuming 10FDZ-BT" — the DESIGN
  proceeds to a sealed release), but a REAL-PART physical footprint confirm
  (drill pattern + polarization-peg position against a purchased connector)
  is a mandatory ORDER_README bring-up ritual before any fab order (same
  class as the v1.0 J_TC/J_PWR pin-1 rituals).
- Flex jumper: vendor-assisted, >=100 insertion cycles on a sacrificial
  coupon, never first-fit on the OEM connector (T5).
- D4: passes through unchanged, labeled TP, firmware-locked-out downstream
  (T3) — nothing special on Board C beyond the labeled test point.

## Alternatives rejected

- **Rigid-flex single part**: puts the entire board outside the proven
  rigid pipeline (T5) for zero electrical gain. Rejected.
- **Rigid tongue (1.6mm) into CN1**: explicitly forbidden by the brief
  (§5 — thin membrane/flex tongue, not rigid edge). Rejected.
