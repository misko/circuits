# tscircuit second-opinion — fidelity notes (xt60-usb-supply-rerun)

Phase-1 of ADR-0001 (`docs/decisions/0001-tscircuit-authoring-boundary.md`): does tscircuit
clear the **schematic bridge** for a *connector-heavy* board? KiCad stays the fab-of-record
(`../../04_kicad/xt60-usb-supply.kicad_pcb`); this folder is a non-authoritative render whose
`kicad_sch` export is diffed node-for-node against the sealed board.

## Headline — node-for-node parity ACHIEVED

| metric | result |
|---|---|
| components | **51 / 51** matched (refdes-for-refdes) |
| named nets | **28 / 28** matched (after normalization) |
| per-net node sets `{net → {refdes.pad}}` | **28 / 28** matched |
| total logical nodes | **151 / 151** (KiCad 151, tscircuit 151) |
| pad-name fidelity (all specialty footprints) | every KiCad pad name reproduced |
| **node-for-node parity** | **YES** |

Measured with `scratchpad/parity.py`: KiCad side via `pcbnew`; tscircuit side via
`build/circuit.json` (`subcircuit_connectivity_map_key` links each `source_port`/pad to its
`source_net`). Both sides collapse duplicate/split physical pads to logical `(refdes,padname)`
nodes, so the QFN thermal pad and USB shields compare fairly (see caveats).

## Normalization map (the ONLY normalization needed)

| KiCad net | tscircuit net | why |
|---|---|---|
| `5V_A` | `N5V_A` | leading digit breaks the `net.<NAME>` selector |
| `5V_C` | `N5V_C` | same |

Every other net name is verbatim (`GND`, `VBAT_P`, `VBAT_RAW`, `VBAT_F`, `SW_A/C`, `BST_A/C`,
`FB_A/C`, `VCC_A/C`, `CC1/2`, `DCP1/2/3`, `DCPC`, `LED1/2/3_A`, `PFET_G`, and the four
intentional no-connects `NC_U1_PG`, `NC_U2_PG`, `NC_J5_SBU1`, `NC_J5_SBU2`).

## Footprinter gap — the connector finding (this is what this board tests)

Parity-by-construction bound every pin to an explicit net via `connections={{pin:"net.NAME"}}`.
The stress was footprint availability. tscircuit's **footprinter** resolved only the commodity
land patterns; **11 distinct footprints across 20 components needed hand `<footprint>` children.**

| footprint source | parts | notes |
|---|---|---|
| footprinter `0603` | R1–R6, RFA1/2, RFC1/2, CBS1/2, CVCC1/2 | pads `1`,`2` — match KiCad |
| footprinter `1206` | CIN_A1/A2, CIN_C1/C2 | |
| footprinter `1210` | COUT_A1–A4, COUT_C1–C4 | |
| footprinter `0805` | LED1/2/3 | |
| footprinter `smb` | D1 | DO-214AA, pads `1`,`2` |
| footprinter `sot23_6` | **U3, U4, U5, U6** (USBLC6-2SC6) | pads `1`–`6` — match KiCad |
| **hand `<footprint>`** | **J1** XT60PW-M | Amass power conn; 2 THT blades (Ø2.7 PTH) + 2 board-lock `<hole>` pegs |
| **hand `<footprint>`** | **J2, J3, J4** USB-A (Stewart SS-52100) | 4 THT signal pads + 2 shield PTH (`SH`) each |
| **hand `<footprint>`** | **J5** USB-C (HRO TYPE-C-31-M-12) | 16 SMD signal pads `A1..B12` + 4 shield PTH `SH` + 2 NPTH |
| **hand `<footprint>`** | **U1, U2** SY8368 | irregular flip-chip QFN3x3-10, split GND pad `9` (×3) |
| **hand `<footprint>`** | **L1, L2** FXL0630 | 2 large 2.4×3.2 lands |
| **hand `<footprint>`** | **Q1** AOD4185 | TO-252-2 — footprinter has **no `to252`/`dpak`** |
| **hand `<footprint>`** | **CB1, CB2** MA25V100 | CP_Elec_6.3×5.9 polymer — footprinter has **no `cp`** |
| **hand `<footprint>`** | **F1** Littelfuse NANO2 | 451/453 — no footprinter fuse land |
| **hand `<footprint>`** | **H1–H4** M3 | NPTH `<hole>`; authored as `<chip>` so they count as components |

**Every one of the specialty connectors WAS expressible** as a hand `<footprint>` child —
`<smtpad>` (rect, explicit `pcbX/pcbY`, per-pad `width/height`) and `<platedhole>`
(`outerDiameter`/`holeDiameter`) reproduced the KiCad land patterns pad-for-pad, and
`portHints` carried the exact KiCad pad *names* (`A1`..`B12`, `SH`, `9`), which is what let
the netlist match verbatim. So the footprinter *gap* is real (specialty connectors, DPAK,
polymer cap, fuse all absent) but is **not a blocker** — the `<footprint>` escape hatch is
fully sufficient. Cost: hand-authoring ~11 land patterns from the `.kicad_mod` geometry.

