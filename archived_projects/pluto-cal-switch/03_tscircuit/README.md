# 03_tscircuit — pluto-cal-switch

The board is authored ONCE, here, in TSX (repo ADR-0001 / ADR-0002), and
compiled to the two artifacts its **two audiences** read:

| audience | artifact | what it is |
|---|---|---|
| **humans** | `build/schematic.pdf` | tscircuit's OWN native render. This is the schematic document the release ships and what satisfies the human-graded **S6** readability item. |
| **the machine** | `kicad/pluto_cal_switch.kicad_sch` | OUR converter's output (`circuit_json_to_kicad_sch.py`). It feeds ERC / netlist / parity / placement / routing. It is never required to be pretty and nobody opens it in a tscircuit-native flow. |

Both derive from the same `build/circuit.json`, so **they cannot disagree on
connectivity.** Do not re-render the KiCad rebuild to make the human PDF — that
is polishing the wrong artifact.

## What is unusual about this board

- **It is an RF board whose netlist carries load-bearing SEMANTICS no
  geometric gate can see.** `03_src/rules/electrical_invariants.yaml` holds 34
  assertions, and the tsx is written to satisfy them by construction. The two
  that matter most: RF1 faces the ANTENNA on both switches (so power-on =
  antenna is native to the silicon, ADR-0001), and the COMPLETE pad chain sits
  UPSTREAM of both switches (so no switch state and no switch FAULT can present
  raw TX to a receiver, ADR-0016).
- **`LOOP_ARM1` / `LOOP_ARM2` are a matched pair whose delta is a PUBLISHED
  release artifact** (brief D4 / ADR-0011). Both arms are instantiated from one
  component function, so they cannot drift apart part-for-part; the remaining
  difference is geometry, which is stage 5's problem and the release's number.
- **The loopback path deliberately carries NO DC blocking capacitors.** The YAT
  pads DC-reference the internal RF node to ground through ~70 ohm per port, so
  the switches' `V_RFDC = 0 V` rating is satisfied by construction. Blocks are
  fitted only on the two user-facing ANTENNA ports (ADR-0005). Adding one to
  the cal path would be a defect, not caution.
- **The YAT exposed pad (pad 7) is the RF GROUND RETURN, not a thermal pad**
  ("Case is defined as ground lead"). It is bound to GND explicitly in the tsx
  rather than left for a pour to find.
- **Nine attenuator chips is the correct count**, not padding — the >=40 dB
  MINIMUM is sized against datasheet min columns and one chip less fails
  (38.67 dB). See `manifest.yaml`.

## Mutability

`src/`, `manifest.yaml`, `net_aliases.txt`, `parity_padmap.txt`, `package.json`,
`README.md`, `GENERATE.md` and `contracts.md` are the ONLY hand-written files
here. `build/`, `kicad/`, `verification/` and `fab/` are GENERATED and are never
hand-edited — a hand-fix there is erased on the next run and silently diverges
from the source. Fix the TSX and regenerate.

Regeneration: see `GENERATE.md`.
