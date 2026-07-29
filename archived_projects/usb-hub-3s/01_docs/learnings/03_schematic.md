# learnings: 03_schematic

- ISSUE: converter layout (WIRED) mode silently merged net VIN_S into HG2 —
  the KiCad netlister joined a VIN_S wire endpoint with an HG2 wire endpoint
  that tscircuit's schematic auto-layout placed at the SAME coordinate. The
  advertised auto-fallback ("genuine cross-net short -> grid mode") did NOT
  trigger: endpoint COINCIDENCE between two separately-imported nets is not
  a crossing. ERC saw nothing (0 errors); only a net-by-net netlist inspection
  caught it (generate_board's zone-on-unknown-net hard error was the tripwire).
  ROOT CAUSE: converter layout-mode trusts tscircuit's schematic geometry to
  be coincidence-free; on a 112-part board it is not.
  AVOID NEXT TIME: (a) this board pins --mode grid in rebuild_all.sh;
  (b) candidate-canon: yes — suggested check S-WIRE-MERGE: after layout-mode
  conversion, diff the netlist's net->pin map against circuit.json's
  connectivity keys; ANY merged pair = hard fail + auto-fallback to grid.
  (The grid-mode netlist verified correct: VIN_S = {RS2.2, Q4.5, R15.1, U1.24}.)
- ISSUE: `kicad-cli sch erc --severity-all --exit-code-violations` exits 5 on
  WARNINGS-only (320 baselined lib_symbol/footprint_link warnings = exit 5).
  The template rebuild gate would abort on every clean board.
  AVOID: gate greps "Errors 0" from the severity-all report instead.
  candidate-canon: yes — fix the template rebuild_all.sh ERC step.
