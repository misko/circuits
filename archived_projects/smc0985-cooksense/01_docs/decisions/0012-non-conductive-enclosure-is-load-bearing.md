# ADR-0012 — The non-conductive enclosure is a LOAD-BEARING electrical assumption

status: accepted
date: 2026-07-25
tags: isolation, mechanical, safety

## Context

cooksense's headline safety property is that the keypad-contact domain
(KEYPAD_ISO: the reed contacts and the RKEY/RSTOP mid-nets that reach the
appliance's own keypad matrix) holds **>= 6.000 mm** creepage to every SELV
logic net (brief section 4/7, ADR-0001). On the board surface that is held by
the isolation comb and, since v1.3, by a DRU rule (`keypad_isolation_6mm`) that
DRC can fail on.

There is one path the DRU rule cannot see. **DRC does not model mounting
hardware.** An NPTH is a hole, not a conductor, so a metal M2.5 screw + DIN125
washer + nut fitted into a mounting hole is invisible to every copper-based
check — while physically being a ~6 mm diameter disc of metal sitting on both
faces of the board. That disc can bridge from keypad copper to SELV copper, and
if two holes are bonded to each other by a conductive enclosure it can bridge
between *different* holes.

The v1.3 measurement that forced this decision: with hardware modelled as a
3.0 mm-radius conductive disc, the nearest keypad copper to a hole centre was
5.311 mm (H1), 5.962 mm (H2), 7.029 mm (H4) — so under a *pairing* model the
board's worst keypad-to-SELV path through the hardware was **3.000 mm against a
6.000 mm requirement**. That is P0-1.

## Decision

**The enclosure is NON-CONDUCTIVE, and no conductive plate, bracket, rail or
standoff set bonds two or more of the four mounting holes together.** (User
decision, 2026-07-25.)

That assumption selects the **PER-HOLE** rule and retires the pairing rule:

    PER-HOLE (ACTIVE):   for every hole i:  a_i + s_i >= 6.000 mm
    PAIRING  (INACTIVE): min_i(a_i) + min_j(s_j) >= 6.000 mm

where `a_i` is the distance from the hardware disc edge to the nearest
KEYPAD_ISO copper and `s_i` the distance to the nearest SELV copper, both
measured on **FILLED** copper (a pads-only scan hides the pour and produces a
false all-clear). Where `s_i < 0` the fastener is SELV-bonded — the GND pour
reaches 0.200 mm from the hole wall — and the per-hole requirement collapses to
`a_i >= 6.000 mm` alone.

Under the per-hole rule H1 and H2 already passed. H4 did not, and is fixed by
an **edge notch** at x[191.50, 200.10] y[48.8, 49.8]: it reaches the east board
edge, so it is OUTLINE geometry rather than an internal slot — no router-bit
minimum, no JLC internal-cutout surcharge. (An internal slot is not even
manufacturable there: the corridor between H4's hardware edge at x196.0 and
K_STOP.3's pad edge at x196.55 is 0.55 mm, narrower than any router bit.)

MEASURED on filled copper after the notch, hardware r = 3.0 mm, by `I-HW`
(`audit_board.py --ihw`, 2026-07-25):

| hole | a (keypad) | s (SELV) | governing figure | verdict |
|---|---|---|---|---|
| H1 | 2.305 (J_KEY_MATRIX.1, KP_U1) | 13.631 (K_U1.2) | a+s = 15.936 | PASS |
| H2 | 3.129 (R_STOP.2, KP_D1) | 13.000 (K_STOP.1) | a+s = 16.129 | PASS |
| H3 | 40.933 (K_U1.4) | -1.450 (GND pour) | a = 40.933 | PASS |
| H4 | **6.598** (K_STOP.3, RSTOP_MID; around the notch) | -1.450 (GND pour) | a = 6.598 | PASS |

**H4's real margin is 0.598 mm, not the 2.5 mm previously recorded.** The
figure of 8.500 mm in commit 95db1d2 does not reproduce and no geometry
recovers it; the shortest legal surface path around the notch's west face,
allowing the fastener disc to overhang the notch end, is 6.598 mm (hand check:
0.602 + 6.004 − 0.008 ≈ 6.6). The verdict direction is unchanged — H4 PASSES —
but anything that grows keypad copper near H4, or shrinks the notch, has
0.598 mm of room, not 2.5 mm. Treat H4 as the tight hole.

A second method note, learned the same day: **a straight-line distance metric
cannot see the notch at all.** It measures the pre-notch and notched boards
identically (H4 a = 4.031 mm on both) — so it would fail the very board the
notch fixes, and it would have "passed" the pre-notch board on any threshold
loose enough to pass this one. I-HW therefore measures the SURFACE PATH around
outline cutouts (visibility-graph shortest path over outline vertices and
disc-rim/outline intersections), which is what creepage actually is.

**No pour pullback was added at H3/H4 and none is wanted.** At both holes the
fastener is SELV-bonded, so the requirement is `a` alone; pulling the plane back
would cost In1/F.Cu/B.Cu copper at two corners of a 4-layer board for zero
change in the safety margin.

## Consequences

The assumption is now a dependency of a safety property, so it has to survive
the person who made it. It is recorded in four places, deliberately redundant:

1. **This ADR** — the reasoning and the measured table.
2. **`03_src/cooksense/audit_board.py`, check `I-HW`** — the machine gate. It
   encodes BOTH rules and takes the enclosure assumption as an explicit
   constant. Flipping that constant to "a conductive enclosure bonds the holes"
   is exactly what makes the check FAIL, at the measured pairing figure. This
   is the only mechanism that survives a future revision moving copper near a
   hole, because DRC will never see it.
3. **The silkscreen**, beside the mounting holes: the person fitting this board
   into a metal bracket has to be told at the moment they are doing it.
4. **The ORDER_README mechanical section**, as a fastener line item:
   non-conductive (nylon/polyamide) M2.5 hardware, or metal hardware in a
   non-conductive enclosure with no plate bonding any two holes.

**If a future build bolts this board to a metal chassis plate, the keypad-to-
SELV isolation defect silently re-opens on a mains-adjacent cooking interlock.**
The correct response is not to waive `I-HW`: it is to move the holes (which
changes the enclosure interface) or to add notches at H1/H2 as was done at H4.

## Alternatives rejected

- **Model the hardware as non-conductive (all-nylon fasteners) and downgrade
  P0-1 to a board marking.** Rejected as the *primary* mechanism: a marking is
  not a gate, and nylon M2.5 in a hot appliance is a creep-and-fail part. Nylon
  hardware remains an acceptable *field* answer, which is why the ORDER_README
  offers it as one of the two ways to satisfy the fastener line item.
- **Pour pullback at every hole.** Costs copper on three layers and, under the
  per-hole rule, buys nothing at H3/H4 (see above).
- **Move the holes.** Correct under the pairing rule, but it changes the
  enclosure interface and was not the user's call to make silently.
