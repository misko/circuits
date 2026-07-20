# tscircuit_modules — THE REGISTRY (ADR-0002 Phase C)

Our hard-won, **proven** subcircuits, published as **reusable, parameterized
tscircuit modules**. New boards COMPOSE certified building blocks instead of
re-authoring them. This is the "best of both worlds": tscircuit's ergonomics,
our engineering. KiCad stays authoritative (canon S-DSL / ADR-0001) — a module is
just a typed way to emit the same `circuit.json` that our converter + gate stack
already certify.

## Location & layout

Repo root `tscircuit_modules/` (a shared library, deliberately NOT inside any one
project so many boards can import it):

```
tscircuit_modules/
  README.md                     # this catalog + the compose pattern
  src/
    ShuntMonitor.tsx            # module #1 — INA238 + WSLP2726 Kelvin shunt channel
  demo/                         # a gate board that composes the module(s)
    package.json
    shunt_monitor_demo.tsx      # imports ShuntMonitor, instantiates it 6x (0x40..0x45)
    build/circuit.json          # (generated) tsci build output
    kicad/*.kicad_sch           # (generated) OUR converter output — the machine artifact
    verification/
      parity.md                 # the Phase C gate result (node-for-node vs ble-bus-bar)
      channel_parity.py         # the falsifiable gate script
      erc.rpt  demo.net  ble_bus_bar_sealed.net
```

## The compose pattern — how a new board reuses a module

1. **Import** the module and instantiate it, once per instance, with a plain-net-name
   API. Internal nets are channel-prefixed by the module so N instances never collide;
   you only pass the board-level nets (studs, rails, bus signals) and the parameters:

   ```tsx
   import { ShuntMonitor } from "../src/ShuntMonitor"

   {[1,2,3,4,5,6].map((ch) => (
     <ShuntMonitor key={`mon${ch}`} channel={ch} i2cAddress={0x40 + (ch-1)}
       busNet={`VF${ch}`} loadNet={`VP${ch}`}
       sdaNet="SDA" sclNet="SCL" alertNet="ALERT"
       vsNet="N3V3" gndNet="GND" />
   ))}
   ```

   **Net-name convention (ADR-0001 canonical-name):** the `net.` selector can't author
   a leading digit, so pass the 3V3 rail as `"N3V3"` — the converter's `canon_net`
   strips the guard `N` → `3V3`. `GND`/`SDA`/`SCL`/`ALERT` pass through verbatim.

2. **Render → certify** with the existing bridge — no new tooling:

   ```
   export PATH="$HOME/.bun/bin:$PATH"
   tsci build <board>.tsx                                   # -> dist/.../circuit.json
   circuit_json_to_kicad_sch.py build/circuit.json -o kicad/<board>.kicad_sch \
       --parts-dir <project>/02_parts                       # specialty FPIDs
   kicad-cli sch erc --severity-all ...                     # gate: 0 errors
   kicad-cli sch export netlist ...                         # -> node-for-node parity
   ```

   **Specialty parts need two things in the TSX:** `supplierPartNumbers={{ jlcpcb: [...] }}`
   (the JLC code links the part to its `02_parts/<MPN>/part.yaml` footprint via the
   converter's override) **and** a `<footprint>` child (or a footprinter token) so
   tscircuit can render it. Commodity R/C/headers just take a size string (`"0805"`).
   Point `--parts-dir` at the project whose `02_parts/` holds the specialty footprints.

## Catalog

| module | source of truth (proven on) | parts | status |
|---|---|---|---|
| **`ShuntMonitor`** | ble-bus-bar `port_channel(i)` | INA238 (I2C addr strap) + WSLP2726 0.5 mR Kelvin shunt + 2×10R + 100n diff filter + 100n decoupler | **PROVEN 2026-07-20** — 6× → node-for-node parity vs sealed board, addresses distinct, Kelvin preserved, ERC 0 errors (`demo/verification/parity.md`) |

### `ShuntMonitor` API

```ts
ShuntMonitor({
  channel: number,        // 1-based; prefixes internal KA{ch}/KB{ch}, suffixes refdes
  i2cAddress: number,     // 0x40..0x4F; decodes to the A1/A0 strap targets
  busNet: string,         // shunt pin1 / RP tap (bus-side stud, e.g. "VF1")
  loadNet: string,        // shunt pin2 / RN tap (load-side stud, e.g. "VP1")
  sdaNet, sclNet, alertNet: string,   // I2C + open-drain alert
  vsNet: string,          // INA VS rail + strap target (canonical-guarded, e.g. "N3V3")
  gndNet: string,         // ground + strap target (e.g. "GND")
  shuntMilliohm?: number, // default 0.5 (WSLP2726L5000FEA)
  inaJlc?: string,        // default C2868250 (INA238AIDGSR)
  shuntJlc?: string,      // default C844297 (WSLP2726L5000FEA)
})
```

Emits per instance: `RS{ch}` (shunt), `RP{ch}`/`RN{ch}` (10R Kelvin sense),
`CD{ch}` (100n diff), `CB{ch}` (100n decouple), `U{ch}` (INA238). Refdes match
ble-bus-bar's, so a composed board's netlist matches the hand-authored one verbatim.

## Next candidates (priority order)

1. **RJ45 port-channel** — the crow-array / crowsync repeated Ethernet jack + magnetics
   + termination block (another N-identical-channel case, the strongest reuse signal).
2. **power-entry-protection** — reverse-block + TVS + fuse + bulk (usb-power-3s /
   ble-bus-bar bus input; a fixed, high-consequence block that's been re-derived per board).
3. **ESP32 standard hookup** — ESP32-C3/S3 module + boot/reset straps + decoupling +
   USB-C/USBLC6 front end (cook-hub, esp32-laser-timing, ble-bus-bar all re-author it).

Each graduates the same way `ShuntMonitor` did: author once in `src/`, compose in a
`demo/`, and PROVE node-for-node parity against the sealed board it was distilled from.

## Boundaries (unchanged by the registry)

A module is an authoring convenience only. It emits `circuit.json`; the converter
compiles that to native `.kicad_sch`; **every gate still runs on the native artifact**
(ERC, netlist parity, and — when a board adopts placement-as-code — audit/legalize/DRC).
The two hard lines stay KiCad-only: **routing physics** (KRT) and the **digital twin**.
A module never routes and never self-grades.
