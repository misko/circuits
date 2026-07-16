# checklist: xt60-usb-supply — pre-release gate

Every line is a runnable command or a file inspection with an expected
result. A release dir may not be cut while any BRIEF.md criterion is
`unmet` (contract rule).

## Build + electrical gates

- [ ] `bash 03_src/rebuild_all.sh` completes; final lines `violations: 0 {}`
      and `unconnected: 0` (includes schematic parity on KiCad 10).
- [ ] Rebuild output contains `AUDIT: PASS` (placement/pad invariants I1-I7).
- [ ] `04_kicad/xt60-usb-supply.kicad_dru` byte-identical to committed after
      rebuild (`git diff --stat` empty for it).
- [ ] Netlist parity: rebuild prints `NETLIST PARITY: PASS`.
- [ ] Polarity audit: rebuild prints `POLARITY: PASS` for every 2-pad
      polarized part (XT60 pad1 = "-" blade to GND; TVS cathode to VBAT_P;
      LED cathodes to their resistor/GND per schematic).
- [ ] Ampacity walk: SW_A/SW_C/5V_A/5V_C/VBAT_* trunk cross-sections are
      pour-served; `grep min_width 03_src/rules/nets.yaml` floors present in
      the generated .kicad_dru.
- [ ] No tracks on In1.Cu: `python3 -c` one-liner in rebuild prints
      `IN1_CLEAN: PASS`.

## Parts + sourcing gates

- [ ] `python3 03_src/bom_seed.py` exits 0 (every BOM line maps to
      02_parts/<MPN>/part.yaml with real LCSC or explicit hand-solder).
- [ ] `python3 skills/jlcpcb-fab/scripts/jlc_stock_check.py <fab>/bom_jlc.csv`
      — every coded line found, stock >= 5x qty, on order day.
- [ ] Every 02_parts/<MPN>/ has the datasheet PDF, sha256 matches part.yaml.

## Fab package gates

- [ ] `export_jlc_package.py` ran on the gated board; gerber zip contains 13
      files (4-layer).
- [ ] JLC digital twin (`jlc_twin.py`): zero unadjudicated criticals;
      MODEL-REG pass; report saved to release verification/.
- [ ] Fresh-context pin review (pin_audit.py protocol): every active part
      verdict PASS; report in release verification/.
- [ ] PDFs (schematic, layers, assembly) exported, rendered to PNG, and
      visually verified by a fresh-context agent; findings dispositioned.
- [ ] Release MANIFEST: sha256 table, git SHA exists, tool versions,
      hand-solder list present.
