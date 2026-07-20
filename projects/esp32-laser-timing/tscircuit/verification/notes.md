# esp32-laser-timing — tscircuit second-opinion: fidelity notes

Phase-1 of the boundary-migration ADR (`docs/decisions/0001-tscircuit-authoring-boundary.md`):
prove the tscircuit -> **KiCad schematic** bridge on a LARGE / ACTIVE board
(~76 parts: ESP32-S3-WROOM-1 module, USB-C, LM339 quad comparator, AMS1117, USB ESD, 3×
laser-driver FETs, 3× threshold dividers, buttons). Chosen to stress SCALE + active-IC
pin maps. KiCad (`../04_kicad/esp32_laser_timing.kicad_pcb`) stays the authoritative
fab-of-record; this folder is a non-authoritative render + measurement.

## Headline

| Measure | Result |
|---|---|
| Electrical components authored | **72 / 72** (76 KiCad footprints − 4 non-electrical M3 holes) |
| **tscircuit MODEL** net parity (circuit.json / readable-netlist, node-for-node) | **36 / 36 named nets identical** |
| **tscircuit kicad_sch EXPORT** net parity (node-for-node) | **14 / 36** — exporter loses fidelity at scale |
| ERC on the tscircuit kicad_sch (`kicad-cli sch erc --severity-all`) | **563** (mostly parametric, see below) |
| DRC on the tscircuit kicad_pcb (`kicad-cli pcb drc --severity-all`) | **260 violations / 150 unconnected** (mostly parametric) |
| Node-for-node parity after normalization | **YES for the tscircuit design model; NO through the native kicad_sch export** |

**Verdict:** tscircuit *authors* this large/active board perfectly — parity-by-construction
gives an exact node-for-node match of the sealed KiCad netlist, and the two stress parts
(41-pin ESP32 module, 14-pin LM339) mapped cleanly with zero pin-label errors. But its
**native `kicad_sch` exporter is not yet fidelity-preserving at this scale**: it collapses
multiple custom-footprint multi-pin chips onto one shared schematic symbol and fragments the
densest nets. So the *design* clears the bridge; the *current native-KiCad schematic export*
does **not** for a board with 2+ many-pin hand-authored-footprint parts.

## Net-name normalization map (KiCad → tscircuit)

Only leading-digit renames were needed (tscircuit `net.` selectors reject a leading digit):

| KiCad net | tscircuit net |
|---|---|
| `3V3` | `N3V3` |
| `5V`  | `N5V` |

All other 34 net names are preserved verbatim (`GND`, `COMP1..3`, `VTH1..3`, `PD1..3`,
`LDRV1..3`, `GATE1..3`, `LSW1..3`, `BTN1..3_N/_G`, `USB_DM/DP`, `CC1/2`, `EN`, `BOOT`,
`SCL`, `SDA`, `LED_A`). KiCad `unconnected-*` auto-nets are true no-connects and are not
authored (the ESP32 has 22 unused GPIO pads; the LM339 OUT4 pin13; USB-C SBU1/SBU2).

## How SCALE + active-IC pin mapping held up (the point of the exercise)

- **ESP32-S3-WROOM-1 (U1, 41 pads incl. EPAD)** — authored as a `<chip>` with a hand-authored
  `<footprint>` land pattern (perimeter pads 1–40 + 3.9 mm EPAD pad 41, real coordinates
  pulled from the KiCad footprint) and a **`pinLabels` map keyed to the same pad numbers as the
  KiCad symbol** (datasheet functions IO0/IO19_DM/EN/…; the three GND pads 1/40/41 given
  distinct labels GND/GND40/EPAD to keep schematic ports unique). In the tscircuit **model**
  all 19 connected pads land on the correct nets — **zero pin-label mismatches**.
- **LM339DT (U3, SOIC-14)** — `<chip footprint="soic14_p1.27mm">` + `pinLabels` (OUT2/OUT1/VCC/
  IN1-…/GND). The asymmetric datasheet pinout (outputs 2/1 top-left, inputs 4–11, outputs 14/13
  bottom-right; per-side minus-first) mapped verbatim; VTH3 correctly shared across pads 8 & 10.
  Exported cleanly (all 14 pads) because a **footprinter-string** footprint yields a uniquely
  named schematic symbol.
