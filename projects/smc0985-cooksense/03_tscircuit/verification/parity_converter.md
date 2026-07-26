=== cooksense netlist parity (converter kicad_sch vs sealed 04_kicad) ===
converter nets=161  kicad nets=161
  DIFF 'CONTACTOR_C': only_converter=[('J_ISOLOOP', '1')] only_kicad=[('J_ESTOPLOOP', '1')]
  DIFF 'CONTACTOR_E': only_converter=[('J_ISOLOOP', '4')] only_kicad=[('J_CONTACTOR', '2')]
  DIFF 'CONTACTOR_LOOP': only_converter=[('J_ISOLOOP', '2'), ('J_ISOLOOP', '3')] only_kicad=[('J_CONTACTOR', '1'), ('J_ESTOPLOOP', '2')]
  NO-CONNECT DIFF: only_converter=[] only_kicad=[('J_KEY_MATRIX', 'MP')]
connected nodes: converter=748 kicad=748   no-connects: converter=31 kicad=32
REAL DISCREPANCIES: 4  ->  FAIL
