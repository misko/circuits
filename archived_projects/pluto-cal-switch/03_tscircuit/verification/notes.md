# verification notes — pluto-cal-switch, schematic gate 2026-07-28

Fidelity gaps and what each one is assigned to. Written at the SCHEMATIC gate,
which is a declared handoff boundary: placement and routing are the next
session's work and nothing below is a routing claim.

## Gate results as measured

| gate | id | result |
|---|---|---|
| `tsx_preflight.py` | TSX-PRE | **PASS 20/20** part.yaml, 13 multi-pin — every pad name on this board is numeric, so nothing needed mapping |
| `kicad-cli sch erc --severity-all` | S1/S4 | **0 errors** / 542 warnings, all three classes parametric (see below) |
| netlist parity vs sealed `04_kicad` | S2 | **N/A — there is no sealed board.** This is the board's FIRST schematic; `04_kicad/` held only its `contracts.md` until today. Stated as N/A rather than reported as a pass |
| `net_label_survival.py` | S-NETMERGE | **PASS 48/48** labels survive to the exported netlist |
| `electrical_invariants.py` | E-INV | **OK 40/40** invariants hold |
| `electrical_invariants.py --adr-coverage` | E-ADR | **FAIL 11/12 — the DECLARED gate gap O8b, not a defect.** See below |
| `power_topology.py` | E-TOPO | **OK 1/1** rail, 1/1 converter |
| `power_topology.py --margin` | E-MARGIN | **N-A** — no rail declares `load_uv_threshold` |
| `power_topology.py --off-control` | E-OFF | **N-A** — `source_type: usb`, de-energized by unplugging |
| `count_parity.py` | S-COUNT | **PASS 3/3** source pairs agree with `manifest.yaml` over **73 refdes** |
| `bom_source_check.py --circuit-only` | M-BOM leg C | **PASS** — every coded R/C's catalog value == its tsx value prop |

## ERC warnings — classified, not counted

All 542 are parametric and are the classes `03_tscircuit/contracts.md` baselines:

| class | n | why it is not a finding |
|---|---|---|
| `endpoint_off_grid` | 284 | the converter's `layout` mode snaps to a 0.635 mm fidelity grid so pin tips and wire ends coincide exactly; KiCad's default ERC grid is 1.27 mm |
| `lib_symbol_issues` | 185 | the converter's embedded `elt:SYM_<refdes>` library is not in the running `kicad-cli` config. It is embedded in the sheet, which is why the netlist builds correctly |
| `footprint_link_issues` | 73 | **the `pluto_cal_switch:` footprint library does not exist yet.** Every part.yaml names its FPID in that library and all 73 components resolve one, but `03_src/lib/pluto_cal_switch.pretty/` is stage-5 work. This warning is the honest signal of exactly that, and it will go to 0 when the library lands |

**0 errors is the bar and it is met.** There are no `pin_not_connected`,
`wire_dangling`, `unconnected_wire_endpoint` or `isolated_pin_label` findings:
every sanctioned float (`J_USB` ID pad 4, `U_LDO` NC pad 4, `U_HDR_ESD` NC pads
1-2, and 32 unused RP2040 GPIO) carries an explicit `no_connect` flag, which is
what canon S1/S4 asks for.

## What the FPID count proves, and what it does not

The converter reports **73 components (73 with FPID)** — the two numbers must be
equal and are. That proves every part resolved a footprint IDENTIFIER from its
`02_parts/<MPN>/part.yaml`; it does NOT prove the footprint exists, because the
library is stage-5 work. The first build reported **72 with FPID**: the missing
one was `F1`, whose PPTC had no dossier at all. That is the entire value of the
check — a single unresolved FPID is invisible in ERC, in parity and in the
render, and it hard-errors `generate_board` three stages later.

## Deliberate topology facts a reviewer will want to re-check

1. **`U_ESD` pins 1 and 6 are ONE net (`USB_DP`), and 3 and 4 are one net
   (`USB_DM`).** That is the part (Figure 1, Doc ID 11265 Rev 5): the pairs are
   internally connected. "Route the data line in one pin and out the other" is a
   COPPER rule, not two electrical nets — it belongs to placement/routing, and
   the netlist correctly shows a shunt clamp.
2. **The loopback path carries no DC blocking capacitor.** By design
   (ADR-0005); the YAT pads DC-reference the node. `C_DCBLK1/2` appear only on
   the two antenna ports.
3. **`U_SW1.1`/`U_SW2.1` (RF2) sit on `LOOP_ARM1_SW`/`LOOP_ARM2_SW`, not on
   `LOOP_ARM1`/`LOOP_ARM2`.** The arm pad is between the splitter and the
   switch, which is ADR-0004's whole point. The stage-3 invariants file asserted
   the un-padded net and was corrected here (see the journal).
4. **`Y1` pads 1 and 3 are interchangeable** — a quartz crystal is symmetric and
   the Abracon drawing's own note says the chamfer is not a polarity marker.
   A-ROT must not be asked to grade a rotation this part does not have.

## E-ADR: the one RED gate, and why it stays red

`E-ADR FAIL: 11/12 — ADR 0006 ... no invariant cites adr: 0006`.

**This is O8b, declared in ARCHITECTURE §12 before the schematic existed, and it
is a gate gap rather than a board defect.** `electrical_invariants.py`'s
`protection_adrs()` excludes only `0000-example`; it does not read `status:`.
ADR-0006 is `superseded-by-0015` and its decision (SMA→SMP adapters) **no longer
exists**, so there is no design intent left to assert about it. The intent loop
IS closed by its successors: ADR-0015 emits 3 invariants and ADR-0016 emits 1.

**It would take one line to make this gate green — adding a `tags:`-free front
matter or retagging ADR-0006 — and that is exactly why it is left red.** Gaming
a coverage gate by editing the document it grades is the silent-downgrade class
this canon exists to prevent. The fix belongs in `skills/`; a proposed patch is
in the stage-4 report.

## Owed before the board can be built (NOT schematic-gate items)

- `03_src/lib/pluto_cal_switch.pretty/` — every footprint this board names.
  Nine distinct land patterns are non-stock and must be authored: the SMA
  5-Ø1.4 @ 5.08 mm THT pattern, MCLP-6-EP 2×2, TSNP-6 0.7×1.1 @ 0.4 mm,
  QFN-56 0.4 mm, the XKB micro-B with its two OVAL PLATED SLOTS, SOT-553,
  SOT-23-5/-6, and the two RF-minimum-area 0402 patterns.
- `03_src/floorplan.yaml` placement — it carries this board's identity but no
  anchors or seeds yet, deliberately (see its banner).
- `J_USB`'s pin map is still the INFERRED USB Micro-B standard map. Its
  resolution is a fresh-context pin review against JLC's own fetched footprint
  at the twin stage — the schematic cannot settle it, and it is registered in
  `02_parts/README.md`.