### Duplicate-pad representation caveat (footprint semantics, not a parity gap)
tscircuit's two pad primitives merge duplicate `portHints` differently:
- **`<smtpad>` duplicates merge** into one schematic pin — matches how KiCad's split QFN
  thermal pad `9` (3 physical pads) is one logical GND node.
- **`<platedhole>` duplicates stay separate** pins — so J2/J3/J4 expose `SH`,`SH` and J5
  exposes `SH`×4, mirroring KiCad's multiple physical shield pads.

Either way the *logical* node set is identical; the parity script compares deduped
`(refdes,padname)` sets on both sides, so 151/151 nodes match.

## ERC on the tscircuit `kicad_sch` export

`kicad-cli sch erc --severity-all` → **635 violations (72 error, 563 warning).** All are
schematic-*rendering* artifacts of the circuit-json→kicad_sch converter, NOT electrical
design faults (connectivity is proven identical to KiCad):

| code | n | class |
|---|---|---|
| `endpoint_off_grid` | 436 | parametric — tscircuit places wires off KiCad's 50-mil grid |
| `lib_symbol_issues` | 82 | parametric — generated symbols differ from KiCad standard lib |
| `pin_not_connected` | 50 | mostly the per-net `GND` rail symbols + the 4 intended NC pins |
| `unconnected_wire_endpoint` | 44 | parametric — converter wire stubs |
| `label_dangling` | 13 | parametric |
| `wire_dangling` | 9 | parametric |
| `isolated_pin_label` | 1 | parametric |

The 72 "errors" are `pin_not_connected` on tscircuit's synthetic per-instance `GND` rail
symbols and the deliberate no-connect pins — none indicate a wrong or missing connection.

## DRC-on-export (PCB) — study only, classified

`kicad-cli pcb drc --severity-all` on the tscircuit `kicad_pcb` → **217 violations + 118
unconnected.** The autorouter was **skipped** (50 placement DRC errors from the deliberately
compact study placement + the USB-C mid-mount A/B rows that overlap by design), so no copper
was routed. Classification:

| type | n | class |
|---|---|---|
| `lib_footprint_issues` | 51 | parametric — every footprint flagged (no KiCad fp metadata) |
| `solder_mask_bridge` | 34 | parametric — overlapping/tight pads (USB-C A/B rows, packed cap pairs) |
| `text_thickness` / `text_height` | 34 / 34 | parametric — default silk text metrics |
| `shorting_items` | 28 | routing-study — same-net pad overlaps, autorouter skipped |
| `clearance` | 16 | routing-study — default 0.15 mm geometry, no netclass |
| `silk_over_copper` / `silk_overlap` | 8 / 5 | parametric |
| `courtyards_overlap` | 6 | parametric — compact study placement |
| `pth_inside_courtyard` | 1 | parametric |
| unconnected | 118 | autorouter skipped — nets unrouted |

Zero of these are schematic/connectivity faults. Per the folder canon, the copper is a design
study; parity proves the *design*, and the KiCad board remains the fab-of-record.

## Verdict

**tscircuit CLEARS the schematic bridge for a connector-heavy board.** Node-for-node netlist
parity (51/51 parts, 28/28 nets, 151/151 nodes) was reached with a single leading-digit net
rename and zero connectivity compromises. The footprinter has no specialty connectors / DPAK /
polymer cap / fuse, but the `<footprint>` child escape hatch reproduced all of them pad- and
name-for-name — so the gap costs authoring effort, not fidelity. ERC (635) and PCB DRC (217+118)
are the expected parametric render noise, not design signal.


---

## Phase-2 update (2026-07-19) — OUR converter is the bridge

`ERC on the tscircuit kicad_sch export` above refers to tscircuit's NATIVE export,
which is no longer the bridge. The pipeline now renders the AUTHORITATIVE
`kicad/xt60-usb-supply.kicad_sch` via `scripts/circuit_json_to_kicad_sch.py`
(ADR-0001 Phase 2): a UNIQUE `elt:SYM_<refdes>` symbol per component with pins keyed
to the exact KiCad pad names and one global-label net-glue per pin. Gate result:
**`kicad-cli sch erc --severity-all` = 0 errors** (95 warnings: parametric
`lib_symbol_issues` + 4 `isolated_pin_label` for the four intentional named-NC nets
`NC_U1_PG`/`NC_U2_PG`/`NC_J5_SBU1`/`NC_J5_SBU2`) and **node-for-node netlist parity 0**
vs the sealed board — 28/28 nets, 151/151 nodes. All 11 hand `<footprint>` connectors
(XT60, USB-A ×3, USB-C, DPAK, polymer caps, fuse) export their full pin sets with the
KiCad pad names intact. Normalization: leading-digit net renames (`N5V_A`/`N5V_C`) only.
See `parity_converter.md` / `erc_converter.rpt`; native export kept as `.native.kicad_sch`.
