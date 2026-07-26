# SUPERSEDED — DO NOT ORDER

Superseded by: `07_releases/cooksense-v1.3-2026-07-26/`

**This release is NOT orderable, and neither is v1.0** (its own notice, which
said v1.0 "remains electrically valid", is corrected as of 2026-07-26 — that
statement was true only about the mechanical repack and was read too broadly).

Every defect below was verified against THIS release's own sealed artifacts —
`source/cooksense.net` and `fab/cpl.csv` — not inferred from the changelog.
They are ordered worst-first: the first four are missing or inverted safety
behaviour, and each one is disqualifying on its own.

---

## 1. The opto-isolated 30 V contactor loop shares a SELV connector housing

Measured in `source/cooksense.net`:

```
J_ESTOP.1 -> 3V3          J_ESTOP.3 -> CONTACTOR_C     (isolated secondary)
J_ESTOP.2 -> ESTOP_RAW    J_ESTOP.4 -> CONTACTOR_LOOP  (isolated secondary)
J_ESTOP.5 -> GND
```

`ESTOP_RAW` (SELV) and `CONTACTOR_C` (the far side of the LTV-817S barrier) sit
on **adjacent pads of one 1.25 mm-pitch JST-GH housing, 0.650 mm apart, in a
single field harness**. One damaged, wet or contaminated harness is a
common-cause failure straight across the isolation boundary — the barrier is
5000 Vrms inside the package and 0.650 mm at the connector.

v1.3 moves the whole isolated domain onto its own 4-pole 3.5 mm screw terminal
(`J_ISOLOOP`), leaving J_ESTOP SELV-only with pins 3/4 on GND.

## 2. The door interlock is FAIL-PERMISSIVE

v1.1 fits `R_DOORPU`: pin 1 on `DOOR_RAW`, **pin 2 on 3V3** — a pull-UP. A
disconnected or broken door harness therefore floats the interlock input to the
permissive state. v1.3 replaces it with `R_DOORPD` pulling DOWN, so a lost
harness reads "door open" and refuses.

## 3. The watchdog can pet itself — `WD_PET` has no hold-down

Measured: `WD_PET: [('J_PI','11'), ('U_WD','4')]`. **That is the entire net.**
There is no pull-down. When the Pi tri-states GPIO17 — on reboot, on a crashed
process, on any GPIO reconfiguration — the TPS3823's WDI input floats, and a
floating WDI can be toggled by leakage and coupling. The board's primary runaway
backstop is not reliably present.

v1.3 adds `R_WDPETPD` at **1 k** (not 100 k: the value is derived from
I_IL x R < V_IL on the trigger input; a 100 k hold-down looks fixed and leaves
the node floating, and it passes every topology assert while doing so).

## 4. There is no open-thermistor detection at all

v1.1 contains **no** `U_COMP2`, `R_OPENT`, `R_OPENB`, `R_CLMPA/B` or
`TCAM_OPEN` — zero occurrences of each in the sealed netlist. The board has the
over-temp comparator only. An **unplugged, broken or open-circuit thermistor is
not distinguished from a healthy cold sensor**, so the temperature interlock
silently stops protecting when a sensor head falls off.

v1.3 adds the second comparator half plus the bleed/threshold network that makes
open, cold and hot separable, with every reading inside the LMV393's specified
common-mode range.

## 5. `CE1` ships REVERSED — a polarized electrolytic across a live 5 V rail

Measured in `fab/cpl.csv`:

```
CE1,220uF,CP_Elec_6.3x7.7,50.0,-66.0,top,180.0
```

CE1 is a 220 uF aluminium electrolytic on 5V_PROTECTED. At 180 its "+" terminal
lands on GND. A reverse-biased aluminium electrolytic on a live supply vents.

The netlist was never wrong — pad 1 is on 5V_PROTECTED in every revision. The
defect is the **CPL rotation**, inherited from an advisory name-DB rule
(`^CP_Elec_6.3x7.7`) that encodes a **different vendor's pad-1 convention**.
Measured against JLC's own model the correct offset is **0**: our pad 1 at local
x=-2.700 versus JLC's at x=-2.670, rms 0.0300 mm at 0 against 3.7972 mm at 90
(127x), and JLC's silk chamfer runs -1.98,3.38 -> -3.38,1.98, on the same -x end
as our pad 1. Third instance of this class in the fleet after usb-hub-3s-v3's
C1/C2.

## 6. Twenty-two wrong CPL rotations, including all ten safety-chain gates

Every rotation in this release came from name-DB guesses rather than
measurement. Measured in `fab/cpl.csv`:

```
U_AND1,C22046,SOT-23-6,158.0,-68.0,top,270.0
```

- **The 10 safety-chain SOT-23-6 gates** — U_AND1, U_AND2, U_AND3, U_CAND1,
  U_CAND2, U_DECDEN, U_DECUEN, U_FAULTAND, U_LATCHG, U_OSCLR (C22046) — ship at
  **270 where the measured answer is 180**, i.e. 90 degrees out. A
  90-degree-rotated SOT-23-6 does not connect its intended nets, and **every
  hardware safety interlock on this board is one of these ten**.
- **The 8 JST-GH connectors**, **U_OPTO** (the isolation opto itself), **CE1**,
  **J_PWR** and **J_LOADCELL** ship at unadjudicated name-DB rotations.

v1.3 resolves **189/189 CPL rotations from measured per-LCSC rows**, and the 10
codes / 14 refs with no numbering-free corroboration are named in
`fab/rotation_human_gate.txt` for the order-preview human gate.

## 7. CPL population and datum defects

- **13 CPL placement rows carry a BLANK LCSC** — the twelve Standex reeds and
  J_TC — instructing JLC to machine-place parts it cannot source. v1.1's
  MANIFEST declared 12 of the 13 and omitted J_TC, so the paperwork and the
  machine instruction disagreed with each other and with the board.
- **J_LOADCELL and J_PI are CPL rows despite being pure through-hole** (5/5 and
  40/40 plated drilled pads, F.Paste on none) on an SMT-only order.
- **J_PI's CPL position is 24.1634 mm off JLC's datum.** JLC's datum is the
  bounding-box centre of PAD CENTRES; our footprint anchors on pad 1. The
  x-component is 24.130 mm (half the 48.26 mm array span), the y-component
  1.270 mm (half the row pitch).
- **The opto isolation barrier measures 0.199 mm** of ISO-to-SELV copper on the
  v1.2 routed copper that descends from this placement, against a 2.000 mm
  requirement. v1.3 measures 2.126 mm.

---

## What is NOT a defect of this release

The v1.3 **R_OPENT 6.2 kOhm** finding does not apply here and is deliberately
not listed above. R_OPENT does not exist in v1.0 or v1.1 — the open-detect
network is a v1.3 addition (see item 4), so this release cannot have mis-valued
it. That defect was found and fixed **inside the v1.3 development cycle before
release**, and it is recorded in the v1.3 ORDER_README section 12 and in
`01_docs/STATUS-cooksense.md`. Attributing it here would put a defect on a
release that could not have had one.

## What v1.0 and v1.1 remain useful for

Nothing that gets built. Keep them as the provenance record for the mechanical
repack, and as fixtures: the pre-notch board at `3f781da` is still the known-bad
fixture that proves the I-HW mounting-hardware check can fail. **Do not
fabricate or assemble from either release.**
