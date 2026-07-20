# Phase C gate — ShuntMonitor composed 6x vs ble-bus-bar sealed board

**Question (falsifiable):** does ONE authored module (`../src/ShuntMonitor.tsx`),
instantiated 6x (channels 1..6, addresses 0x40..0x45), reproduce ble-bus-bar's 6
hand-authored current-monitor channels EXACTLY?

## How to reproduce

```
export PATH="$HOME/.bun/bin:$PATH"
cd tscircuit_modules/demo
tsci build shunt_monitor_demo.tsx
cp dist/shunt_monitor_demo/circuit.json build/circuit.json
python3 ~/.claude/skills/kicad-pcb/scripts/circuit_json_to_kicad_sch.py build/circuit.json \
  -o kicad/shunt_monitor_demo.kicad_sch --project shunt_monitor_demo \
  --parts-dir ../../projects/ble-bus-bar/02_parts
kicad-cli sch erc --severity-all -o verification/erc.rpt kicad/shunt_monitor_demo.kicad_sch
kicad-cli sch export netlist -o verification/demo.net kicad/shunt_monitor_demo.kicad_sch
# sealed reference:
kicad-cli sch export netlist -o verification/ble_bus_bar_sealed.net \
  ../../projects/ble-bus-bar/04_kicad/ble_bus_bar.kicad_sch
python3 verification/channel_parity.py verification/ble_bus_bar_sealed.net verification/demo.net
```

## Result (2026-07-20)

The converter kicad_sch resolves **54/54 components with a real FPID** (INA238 →
`Package_SO:MSOP-10_3x3mm_P0.5mm` via JLC C2868250; shunt → `bbar:R_Shunt_WSLP2726`
via JLC C844297 — both from ble-bus-bar's `02_parts`, passed with `--parts-dir`).

### Node-for-node parity (`channel_parity.py`)

For each channel i∈{1..6} the module emits {RS,RP,RN,CD,CB,U}{i}; every component's
pad→net map is **IDENTICAL** to the sealed ble-bus-bar board:

| channel | addr | node-for-node vs sealed |
|---|---|---|
| 1 | 0x40 | PASS |
| 2 | 0x41 | PASS |
| 3 | 0x42 | PASS |
| 4 | 0x43 | PASS |
| 5 | 0x44 | PASS |
| 6 | 0x45 | PASS |

- **NODE-FOR-NODE PARITY vs sealed: PASS** (all 6 channels)
- **ADDRESSES DISTINCT 0x40..0x45: PASS** — A1/A0 straps
  (0x40 GND,GND · 0x41 GND,VS · 0x42 GND,SDA · 0x43 GND,SCL · 0x44 VS,GND · 0x45 VS,VS)
- **KELVIN SENSE PRESERVED: PASS** — every channel: `RP` taps the shunt pin-1 (bus)
  stud → INA `IN+`; `RN` taps the shunt pin-2 (load) stud → INA `IN-`(9) = `VBUS`(8);
  `CD` bridges `KA↔KB`. Diff nets are the channel-local `KA{i}`/`KB{i}` (no P/N suffix,
  so KiCad diff-pair inference stays out — exactly the sealed board's choice).
- The six channels are **byte-identical in topology except at the two address-strap
  pins** (INA pad1=A1, pad2=A0) — confirmed by an isomorphism check that excludes those
  two pins → `True`. That per-channel difference IS the address, and it matches the
  sealed board channel-for-channel. (The headline `channel_parity.py` line "CHANNELS
  MUTUALLY ISOMORPHIC: FAIL" is an over-strict check that does NOT exclude the strap
  pins; the real gate is the per-channel-vs-sealed PASS above.)

### ERC (`erc.rpt`, `kicad-cli sch erc --severity-all`)

- **0 errors.** 380 violations, all `; warning`, in exactly the three documented
  parametric classes:
  - `endpoint_off_grid` (250) — the converter's 0.635 mm layout-mode fidelity grid.
  - `lib_symbol_issues` (76) — the embedded `elt:` symbol lib isn't in the headless
    kicad-cli config (env note).
  - `footprint_link_issues` (54) — `bbar:`/`Package_SO:` fp-libs not in the headless
    kicad-cli config (env note).
  This is the ADR bar: **0 ERC errors; warnings baselined with reasons.**

## Verdict

**One authored module, instantiated 6x, reproduces the 6 hand-authored channels
exactly.** Node-for-node parity holds on all six; the only per-channel variation is
the I2C address strap, which is a module *parameter* and lands correctly. The
registry model delivers "author once, compose everywhere" for this proven block.
