# learnings — stage 4, schematic authoring

Harvest source for the canon (`design-policies.md` / the skill templates), not
canon itself. Each entry: what was hit, its ROOT CAUSE, and a concrete "how to
avoid next time" with a suggested check ID.

---

## 1. tscircuit's parts engine silently CHOOSES an LCSC code for every un-coded passive — and `tsci build` is non-deterministic

**Hit.** `bom_source_check --circuit-only` came back with 10
`UNVERIFIABLE-VALUE` findings naming LCSC codes that appear nowhere in the TSX,
in `02_parts`, or in any design document. Measured: **all 38 commodity passives
on this board had been assigned a supplier code by tscircuit**, with multiple
candidates each, purely from the value + footprint token.

**Root cause.** The authoring contract says "a SPECIALTY part MUST author
`supplierPartNumbers`" and is silent about commodity passives, because the
converter's `COMMODITY_FP` token map resolves their FOOTPRINT without one. But
the FOOTPRINT is not the only thing a supplier code decides — it also decides
the **BOM line**, and nobody had noticed that leaving it blank does not produce
a blank: it produces a build-time guess.

**Why it matters, in two numbers.** (a) `tsci build` is documented as
NON-DETERMINISTIC, so an unpinned BOM line is not regenerable from source —
a canon **M3** violation that no gate looked for. (b) The engine's 47 Ω pick was
**C25118 (0402WGF470JTCE) at stock 10, extended**, for a part this board uses
**four times** and whose value ADR-0005 machine-asserts, because 47 Ω is what
holds PE42482A-X's 3.6 V digital absolute maximum against a 4.81 V far-end
reflection. The same value is available as **C137864 at stock 86,783**. Nothing
in the pipeline was going to compare those two numbers.

