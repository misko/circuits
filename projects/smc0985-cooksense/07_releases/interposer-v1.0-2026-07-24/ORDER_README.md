# ORDER — interposer (Board C) v1.0, 2026-07-24

Passive keypad interposer for the SMC0985KS (project smc0985-cooksense,
ADR-0007 multi-board; this is the SECOND board — the main board is
cooksense-v1.1-2026-07-24). OEM membrane tail -> J_MEMBRANE (10FDZ-BT ZIF) ->
ten straight-through lines -> J_CN1_JUMPER (10FDZ-BT ZIF) -> flex jumper
(SEPARATE part, NOT in this release) -> OEM CN1; the ten lines break out on
J_KEY_MATRIX (JST GH) to the main board. Floating keypad domain: NO ground,
NO power, NO chassis bond anywhere on this board — that is the spec, not an
omission (BRIEF §5, ADR-0009).

## 0. ORDER GATES — read BEFORE spending money (both are USER-HELD)

1. **VERIFY THE 10FDZ-BT LAND PATTERN AGAINST A PHYSICAL CONNECTOR BEFORE
   ORDERING FAB.** The footprint (drill pattern + polarization-peg position +
   which housing end carries circuit 1) is derived from the JST eFDZ
   datasheet drawing ONLY (p.3 top-entry layout, "hole dimensions are for
   reference only", note 4) — it is NOT real-part-verified. Buy the
   connectors FIRST (2x 10FDZ-BT(S)(LF)(SN) + spares), lay one on a 1:1
   printout of pdf/assembly.pdf (or measure: 10 holes phi0.9 at 2.54mm
   pitch, span 22.86mm, phi1.8 boss colinear 2.54mm outside pin 1), and
   confirm pin-1/boss end. Same posture as the main board's J_TC/J_PWR
   pin-1 rituals. A mirrored circuit-1 read would attach U/D labels to the
   wrong conductors (redteam_topology P1).
2. **G1/G2 coupon discipline stands** for the FLEX JUMPER (separate part):
   >=100 insertion cycles on a sacrificial coupon, never first-fit on the
   OEM CN1 (T5, ADR-0008/0009). This board itself is rigid and in-pipeline,
   but its system role is exercised only through that jumper.

## 1. JLC order options

- 2-layer, 1.6mm FR-4 (10FDZ-BT applicable PCB thickness = 1.6mm — do NOT
  order 0.8/1.0mm), tier jlc_2layer_default: NO advanced options needed.
- Board 54 x 46 mm. Quantity: 5 (min) — 1 build + spares for the G2 fit trials.
- Surface finish: HASL fine (hand-solder THT + one 1.25mm SMD connector);
  ENIG optional.
- Assembly: EITHER bare boards (hand-solder everything: one SMD GH + two THT
  ZIFs) OR SMT assembly for J_KEY_MATRIX only. **If uploading BOM/CPL to
  JLC assembly: DELETE the two uncoded 10FDZ-BT rows first** (J_MEMBRANE,
  J_CN1_JUMPER — self-supplied hand-solder; leaving blank-LCSC THT rows
  invites a substitution query). Rotation: the exporter already emits the
  GH at JLC rotation 90 (twin fit=0.01mm) — still confirm in the JLC
  placement preview.

## 2. Hand-solder list (self-supplied, DO-NOT-SUBSTITUTE)

| Ref | Part | Source | Note |
|---|---|---|---|
| J_MEMBRANE, J_CN1_JUMPER | JST **10FDZ-BT(S)(LF)(SN)** | Mouser / RS / DigiKey (NOT on LCSC) | TOP entry ("BT"). **Never 10FDZ-ST** (side entry, different land pattern). Boss NPTH sets orientation; "1"/"10" silk numerals remain visible seated |
| (J_KEY_MATRIX) | JST SM10B-GHS-TB, LCSC C2683602 | JLC stock 8587 (checked 2026-07-24) | SMD; hand-solderable if ordering bare boards |

## 3. KEYPAD RIBBON — harness spec (redteam P1: silent-reversal trap)

Interposer J_KEY_MATRIX <-> main-board J_KEY_MATRIX: **10-way JST GHR-10V-S
housings BOTH ends, SSHL-002T-P0.2 contacts, wired contact-k -> contact-k
(1->1 ... 10->10).** Both boards carry the SAME part at the SAME rotation
(mouth off-board), so for a flat cable both housings must be crimped on the
SAME conductor face with pin 1 on the SAME cable edge, mated via a planar
U-bend. A premade "opposite-side" GH jumper SWAPS pin1<->pin10 (U-bank <->
D-bank) with zero electrical symptom until the key matrix scans wrong.
**Before first use: continuity-beep interposer TP_M_U1 -> main-board KP_U1
(J_KEY_MATRIX pin 1 side) and TP_M_D4 -> KP_D4.**

## 4. Bring-up ritual (G6 continuity map)

1. Bare board, nothing inserted: beep each of the 10 lines J_MEMBRANE.k <->
   J_CN1_JUMPER.k <-> J_KEY_MATRIX.k <-> TP_M_* <-> TP_C_* (labels on silk;
   pins count 1..10 west->east between the "1" and "10" numerals). Confirm
   NO continuity between any two different lines, and NO continuity from any
   line to the four mounting holes (they are NPTH — floating by design).
2. ZIF handling: slider OPEN before inserting a tail (12.7mm overhead when
   open); tail is a plain 0.125mm membrane lead, contact face per the OEM
   tail's existing orientation in CN1.
3. With the OEM membrane tail seated in J_MEMBRANE and the (coupon-passed)
   flex jumper to CN1: the OEM panel must remain FULLY operational through
   the interposer before anything connects to J_KEY_MATRIX (G6 before G7).
4. D4 (T3): present on TP_M_D4/TP_C_D4 and J_KEY_MATRIX.10, passed through
   unchanged; its function is uncharacterized — downstream lockout owns it.

## 5. Isolation reminder

Do not "improve" this board with a ground pour, shield, or chassis strap.
The keypad domain floats (BRIEF §5); the sealed main board enforces its own
isolation comb on its side of the ribbon.