- **AMS1117 (U2, SOT-223), USBLC6 (D1, SOT-23-6), AO3400 FETs (Q1–3, SOT-23)** — footprinter
  strings; all pins exported correctly. (U2 SOT-223 tab: KiCad names it pad `2`, tscircuit's
  `sot223` names the tab pad `4`; both tie to 3V3 — benign pad-name delta, same net.)
- Parity-by-construction (`connections={{ pin: "net.NAME" }}`) is what makes the model exact —
  no reliance on tscircuit's `C1_pos`-style auto net naming.

## The exporter fidelity gap (root-caused)

The tscircuit design model (`build/circuit.json` / `verification/tsc_netlist.txt`) is
**36/36 node-for-node correct**. Everything below is lost only in the DSL→native-KiCad
`kicad_sch` *export*:

1. **Custom-footprint symbol collision (the big one).** tscircuit derives a chip's schematic
   lib-symbol id as `Device:U_chip_<footprintName>`. A footprinter *string* footprint has a
   name, so each such chip gets a **unique** symbol (`…_soic14_p1.27mm`, `…_sot223`, `…_sot23_6`,
   `…_pinrow4`) and exports all its pins. A **hand-authored `<footprint>`** has *no name*, so
   every custom-footprint chip collapses to the bare `Device:U_chip`. With **two** such chips
   (U1 and J1) both instances reference one shared symbol that cannot represent both pinouts —
   each is truncated to **2 pins** (pin1/pin2, emitted as `unconnected-(U1-Pad1/2)`), dropping
   the other 39 (U1) / 16 (J1) pins from the exported netlist.
   - Verified in isolation: a *single* 41-pin custom-footprint chip exports all 41 pins;
     add a second custom-footprint chip and **both** drop to a shared-symbol-limited count.
   - Naming the `<footprint name="…">` element does **not** propagate into the lib-id.
   - Practical rule for now: **at most one hand-authored-footprint `<chip>` per board** will
     survive the kicad_sch export intact; give any others a footprinter-string footprint.
2. **Dense-net fragmentation.** The schematic auto-layout does not merge every label on the
   busiest nets: some GND cap pins land on `Net-(C4-Pad2)` / `unconnected-(C3-Pad2)` fragments
   rather than the unified `GND` net, and `VTH1/VTH2` split similarly. This is why GND, VTH1,
   VTH2 miss nodes in the export even though those parts are simple two-pad passives.

**Net parity accounting (kicad_sch export, 14/36 pass):** of the 22 failing nets, ~18 fail only
because U1 and/or J1 are missing (symbol collision) — 3V3, BOOT, BTN{1,2,3}_G, CC1, CC2,
COMP1–3, EN, LDRV1–3, SCL, SDA, USB_DM, USB_DP; the remaining ~4 (GND, VTH1, VTH2, and 5V's
C11) fail from net fragmentation. All 70 non-U1/J1 components export their full pin set.

## ERC on the tscircuit kicad_sch — 563, classified

| n | type | class |
|---|---|---|
| 399 | `endpoint_off_grid` | parametric — tscircuit schematic coords aren't on KiCad's 50-mil grid |
| 95 | `lib_symbol_issues` | parametric — generated symbols lack KiCad library metadata |
| 40 | `pin_not_connected` | real & expected — the 22 unused ESP32 GPIOs, LM339 OUT4, USB SBU1/2, etc. |
| 12+10+6+1 | `label_dangling` / `unconnected_wire_endpoint` / `isolated_pin_label` / `wire_dangling` | artifacts of the U1/J1 collision + net fragmentation above |

~494 of 563 are parametric (grid + symbol-metadata); ERC is a fidelity signal, not a release gate.

## DRC on the tscircuit kicad_pcb — 260 / 150, classified

