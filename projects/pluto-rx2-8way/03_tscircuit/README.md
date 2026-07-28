# `03_tscircuit/` — pluto-rx2-8way, the board as source

`src/pluto_rx2_8way.tsx` **is** the board: an 8-element antenna selector for
angle-of-arrival on an ADALM-PlutoPlus RX2. One absorptive SP8T at the
geometric centre of a ring of ten vertical SMA jacks, sequenced by a
free-running RP2040 PIO, with element 8 shared with RX1 through a two-resistor
pickoff that costs RX1 0.43 dB.

This folder is pipeline stage **03 — hand-written truth**, the same stage as
`03_src/` (hence the same number). `03_src/` holds the KiCad-side config and
the promoted route; this holds the TSX the design is authored in. If they
disagree about the circuit, the TSX is right and the KiCad side is stale.

## S-DSL positioning

The declaration compiles to NATIVE KiCad artifacts and every gate runs on those
artifacts, never on the DSL's claims (canon S-DSL, repo ADR-0001/0002). The
bridge is OUR converter — `circuit_json_to_kicad_sch.py` — and NOT
`tsci export -f kicad_sch`, whose two proven bugs would be fatal on exactly
this board: it collapses every custom-`<footprint>` chip to one
`Device:U_chip` symbol and truncates it to 2 pins (this board has FOUR such
chips — a 25-pad QFN, a 57-pad QFN, ten 5-pad SMA jacks and a 17-pad USB-C),
and it emits an unannotated sheet that netlists to 0 nets.

## What is hand-written here, and what is generated

| hand-written | generated (never hand-edit) |
|---|---|
| `src/pluto_rx2_8way.tsx` | `build/`, `kicad/`, `verification/` |
| `manifest.yaml` — the declared refdes SET (S-COUNT base) | |
| `net_aliases.txt` — the one digit-leading rail | |
| `parity_padmap.txt` — `J_USB`'s alphanumeric pads | |
| `package.json`, `README.md`, `GENERATE.md`, `contracts.md` | |

A hand-fix in a generated file is erased on the next run and silently diverges
from the TSX until then. Fix the TSX.

## The two audiences

- **Humans** read `build/schematic.pdf` — tscircuit's OWN render. That is what
  a release ships as its schematic document.
- **The machine** reads `kicad/pluto_rx2_8way.kicad_sch` — our converter's
  output. It feeds ERC / netlist / parity / placement / routing and is never
  required to be pretty.

Both derive from the same `build/circuit.json`, so they cannot disagree on
connectivity.

## The three things this file is the first artifact to enforce

Each is invisible to ERC, DRC, netlist parity and the digital twin, and each
has a named incident behind it:

1. **`A6`↔`B6` and `A7`↔`B7` are strapped.** A Type-C plug is reversible. Wire
   one pair and the board enumerates in one insertion orientation and is dead
   in the other — with every gate green, because every pin has a net.
2. **`D_TVS` pad 1 is the cathode and clamps `VBUS_F`**, downstream of `F_IN`.
   This is the geometry of the usb-hub-3s v1.0 D1 defect, which passed ERC,
   DRC, parity, twin AND pin review because every artifact was consistently
   wrong together.
3. **`VREG_VOUT` (45) is wired in copper to `DVDD` (23, 50).** RP2040's 1.1 V
   core regulator is on-die and its output leaves the package; omit the link
   and every artifact still looks correct — `VREG_VOUT` reads as an unused
   output and `DVDD` as an undriven supply — while the chip never leaves reset.

See `GENERATE.md` for the commands and `contracts.md` for the mutability rules.
