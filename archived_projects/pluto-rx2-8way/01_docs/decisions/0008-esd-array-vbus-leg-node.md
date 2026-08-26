---
id: 0008
date: 2026-07-28
status: accepted
tags: [protection, esd, usb, topology]
---
# 0008 — `U_ESD` pin 5 sits on `VBUS_F`, downstream of the fuse

## Context

`02_parts/USBLC6-2SC6/part.yaml` left exactly one thing open and said so:

> "WHICH NODE PIN 5 SITS ON IS AN OPEN SCHEMATIC DECISION AND IT IS NOT FREE.
> … Either is defensible; what is NOT defensible is choosing by accident.
> RAISE IT AT SCHEMATIC CAPTURE and record the choice — this dossier
> deliberately does not silently decide something ADR-0004 owns."

This is that record. It is written BEFORE the TSX, because
`03_src/rules/electrical_invariants.yaml` has to assert whichever arm wins and
an invariant written after the schematic asserts the schematic, not the intent.

The tension is real and it is between two rules this board already accepted:

- **ADR-0004 puts the fuse UPSTREAM of the clamp** so a clamp that fails
  SHORT opens `F_IN` instead of burning on the host's current budget. That is
  the same ordering `D_TVS` obeys, and it is emitted as the
  `[VBUS, F_IN, VBUS_F]` `series_chain` invariant.
- **ST DocID11265 Rev 5 §2.3 says put the array as close as possible to the
  disturbance source (the connector)**, and §2.2 prices every millimetre:
  a 10 mm × 0.5 mm track is ~6 nH, and at dI/dt = 24 A/ns that is +144 V per
  leg — a 17 V clamp becomes 305 V. On that reading, pin 5 wants raw `VBUS`
  on the CONNECTOR side of `F_IN`, not `VBUS_F` behind a PPTC's resistance
  and inductance.

Two device facts frame it. `F_IN` (`1206L050/24WR`) is **R_1max 0.75 Ω**. The
USBLC6-2SC6 is a **rail-to-rail array**: two steering diodes per I/O (I/O→VBUS
and GND→I/O) plus **one Transil between the VBUS node and the GND node**, and
that Transil is INSIDE the package (Figure 1, PDF p1; the pin map was read from
it at stage 2).

## Options

### (a) pin 5 on raw `VBUS` — the connector side of `F_IN`

- **For:** the shortest possible path from pin 5 to the host supply, and it is
  what ST's own Figure 14/18 reference draws (no fuse in between).
- **Against — the decisive one:** it puts a shorted clamp leg OUTSIDE the only
  current limit this board owns. A USBLC6-2SC6 whose Transil fails short —
  which is how a TVS fails — then sits across the host's VBUS with nothing but
  the HOST's current limit in series. On a 3 A charger port that is a
  SOT-23-6 die dissipating up to ~15 W. `F_IN` exists to make exactly that
  case a 500 mA trip, and this arm walks the array out from behind it.
- **Against — and this one is counter-intuitive, which is why it is written
  down:** raw `VBUS` is the WORSE node for the I/O-strike path, not the
  better one. `C_BULK` (4.7 µF) and `D_TVS` both live on `VBUS_F`. An I/O
  surge is steered UP into the pin-5 node; the energy needs a SINK, and every
  sink on this board is on the far side of `F_IN`. Putting pin 5 on raw
  `VBUS` separates the array's clamp leg from the bulk capacitor and from the
  second clamp by 0.75 Ω plus the fuse's own inductance.

### (b) pin 5 on `VBUS_F` — downstream of `F_IN`. **CHOSEN**