| n | type | class |
|---|---|---|
| 76 | `lib_footprint_issues` | parametric — tscircuit footprints carry no KiCad lib link |
| 62 | `text_thickness` | parametric — silk ref/val text sizing |
| 62 | `text_height` | parametric — silk ref/val text sizing |
| 24 | `solder_mask_bridge` | mostly real geometry — USB-C A/B rows overlap by design + tight pad gaps |
| 23 | `clearance` | parametric — 0.15 mm default tracks, no netclass/pour |
| 9 | `shorting_items` | **real** — auto-router shorts in congested corners |
| 2+2 | `copper_edge_clearance` / `silk_overlap` | minor |

Per the folder charter, tscircuit's auto-route is a *study, not fab-grade*: it emits thin
default geometry with no netclass/pour, so most of the count is parametric. The real signal is
the 9 auto-router shorts + 24 mask bridges. **The KiCad fab-of-record (`04_kicad/`) remains the
only orderable artifact.**

## Footprint gaps

- Hand-authored `<footprint>` children (KiCad land pattern, real pad geometry) for the two parts
  absent from footprinter: **ESP32-S3-WROOM-1 (U1)** and **USB-C TYPE-C-31-M-12 (J1)**; plus a
  small custom land for the **KF128L-3.5-2P screw terminals (J4–J12)** and the **CP_Elec 6.3×5.4
  electrolytic (C11)**.
- Everything else resolved from footprinter strings: `0805`, `sot23`, `sot23_6`, `sot223`,
  `soic14_p1.27mm`, `pinrow4`, plus `<led>`, `<pushbutton>`, `<testpoint>`, `<hole>`.
- Note: SW1/SW2 (TS-1187A, KiCad 4 pads named 1,1,2,2) render as a 2-terminal `<pushbutton>` —
  node-equivalent (BOOT/EN vs GND), pad-name delta only.

## Reproduce

```
export PATH="$HOME/.bun/bin:$PATH"
bash ~/.claude/skills/kicad-pcb/scripts/gen_tscircuit.sh ~/gits/circuits/projects/esp32-laser-timing
kicad-cli sch erc --severity-all kicad/esp32_laser_timing.kicad_sch
kicad-cli sch export netlist --format kicadsexpr -o verification/tsc_sch_netlist.net kicad/esp32_laser_timing.kicad_sch
```


---

## Phase-2 update (2026-07-19) — OUR converter clears the exporter ceiling

The "exporter fidelity gap" section above (14/36 net parity through the NATIVE export;
U1 + J1 collapsing to 2 pins each via the `Device:U_chip` symbol-id collision) is
**resolved** by our own converter (ADR-0001 Phase 2). `gen_tscircuit.sh` now renders the
AUTHORITATIVE `kicad/esp32_laser_timing.kicad_sch` via
`scripts/circuit_json_to_kicad_sch.py`, which gives every component a UNIQUE
`elt:SYM_<refdes>` lib_symbol (collision impossible) with pins keyed to the KiCad pad
names and one global-label net-glue per pin.

- **The ceiling is gone.** U1 (ESP32-S3-WROOM-1, 41 pads) exports **all 41 pins** and
  J1 (USB-C, 20 pads / 17 distinct) exports **all 17 distinct pads** — both matching the
  sealed board, vs **2 pins each** through the native export.
- **Gate result: `kicad-cli sch erc --severity-all` = 0 errors** (119 warnings, all the
  parametric `lib_symbol_issues` "lib 'elt' not in config" note) and **node-for-node
  netlist parity 0** vs the sealed board — **36/36 nets, 189/189 nodes, 25/25 no-connects**
  (up from 14/36 through the native export).
- Normalization: the leading-digit net renames (`N3V3`→`3V3`, `N5V`→`5V`) plus ONE
  documented footprint pad-name delta — AMS1117 SOT-223 tab, tscircuit `sot223` pad `4`
  ≡ KiCad merged pad `2`, same 3V3 net both sides (recorded in `../parity_padmap.txt`).

See `parity_converter.md` / `erc_converter.rpt`. tscircuit's native export is retained
as `kicad/esp32_laser_timing.native.kicad_sch` for reference (still 2-pin-truncated —
that is the bug the converter exists to bypass).