**Avoid next time.** `candidate-canon: yes`. Suggested **S-PIN** (or fold into
S-COUNT's family): *every `<resistor>`/`<capacitor>`/`<inductor>` in a TSX
carries an explicit `supplierPartNumbers`; a circuit.json component whose
supplier code is absent from the TSX source text is a FAIL.* It is a one-regex
check over the TSX plus circuit.json, it has an obvious known-bad fixture (delete
one `supplierPartNumbers` and the gate must go red), and it converts a silent
build-time guess into an authored decision.

---

## 2. The stage-2 coverage denominator was the value index, and the value index does not list every part

**Hit.** `02_parts/README.md` opened with "COMPLETE for every part the design
names — thirteen dossiers, one per part in `01_docs/DETAIL_DESIGN.md`". At
stage 4 the indicator LED and the pushbutton both turned out to have no dossier,
so four of sixty-four components resolved to an **EMPTY FPID** — which
`generate_board_generic.py` hard-errors on, at stage 5, after the schematic is
already committed.

**Root cause.** The sweep counted itself against `DETAIL_DESIGN.md` §8's value
index. That table lists the LED **BALLASTS** (`R_LED1`/`R_LED2` = 680 Ω, derived
from `(3.3 − 2.0)/680`) and never the LEDs, and never mentions a button at all.
Meanwhile `floorplan.yaml` seeded `LED_PWR`, `LED_ST`, `SW_BOOT` and `nets.yaml`
declared `LED_PWR`, `LED_STAT`, `BOOTSEL_N`, `RUN_N`. **Three files named the
parts and the fourth was the one used as the denominator.**

**A second-order find in the same place:** the 680 Ω was derived at
**Vf = 2.0 V**, which silently pins the indicator to a RED LED. A green part at
Vf 2.6–3.1 V through the same ballast runs 0.29–1.03 mA — up to 6.6× dimmer.
A "colour preference" was actually a part constraint.

**Avoid next time.** `candidate-canon: yes`. Suggested **P-DENOM**: *the 02_parts
coverage denominator is the UNION of `floorplan.yaml` `anchors:`+`seeds:` refdes
and the refdes implied by `nets.yaml`, not a prose table.* Mechanically:
`03_tscircuit/manifest.yaml` already IS that union once it exists, so the check
is "every manifest refdes whose prefix is not a commodity class resolves to a
`02_parts` dossier or to the vetted passives ledger". This is exactly the check
that would have caught it before the schematic was authored rather than after.

---

## 3. Two skill-template files had been seeded and never edited, and one of them names a DIFFERENT BOARD

**Hit.** `03_src/route.yaml` was still the skill's schema example **verbatim** —
header comment, cook-loadcell's wave groups, `fab_tier: standard`, a 2-layer
`layers: [F.Cu, B.Cu]`, and `project: {name: cook_loadcell, board:
04_kicad/cook_loadcell.kicad_pcb}`. `03_src/rebuild_all.sh` was likewise
unedited: `BOARD=power3s`, `TSX=power3s`.

**Root cause.** The seeding step ("copy the templates, then replace the values")
has no gate on the SECOND half. `rebuild_reuse.sh` derives its board name from
`floorplan.yaml` and would have been correct; every `route_and_stitch_generic.py`
step reads `route.yaml` and would have been wrong — so the routing stage would
have written, stitched and gated a board file that the DRC gate never reads.
This is the same class a sibling board hit one day earlier.

**Avoid next time.** `candidate-canon: yes`. Suggested **C-SEED**: *no file under
`03_src/` may carry a `project.name` / `BOARD=` / `TSX=` that disagrees with
`floorplan.yaml` `project.name`, and no `03_src/` file may still contain the
template's own marker string (`SCHEMA EXAMPLE`, `power3s`).* Two greps. It costs
nothing and it is the cheapest possible catch for a landmine that only detonates
three stages later.

---

## 4. `adjacency:` budgets in `part.yaml` are written, cited, arithmetically derived — and graded by NOTHING

**Hit.** Two independent stage-2 dossiers (`USBLC6-2SC6` and
`TYPE-C-31-M-12A`) both recorded `adjacency: [{refdes: [U_ESD, J_USB],
max_mm: 2.0}]` with the ST §2.2 arithmetic behind it, and both flagged that the
floorplan had them ~8 mm apart. Reading `policy_audit.py`'s P-ADJ
implementation: it iterates `layout.keep_short` only. **`adjacency:` is never
read by any gate.**

**Why it matters.** The number is not decorative: 6 nH per 10 mm × 0.5 mm at
dI/dt = 24 A/ns is +144 V **per leg**, which turns the array's 17 V clamp into
305 V. ST prints that arithmetic specifically to make the point that a badly
laid-out USBLC6-2 is *worse than none*, because the designer believes the port
is protected. And it is invisible to every other gate — the netlist is identical
at 2 mm and at 8 mm.

**Avoid next time.** `candidate-canon: yes`. Suggested **P-ADJ-PAIR**: *grade
`layout.adjacency` refdes pairs against the board's footprint positions, with
the same UNREACHED-not-skipped discipline P-ADJ already has for a net that
carries fewer than two pads.* It is ~15 lines beside the existing P-ADJ loop and
it currently has zero coverage across the fleet.

---

## 5. Three `keep_short` budgets on this board name nets the board does not carry, and one names a plane

**Hit, before the board exists** (predicted, so stage 5 is not surprised):
`PE42482A-X` budgets `SW_VDD ≤ 3 mm` and `SW_LS ≤ 2 mm`; `KH-SMA-KE-Z` budgets
`RF_ANT_LAUNCH ≤ 3 mm`. None of those three is a net on this board — LS is on
`GND` by ADR-0005, pin 8 is on the global `3V3` with no series element to make a
second node, and `RF_ANT_LAUNCH` is a generic name. They will land in
**P-ADJ-UNREACHED**. Worse: `ABM8-272-T3` budgets **`GND ≤ 3 mm`**, and GND is a
four-layer pour with hundreds of pads — that one will land in **P-ADJ** as a
hard FAIL that can only ever be waived.

**Root cause.** A `keep_short` budget is authored from the DATASHEET's net
names, and the board's net names are chosen later, independently. Nothing
cross-checks them, so the failure mode splits: a renamed net goes quiet
(UNREACHED) and a plane net goes loud-but-meaningless (a permanent waiver, which
canon M4 calls an inherited defect in the making).

**Avoid next time.** `candidate-canon: yes`. Suggested **P-BUDGET-NET**: *at the
SCHEMATIC gate — where the netlist first exists and the board does not — check
every `layout.keep_short.net` against the exported netlist, and FAIL a budget
whose net is absent OR whose net is a declared plane/pour net.* Moving it from
the board stage to the schematic gate is the point: the fix is a one-line
`part.yaml` edit, and at stage 5 it arrives mixed in with real placement work.

---

## 6. A 4-pad tactile switch has TWO pad NUMBERS, and authoring four is invisible until the board stage

**Hit.** The switch was first authored with pads 1/2/3/4 (the physical foot
count). KiCad's `Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A` gives **two** pad
numbers to four pads — `"1"` at (±3, −1.875) and `"2"` at (±3, +1.875). Pins 3
and 4 would have had no pad to answer to.

**Why it survives the schematic gate.** ERC is happy (both pins have nets),
`count_parity` is happy (the refdes SET is unchanged), the netlist is
self-consistent. It surfaces only as a `--schematic-parity` diff after the board
is generated — i.e. at the stage where it costs a rebuild.

**Avoid next time.** `candidate-canon: yes` — and cheaply: **`tsx_preflight.py`
already parses every `part.yaml` `pins:` map and already resolves the
footprint.** Extend it to compare the pad-NUMBER SET in `pins:` against the pad
names in the resolved `.kicad_mod` and fail on a mismatch. Same gate, same
inputs, one more property — and it is the same shape as the alphanumeric-pad
check it already performs.