- **For:** it obeys ADR-0004's fuse-upstream-of-clamp ordering, so BOTH clamps
  on this board (`D_TVS` and `U_ESD`'s VBUS leg) are behind the same 500 mA
  PPTC and a short in either opens it.
- **For:** it lands the clamp leg on the node that already carries `C_BULK`
  4.7 µF and `D_TVS` — the sink, not the source.
- **Against, and this is the cost the rejected arm was bought at:** for a
  strike arriving on the **VBUS contact of the connector itself**, `U_ESD`
  now clamps only after `F_IN`. The raw-`VBUS` stub between `J_USB`'s four
  VBUS lands and `F_IN` is left with no clamp of its own.

### (c) pin 5 on raw `VBUS` with a second PPTC in the pin-5 leg

REJECTED as a part class added to solve a problem option (b) solves with
topology. It also re-introduces the inductance the arm was chosen to avoid.

## Decision

**`U_ESD` pin 5 is on `VBUS_F`.** `F_IN` is upstream of every clamp on this
board without exception, and the array's clamp leg shares a node with the bulk
capacitance and the energy-class TVS.

**A 100 nF (`C_ESD`) is fitted from pin 5 to GND at the pin**, per ST Figure 18
(PDF p9, `CBUS`). It was absent from `DETAIL_DESIGN.md` §5's passives table and
is added there by this decision. It is not decoration: it is what makes the
pin-5 leg a LOCAL AC return, and it is the element that recovers most of what
option (a) was reaching for. The strike loop that matters is
`I/O pad → steering diode → (internal) Transil → pin 2 → GND`, closed locally
by `C_ESD` between pin 5 and pin 2 — **not** a loop that runs upstream through
`F_IN` at all. `F_IN`'s 0.75 Ω is in the DC feed to pin 5, which carries
150 nA max (Table 2) and no strike current.

**The cost of the rejected arm is stated rather than implied**, because the
half of ST §2.2 that option (a) was defending is real and is NOT recovered by
`C_ESD`: on a strike into the VBUS contact, this board's first clamp is
`D_TVS` behind `F_IN`, and the ~0.75 Ω + fuse inductance is genuinely in that
path. Two things bound it. First, the raw-`VBUS` stub carries no
semiconductor — four connector lands and one PPTC pad — so there is nothing on
it to damage. Second, ADR-0004 had ALREADY made that trade for `D_TVS`; option
(a) would not have removed it, only added a second clamp in front of it.

**What is emitted** into `03_src/rules/electrical_invariants.yaml` citing this
ADR (without them this is prose, and prose is what the D1 defect was):

| assertion | pins |
|---|---|
| `pin_on_net` | `U_ESD.5` → `VBUS_F` — the decision itself |
| `pin_on_net` | `U_ESD.2` → `GND` — the SINGLE ground pin, which carries the whole return |
| `pin_on_net` | `C_ESD.1` → `VBUS_F` — the Figure-18 capacitor exists and is on the chosen node |

## Consequences

- **The floorplan changes, and it was already wrong.** Both the ESD dossier and
  the USB-C dossier independently recorded the same finding at stage 2:
  `U_ESD` at `[54.0, 84.0]` against `J_USB` at `[46.0, 87.0]` is ~8 mm, against
  a **2.0 mm** `adjacency:` budget derived from ST §2.2 (at 2 mm the parasitic
  adder is ~29 V/leg and the clamp stays near 75 V; at 8 mm it is ~305 V).
  `03_src/floorplan.yaml` now seeds `U_ESD` straddling the D+/D- escape
  immediately behind the connector, with `C_ESD` at its pin 5 and `R_CC1`/
  `R_CC2` beside it. **A 17 V clamp turned into a 305 V clamp is not a
  placement preference; it is the difference between a protected port and a
  port whose owner believes it is protected.**
- **`C_ESD` is a new BOM line** (100 nF 0402) and a new row in
  `DETAIL_DESIGN.md` §5. It raises the VBUS-side bypass total from 5.7 µF to
  **5.8 µF**, still far under the USB 2.0 §7.2.4.1 10 µF device cap that makes
  "no inrush limiter" a decision (ADR-0004).
- **What is still NOT machine-graded, stated rather than implied:** the 2.0 mm
  `J_USB`↔`U_ESD` proximity is graded by **P-ADJ at the BOARD stage**, not at
  the schematic gate — E1 invariants read the netlist, and the netlist is
  identical at 2 mm and at 8 mm. The same is true of "route D+ IN on pin 1,
  OUT on pin 6": pins 1 and 6 are the same node, so no ERC, DRC, netlist or
  parity check can tell the in-line dress from a stub. Both are CHECKLIST
  lines, and both are why this ADR exists in a folder rather than in someone's
  memory.
- **The reversal trigger:** if anything ACTIVE is ever put on CC or SBU (a PD
  sink controller, a debug UART on SBU, a test point that leads somewhere), the
  ESD dossier's coverage argument is void and a 4-channel array is the right
  answer — and at that point the pin-5 node question re-opens with a different
  balance, because the CC lines would then have silicon behind them.
- **If `F_IN` is ever re-selected**, its R_1max is in the DC feed to pin 5 and
  in `D_TVS`'s strike path but NOT in the I/O strike loop; the dropout
  arithmetic in `DETAIL_DESIGN.md` §5 constraint 1 is the binding consumer of
  that number, not this ADR.
