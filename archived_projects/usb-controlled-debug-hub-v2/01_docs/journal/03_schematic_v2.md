# Schematic stage — two-USB-C v2

## Outcome

- Generated 162 components on ten human-readable pages.
- TSX diagnostics: 0 embedded errors.
- KiCad converter ERC: 0 errors.
- Source electrical invariants: 111/111 pass against the exact generated
  converter netlist; protection/topology ADR coverage 5/5.
- Early design gates: downstream-port contract, PD surge coordination,
  effective USB bulk capacitance and aggregate fault envelope all pass.
- Power topology: 7/7 rails and 2/2 converters pass. The derived worst-case PD
  input is about 2.1 A at the conservative 13.5 V corner, so the external
  requirement was corrected from 15 V / 2 A to 15 V / 3 A before layout.
- Human readability review split the original 40-component power sheet into a
  23-component PD/regulator sheet and a 17-component distribution sheet.
  Automated schematic occlusion is 0 and no two nets are drawn as one wire.

## Expected red evidence

The v2 generated schematic intentionally fails parity against the untouched v1
PCB/source in `04_kicad`: 22 changed nets and 26 new/renamed parts. This is the
stage boundary, not a waiver. PCB promotion must replace the v1 connectors and
input path, then restore exact board/netlist parity before routing.

## Learnings

1. Run source power topology before schematic generation: it rejected the
   initially under-sized 30 W PD contract without a KiCad rebuild.
2. Run surge coordination before schematic generation: it rejected 25 V input
   capacitors behind a 29.2 V clamp and led to the coordinated SMF16A + 50 V
   capacitor set.
3. Keep the PD converter and downstream distribution on separate schematic
   pages. Both are independently reviewable and future revisions do not need
   to refit a 40-component page.
4. The same USB-C mechanical family can be reused safely only when the sheets,
   silk and invariants name the roles `DATA` and `POWER`; identical connectors
   do not imply interchangeable electrical domains.

## Next stage

Author and independently check exact KiCad footprints for CH224K, TPS56637 RPA
HotRod and MWSA0804S; replace J_UP/J_PWR/F_IN on the v1-derived board; place the
PD hot loop from TI Figure 34; then regenerate connector-orientation and human
3D approval evidence before any routing.
